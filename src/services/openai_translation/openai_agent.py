"""
OpenAI Agents SDK Implementation for Translation.

This module properly implements translation using the OpenAI Agents SDK
with Gemini API integration, including proper error handling for rate limits.
"""

import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
import time
import json

from agents import Agent, Runner, function_tool, RunContextWrapper
from src.services.openai_translation.client import GeminiOpenAIClient, get_gemini_client
from src.models.translation_openai import TranslationJob, TranslationChunk
from src.utils.translation_logger import get_translation_logger
from src.utils.translation_errors import (
    TranslationError, RateLimitError, APIError,
    retry_with_exponential_backoff, handle_api_error
)

logger = get_translation_logger(__name__)


@dataclass
class TranslationContext:
    """Context information for translation."""
    page_url: Optional[str] = None
    page_title: Optional[str] = None
    document_type: Optional[str] = None  # book, article, documentation, etc.
    technical_domain: Optional[str] = None  # AI, robotics, programming, etc.
    target_audience: Optional[str] = None  # students, professionals, general
    previous_translations: Optional[List[str]] = None
    glossary: Optional[Dict[str, str]] = None
    chunk_index: Optional[int] = None
    total_chunks: Optional[int] = None


class OpenAITranslationAgent:
    """
    OpenAI Agents SDK-based translation agent with proper error handling.

    Uses the official OpenAI Agents SDK with Gemini API for intelligent translation
    with context awareness and specialized tools.
    """

    def __init__(
        self,
        gemini_client: GeminiOpenAIClient,
        model: str = "gemini-2.0-flash-lite"
    ):
        """
        Initialize translation agent.

        Args:
            gemini_client: Configured Gemini OpenAI client
            model: Model to use for translation
        """
        self.client = gemini_client
        self.model = model
        self.agent = self._create_agent()

        logger.info(
            "OpenAI Translation Agent initialized",
            model=model
        )

    def _create_agent(self) -> Agent:
        """Create the translation agent with tools and proper error handling."""
        instructions = """
        You are a professional translator specializing in technical content translation from English to Urdu.

        Your primary task is to translate English content to Urdu while:
        1. Maintaining technical accuracy
        2. Using appropriate Urdu terminology
        3. Preserving code blocks and technical identifiers
        4. Providing contextually appropriate translations
        5. Using Urdu script (Nastaleeq) for all Urdu text

        Key Translation Guidelines:
        - Translate ALL content unless explicitly marked as code
        - Use Urdu script for all translations
        - For technical terms, use established Urdu translations where available
        - For brand new terms, create appropriate Urdu equivalents
        - Maintain the original document structure and formatting
        - Code blocks remain in English but add Urdu comments if helpful

        Technical Term Examples:
        - AI → مصنوعی ذہانت
        - Machine Learning → مشین لرننگ
        - Robotics → روبوٹکس
        - Computer Vision → کمپیوٹر ویژن
        - Neural Network → نیورل نیٹورک
        - Algorithm → الگورتھم

        Error Handling:
        - If you encounter rate limiting errors, wait and retry automatically
        - If translation fails for a chunk, note the error and continue
        - Always provide meaningful error messages

        Always strive for natural, fluent Urdu that accurately conveys the technical meaning.
        """

        return Agent(
            name="UrduTechnicalTranslator",
            instructions=instructions,
            model=self.model,
            tools=[
                self._create_translate_tool(),
                self._create_analyze_code_tool(),
                self._create_glossary_tool(),
                self._create_context_tool()
            ]
        )

    async def _handle_rate_limit_error(self, error: Exception) -> None:
        """
        Handle rate limit errors with proper backoff.

        Args:
            error: The rate limit error
        """
        if isinstance(error, OpenAIRateLimitError):
            logger.warning(
                "Rate limit hit, implementing backoff",
                retry_after=error.retry_after if hasattr(error, 'retry_after') else None
            )

            # Implement exponential backoff
            retry_after = getattr(error, 'retry_after', 1)
            await asyncio.sleep(retry_after)

        # Handle HTTP 429 from OpenAI client
        elif hasattr(error, 'status_code') and error.status_code == 429:
            retry_after = 1
            if hasattr(error, 'response') and error.response:
                try:
                    error_data = error.response.json()
                    retry_after = error_data.get('retry_after', retry_after)
                except:
                    pass

            logger.warning(
                "HTTP 429 rate limit hit",
                retry_after=retry_after
            )
            await asyncio.sleep(retry_after)

    async def translate_with_agent(
        self,
        text: str,
        context: Optional[TranslationContext] = None
    ) -> Dict[str, Any]:
        """
        Translate text using OpenAI Agents SDK with proper error handling.

        Args:
            text: Text to translate
            context: Translation context

        Returns:
            Translation result with metadata
        """
        logger.info(
            "Starting translation with OpenAI Agents SDK",
            text_length=len(text),
            has_context=bool(context)
        )

        # Prepare context prompt
        context_info = ""
        if context:
            if context.technical_domain:
                context_info += f"\nDomain: {context.technical_domain}"
            if context.document_type:
                context_info += f"\nDocument Type: {context.document_type}"
            if context.target_audience:
                context_info += f"\nTarget Audience: {context.target_audience}"
            if context.chunk_index is not None:
                context_info += f"\nChunk: {context.chunk_index + 1} of {context.total_chunks or '?'}"

        # Create the translation prompt
        prompt = f"""
        Translate the following English text to Urdu:

        {context_info}

        Text:
        {text}

        Requirements:
        - Use Urdu script (Nastaleeq)
        - Translate all non-code content
        - Preserve formatting and structure
        - Use appropriate technical terminology
        - Maintain consistency with previous translations
        """

        try:
            # Create runner and execute with retry logic
            runner = Runner(self.agent)

            # Implement retry with rate limit handling
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    result = await runner.run(prompt)

                    # Extract metadata
                    tokens_used = 0
                    if hasattr(result, 'usage') and result.usage:
                        tokens_used = result.usage.total_tokens

                    return {
                        "translated_text": result.final_output.strip(),
                        "original_text": text,
                        "tokens_used": tokens_used,
                        "model": self.model,
                        "confidence_score": 0.9,  # Placeholder
                        "attempt": attempt + 1,
                        "context": context_info
                    }

                except OpenAIRateLimitError as e:
                    if attempt < max_retries - 1:
                        await self._handle_rate_limit_error(e)
                        continue
                    else:
                        raise RateLimitError(
                            f"Rate limit exceeded after {max_retries} attempts",
                            retry_after=getattr(e, 'retry_after', None)
                        )

                except Exception as e:
                    # Check if it's an HTTP 429 error
                    if hasattr(e, 'status_code') and e.status_code == 429:
                        if attempt < max_retries - 1:
                            await self._handle_rate_limit_error(e)
                            continue
                        else:
                            raise RateLimitError(
                                f"Rate limit exceeded after {max_retries} attempts",
                                retry_after=getattr(e, 'retry_after', 1)
                            )
                    else:
                        # Re-raise non-rate-limit errors
                        raise

        except RateLimitError:
            raise
        except Exception as e:
            logger.error(
                "Agent translation failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise TranslationError(
                f"Translation failed: {str(e)}",
                error_type="AGENT_ERROR",
                details={"original_error": str(e)}
            )

    def _create_translate_tool(self):
        """Create the translate tool for the agent."""
        @function_tool
        async def translate_text(
            ctx: RunContextWrapper[Any],
            text: str,
            context: Optional[Dict[str, Any]] = None,
            preserve_formatting: bool = True
        ) -> str:
            """
            Translate text from English to Urdu using the OpenAI client directly.

            This is a fallback tool used by the agent for complex translations.
            """
            logger.debug(
                "Using translate_text tool",
                text_length=len(text)
            )

            try:
                # Use the Gemini OpenAI client directly
                client = self.client.get_client()

                response = await client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional translator for technical content."
                        },
                        {
                            "role": "user",
                            "content": f"Translate to Urdu: {text}"
                        }
                    ],
                    temperature=0.3,
                    max_tokens=4000
                )

                return response.choices[0].message.content.strip()

            except Exception as e:
                if hasattr(e, 'status_code') and e.status_code == 429:
                    # Convert to OpenAI Agents SDK rate limit error
                    raise OpenAIRateLimitError(
                        "Rate limit exceeded",
                        retry_after=getattr(e, 'retry_after', 1)
                    )
                raise

        return translate_text

    def _create_analyze_code_tool(self):
        """Create the code analysis tool for the agent."""
        @function_tool
        async def analyze_code_blocks(
            ctx: RunContextWrapper[Any],
            text: str
        ) -> List[Dict[str, Any]]:
            """
            Analyze text to identify and extract code blocks.
            """
            import re

            # Pattern to match code blocks
            code_pattern = re.compile(r'```(\w+)?\n(.*?)\n```', re.DOTALL)

            code_blocks = []
            for match in code_pattern.finditer(text):
                language = match.group(1) or "text"
                code_content = match.group(2)
                start_pos = match.start()
                end_pos = match.end()

                code_blocks.append({
                    "language": language,
                    "content": code_content,
                    "start_position": start_pos,
                    "end_position": end_pos,
                    "length": len(code_content)
                })

            return code_blocks

        return analyze_code_blocks

    def _create_glossary_tool(self):
        """Create the glossary tool for the agent."""
        @function_tool
        async def get_translation_glossary(
            ctx: RunContextWrapper[Any],
            domain: Optional[str] = None
        ) -> Dict[str, str]:
            """
            Get domain-specific translation glossary.
            """
            glossaries = {
                "ai": {
                    "Artificial Intelligence": "مصنوعی ذہانت",
                    "Machine Learning": "مشین لرننگ",
                    "Deep Learning": "ڈیپ لرننگ",
                    "Neural Network": "نیورل نیٹورک",
                    "Algorithm": "الگورتھم",
                    "Model": "ماڈل",
                    "Training": "تربیت",
                    "Inference": "استنتاج",
                    "Dataset": "ڈیٹاسیٹ",
                    "Feature": "خصوصیت"
                },
                "robotics": {
                    "Robot": "روبوٹ",
                    "Actuator": "ایکچویٹر",
                    "Sensor": "سینسر",
                    "Kinematics": "کائنیمیٹکس",
                    "Path Planning": "پاتھ پلاننگ",
                    "Control System": "کنٹرول سسٹم",
                    "Embedded": "ایمبیڈڈ",
                    "Autonomous": "خودکار"
                },
                "programming": {
                    "Function": "فنکشن",
                    "Variable": "متغیر",
                    "Class": "کلاس",
                    "Object": "آبجیکٹ",
                    "Method": "میٹھڈ",
                    "Library": "لائبریری",
                    "Framework": "فریم ورک",
                    "API": "API",
                    "Database": "ڈیٹا بیس",
                    "Server": "سرور"
                }
            }

            if domain and domain.lower() in glossaries:
                return glossaries[domain.lower()]

            # Return combined glossary for general use
            combined = {}
            for gloss in glossaries.values():
                combined.update(gloss)

            return combined

        return get_translation_glossary

    def _create_context_tool(self):
        """Create the context tool for the agent."""
        @function_tool
        async def set_translation_context(
            ctx: RunContextWrapper[Any],
            page_url: Optional[str] = None,
            document_type: Optional[str] = None,
            technical_domain: Optional[str] = None,
            target_audience: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Set context for translation decisions.
            """
            context = {
                "page_url": page_url,
                "document_type": document_type,
                "technical_domain": technical_domain,
                "target_audience": target_audience,
                "set_at": time.time()
            }

            logger.info(
                "Translation context set via tool",
                context=context
            )

            return {
                "success": True,
                "message": "Translation context updated successfully",
                "context": context
            }

        return set_translation_context

    async def translate_chunk_sequence(
        self,
        chunks: List[str],
        context: Optional[TranslationContext] = None
    ) -> List[Dict[str, Any]]:
        """
        Translate a sequence of chunks maintaining consistency.

        Args:
            chunks: List of text chunks to translate
            context: Translation context

        Returns:
            List of translation results
        """
        logger.info(
            "Translating chunk sequence with OpenAI Agents SDK",
            chunk_count=len(chunks),
            has_context=bool(context)
        )

        results = []
        total_tokens = 0

        for i, chunk in enumerate(chunks):
            logger.debug(
                "Translating chunk",
                chunk_index=i,
                chunk_length=len(chunk)
            )

            # Update context with chunk info
            chunk_context = context
            if chunk_context:
                chunk_context.chunk_index = i
                chunk_context.total_chunks = len(chunks)

            try:
                result = await self.translate_with_agent(chunk, chunk_context)
                result["chunk_index"] = i
                results.append(result)
                total_tokens += result.get("tokens_used", 0)

            except RateLimitError as e:
                logger.error(
                    "Rate limit hit for chunk",
                    chunk_index=i,
                    retry_after=e.retry_after
                )
                # Add rate limit error result
                results.append({
                    "chunk_index": i,
                    "translated_text": f"[RATE LIMIT ERROR: {str(e)}]",
                    "original_text": chunk,
                    "error": str(e),
                    "error_type": "RATE_LIMIT",
                    "tokens_used": 0,
                    "model": self.model,
                    "confidence_score": 0.0,
                    "retry_after": e.retry_after
                })

            except Exception as e:
                logger.error(
                    "Chunk translation failed",
                    chunk_index=i,
                    error=str(e)
                )
                # Add failed result
                results.append({
                    "chunk_index": i,
                    "translated_text": chunk,  # Fallback to original
                    "original_text": chunk,
                    "error": str(e),
                    "tokens_used": 0,
                    "model": self.model,
                    "confidence_score": 0.0
                })

        logger.info(
            "Chunk sequence translation completed",
            total_chunks=len(chunks),
            successful_chunks=len([r for r in results if not r.get("error")]),
            total_tokens=total_tokens
        )

        return results

    async def get_agent(self) -> Agent:
        """Get the configured translation agent."""
        return self.agent