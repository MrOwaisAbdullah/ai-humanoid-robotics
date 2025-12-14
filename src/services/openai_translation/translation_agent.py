"""
Simplified OpenAI Translation Agent using proper Runner.run pattern.
"""

import asyncio
from typing import Dict, Optional, Any
from dataclasses import dataclass

from agents import Agent, Runner
from src.services.openai_translation.client import GeminiOpenAIClient, get_gemini_client
from src.utils.translation_logger import get_translation_logger

logger = get_translation_logger(__name__)


@dataclass
class TranslationContext:
    """Context information for translation."""
    page_url: Optional[str] = None
    document_type: Optional[str] = None
    technical_domain: Optional[str] = None
    target_audience: Optional[str] = None


class OpenAITranslationAgent:
    """
    OpenAI Agents SDK-based translation agent using proper Runner.run pattern.
    """

    def __init__(
        self,
        gemini_client: Optional[GeminiOpenAIClient] = None,
        model: str = "gemini-2.0-flash-lite"
    ):
        """Initialize translation agent."""
        self.client = gemini_client or get_gemini_client()
        self.model = model

        # Create the agent with translation instructions
        self.agent = Agent(
            name="Translation Agent",
            instructions=self._get_translation_instructions(),
            model=self.client.get_model()
        )

    def _get_translation_instructions(self) -> str:
        """Get the base translation instructions for the agent."""
        return """
You are a professional translator specializing in English to Urdu translation.

CRITICAL REQUIREMENTS:
1. Translate ALL text to Urdu - no English words should remain
2. ONLY preserve code blocks marked with ```
3. Translate technical terms with context (e.g., AI -> مصنوعی ذہانت)
4. Use Urdu script (Nastaleeq) for Urdu text
5. Maintain formatting and structure
6. Mix Urdu with Roman Urdu for technical terms where appropriate

When translating:
- Use appropriate honorifics and politeness levels
- Translate idioms and expressions to their Urdu equivalents
- Preserve the meaning and tone of the original text
- Handle technical terminology correctly
- Ensure grammatical correctness in Urdu

Additional context will be provided as needed for specific domains.
"""

    async def translate_with_agent(
        self,
        text: str,
        context: Optional[TranslationContext] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Translate text using OpenAI Agents SDK with proper Runner.run pattern.

        Args:
            text: Text to translate
            context: Translation context information
            user_id: User ID for tracking

        Returns:
            Dictionary containing translation result
        """
        try:
            # Build the prompt with context
            prompt = self._build_translation_prompt(text, context)

            logger.info(
                "Starting translation with agent",
                text_length=len(text),
                context=context.document_type if context else None,
                model=self.model
            )

            # Run the agent using the proper Runner.run pattern
            result = await Runner.run(
                self.agent,
                prompt,
                max_turns=1  # Single turn for simple translation
            )

            # Extract the translated text
            translated_text = result.final_output

            # Try to extract tokens from usage if available
            tokens_used = 0
            model_used = self.model

            # The result might have usage information in different formats
            if hasattr(result, 'usage') and result.usage:
                tokens_used = result.usage.total_tokens if hasattr(result.usage, 'total_tokens') else 0
                model_used = result.usage.model if hasattr(result.usage, 'model') else self.model

            # Check if the translation contains code blocks
            has_code_blocks = "```" in translated_text

            # Extract code blocks if present
            code_blocks = []
            if has_code_blocks:
                import re
                code_pattern = re.compile(r'```(\w+)?\n(.*?)\n```', re.DOTALL)
                code_blocks = [
                    {
                        "language": match.group(1) or "unknown",
                        "code": match.group(2)
                    }
                    for match in code_pattern.finditer(translated_text)
                ]

            logger.info(
                "Translation completed successfully",
                original_length=len(text),
                translated_length=len(translated_text),
                tokens_used=tokens_used,
                has_code_blocks=has_code_blocks
            )

            return {
                "translated_text": translated_text.strip(),
                "original_text": text,
                "tokens_used": tokens_used,
                "model": model_used,
                "confidence_score": 0.95,  # Agent typically produces high-quality translations
                "has_code_blocks": has_code_blocks,
                "code_blocks": code_blocks,
                "context_used": context is not None,
                "processing_time_ms": 0,  # Could track this if needed
                "cache_hit": False
            }

        except Exception as e:
            logger.error(
                "Agent translation failed",
                error=str(e),
                error_type=type(e).__name__,
                text_length=len(text)
            )

            # Re-raise with context
            raise Exception(f"Translation failed: {str(e)}") from e

    def _build_translation_prompt(
        self,
        text: str,
        context: Optional[TranslationContext]
    ) -> str:
        """Build the translation prompt with context."""
        prompt_parts = ["Translate the following text from English to Urdu:"]

        # Add context information if provided
        if context:
            context_parts = []
            if context.document_type:
                context_parts.append(f"Document Type: {context.document_type}")
            if context.technical_domain:
                context_parts.append(f"Technical Domain: {context.technical_domain}")
            if context.target_audience:
                context_parts.append(f"Target Audience: {context.target_audience}")

            if context_parts:
                prompt_parts.append("\nContext:")
                prompt_parts.append("\n".join(f"- {part}" for part in context_parts))

        # Add the text to translate
        prompt_parts.append(f"\n\nText to translate:\n{text}")

        # Add instruction to translate only the content
        prompt_parts.append("\n\nTranslate only the text above.")

        return "\n".join(prompt_parts)


# Factory function
def create_translation_agent(model: str = "gemini-2.0-flash-lite") -> OpenAITranslationAgent:
    """Create a translation agent instance."""
    return OpenAITranslationAgent(model=model)