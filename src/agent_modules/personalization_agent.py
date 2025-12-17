"""
Personalization Agent for Content Adaptation
Handles AI-powered content personalization based on user background
"""

import os
import json
from typing import Dict, Any, List, Optional
from openai_agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled


class PersonalizationAgent:
    """
    AI Agent for personalizing technical content based on user expertise
    """

    def __init__(self):
        """Initialize the personalization agent with primary and fallback configurations"""
        # Disable tracing for non-OpenAI providers
        set_tracing_disabled(True)

        # Initialize primary Gemini client
        self.gemini_client = AsyncOpenAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            timeout=60.0,
            max_retries=3
        )

        # Initialize fallback OpenRouter client
        self.openrouter_client = None
        if os.getenv("OPENROUTER_API_KEY"):
            self.openrouter_client = AsyncOpenAI(
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                timeout=60.0,
                max_retries=3,
                default_headers={
                    "HTTP-Referer": os.getenv("FRONTEND_URL", "http://localhost:3000"),
                    "X-Title": "AI Book Personalization Agent"
                }
            )

        # Configure primary model (Gemini)
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.primary_model = OpenAIChatCompletionsModel(
            model=model_name,
            openai_client=self.gemini_client
        )

        # Configure fallback model (OpenRouter)
        self.fallback_model = None
        if self.openrouter_client:
            self.fallback_model = OpenAIChatCompletionsModel(
                model="openai/gpt-oss-120b:free",
                openai_client=self.openrouter_client
            )

        # Initialize the agent with primary model
        self.agent = Agent(
            name="ContentPersonalizer",
            instructions=self._get_personalization_instructions(),
            model=self.primary_model
        )

    def _get_personalization_instructions(self) -> str:
        """
        Get the instructions for the personalization agent
        """
        return """
        You are a Content Personalization AI that adapts technical content based on user expertise.

        Your task is to personalize technical explanations while maintaining accuracy and clarity.

        CRITICAL: You MUST format your response using proper Markdown syntax for:
        - Headers using # ## ### etc.
        - Bullet points using - or *
        - Numbered lists using 1. 2. 3.
        - Bold text using **text**
        - Italic text using *text*
        - Code blocks using ```language ... ``` for multi-line code
        - Inline code using `code` for single lines

        Personalization Strategy:

        1. For Software Engineers (technical_focus: "software"):
           - Use code examples and API references
           - Include implementation patterns
           - Reference relevant frameworks/libraries
           - Focus on practical application

        2. For Hardware Engineers (technical_focus: "hardware"):
           - Include physical constraints and considerations
           - Reference material properties and specifications
           - Include performance metrics (power, latency, throughput)
           - Focus on system-level implications

        3. For Beginners (experience_level: "beginner"):
           - Use simple language and clear analogies
           - Break down complex concepts
           - Provide step-by-step explanations
           - Include "Think of it like..." comparisons

        4. For Intermediate Users (experience_level: "intermediate"):
           - Build on existing knowledge
           - Include practical examples
           - Connect related concepts

        5. For Advanced Users (experience_level: "advanced"):
           - Include deep technical details
           - Discuss trade-offs and optimizations
           - Reference advanced patterns and techniques

        Output Format Requirements:
        - Start with a brief overview (using ## header)
        - Use ### headers for major sections
        - Use bullet points or numbered lists for key concepts
        - Use **bold** for important terms
        - Use `code` for technical terms or variable names
        - Use ```python or ```javascript for code examples
        - End with a ## Key Takeaways section

        Example structure:
        ## Personalized Explanation

        ### Overview
        [Brief introduction]

        ### Key Concepts
        - **Concept 1**: [Explanation with `code` examples]
        - **Concept 2**: [Explanation]

        ### Practical Examples
        ```python
        # code example here
        ```

        ### For Software Engineers
        - [Software-specific advice]

        ### Key Takeaways
        - [Summary points]
        """

    async def personalize_content(
        self,
        content: str,
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Personalize content based on user background

        Args:
            content: The original content to personalize
            user_profile: User's background and preferences

        Returns:
            Dictionary with personalized content and metadata
        """
        # Build the input prompt
        personalized_input = self._build_personalization_prompt(
            content,
            user_profile
        )

        # Try primary model first (Gemini)
        result = await self._try_personalize_with_model(
            model_name="gemini-2.0-flash",
            model=self.primary_model,
            input_text=personalized_input,
            content=content,
            user_profile=user_profile
        )

        # If primary model failed due to quota/rate limits and fallback is available, try OpenRouter
        if not result["success"] and self._should_use_fallback(result["error_message"]) and self.fallback_model:
            print(f"Primary model failed, attempting fallback to OpenRouter...")
            result = await self._try_personalize_with_model(
                model_name="openai/gpt-oss-120b:free",
                model=self.fallback_model,
                input_text=personalized_input,
                content=content,
                user_profile=user_profile,
                is_fallback=True
            )

        # If both models failed, use simple fallback personalization
        if not result["success"]:
            print(f"All models failed, using simple fallback personalization")
            expertise_level = user_profile.get("experience_level", "Beginner").lower()
            fallback_response = self._generate_fallback_personalization(content, expertise_level, user_profile)

            return {
                "personalized_content": fallback_response,
                "adaptations_made": result.get("adaptations", ["Generated fallback personalization due to API limitations"]),
                "original_length": len(content.split()),
                "personalized_length": len(fallback_response.split()),
                "processing_metadata": {
                    "model": "simple_fallback",
                    "error": result["error_message"],
                    "note": "All API models unavailable - using rule-based fallback"
                }
            }

        # Return successful result
        return {
            "personalized_content": result["content"],
            "adaptations_made": result["adaptations"],
            "original_length": len(content.split()),
            "personalized_length": len(result["content"].split()),
            "processing_metadata": {
                "model": result["model_name"],
                "max_turns": 3,
                "fallback_used": result.get("is_fallback", False)
            }
        }

    async def _try_personalize_with_model(
        self,
        model_name: str,
        model: Any,
        input_text: str,
        content: str,
        user_profile: Dict[str, Any],
        is_fallback: bool = False
    ) -> Dict[str, Any]:
        """
        Try to personalize content using a specific model
        """
        try:
            # Create a temporary agent with the specified model
            temp_agent = Agent(
                name="ContentPersonalizer",
                instructions=self._get_personalization_instructions(),
                model=model
            )

            # Run the agent
            result = await Runner.run(
                temp_agent,
                input_text,
                max_turns=3  # Limit turns for content generation
            )

            # Extract adaptations made
            adaptations = self._extract_adaptations(
                content,
                result.final_output,
                user_profile
            )

            if is_fallback:
                adaptations.insert(0, "Used OpenRouter fallback model due to primary API unavailability")

            return {
                "success": True,
                "content": result.final_output,
                "adaptations": adaptations,
                "model_name": model_name,
                "is_fallback": is_fallback
            }

        except Exception as e:
            error_msg = str(e)
            print(f"Error in personalization with {model_name}: {error_msg}")

            return {
                "success": False,
                "error_message": error_msg,
                "model_name": model_name
            }

    def _should_use_fallback(self, error_message: str) -> bool:
        """
        Determine if the error indicates we should use the fallback model
        """
        error_lower = error_message.lower()

        # Check for quota/rate limit errors
        quota_indicators = [
            "quota", "limit", "rate", "exceeded", "maximum", "usage",
            "429", "too many requests", "resource exhausted",
            "billing", "payment", "insufficient"
        ]

        return any(indicator in error_lower for indicator in quota_indicators)

    def _format_content_as_markdown(self, content: str) -> str:
        """
        Format the original content as markdown with proper structure
        """
        import re

        # Split content into sentences or key points
        sentences = re.split(r'[.!?]+', content)
        key_points = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

        # Limit to top 5 key points to avoid overwhelming
        key_points = key_points[:5]

        # Format as bullet points with emphasis on important terms
        markdown_points = []
        for point in key_points:
            # Add emphasis to technical terms (simple heuristic)
            point = re.sub(r'\b(important|key|critical|essential|main|primary)\b', r'**\1**', point, flags=re.IGNORECASE)
            # Add inline code for technical terms (simple heuristic)
            point = re.sub(r'\b(system|process|algorithm|method|technique|model)\b', r'`\1`', point, flags=re.IGNORECASE)
            markdown_points.append(f"- {point}")

        return '\n'.join(markdown_points)

    def _build_personalization_prompt(
        self,
        content: str,
        user_profile: Dict[str, Any]
    ) -> str:
        """
        Build the input prompt for personalization
        """
        # Build a readable profile summary
        profile_summary = []
        profile_summary.append(f"Experience Level: {user_profile.get('experience_level', 'beginner')}")
        profile_summary.append(f"Technical Focus: {user_profile.get('technical_focus', 'general')}")

        if user_profile.get('years_of_experience'):
            profile_summary.append(f"Years of Experience: {user_profile['years_of_experience']}")

        if user_profile.get('preferred_languages'):
            profile_summary.append(f"Preferred Languages: {', '.join(user_profile['preferred_languages'])}")

        if user_profile.get('hardware_expertise') and isinstance(user_profile.get('hardware_expertise'), dict):
            hw_exp = user_profile['hardware_expertise']
            hw_levels = []
            for category, level in hw_exp.items():
                if level and level != 'none':
                    hw_levels.append(f"{category}: {level}")
            if hw_levels:
                profile_summary.append(f"Hardware Expertise: {', '.join(hw_levels)}")

        profile_text = "\n        ".join(profile_summary)

        prompt = f"""
        Please personalize the following content for a user with this background:

        User Profile:
        {profile_text}

        Content to Personalize:
        {content}

        Instructions:
        - Adapt the content to match the user's expertise level ({user_profile.get('experience_level', 'beginner')})
        - Tailor examples for their technical focus ({user_profile.get('technical_focus', 'general')})
        - Use examples and analogies relevant to their background
        - Maintain all technical details and accuracy
        - Target approximately {len(content.split())} words
        - Use clear, accessible language while preserving technical depth

        Personalization Focus:
        - If beginner: Use simple explanations and analogies
        - If intermediate: Build on existing knowledge with practical examples
        - If advanced: Include deep technical details and trade-offs
        - If software focus: Include code examples, APIs, implementation patterns
        - If hardware focus: Include physical constraints, specifications, performance metrics
        """

        return prompt

    def _extract_adaptations(
        self,
        original_content: str,
        personalized_content: str,
        user_profile: Dict[str, Any]
    ) -> List[str]:
        """
        Extract and list the adaptations made during personalization
        """
        adaptations = []

        # Check for software expertise adaptations
        if user_profile.get("primary_expertise") == "software":
            if "def " in personalized_content or "function()" in personalized_content:
                adaptations.append("Added code examples for software engineers")
            if "API" in personalized_content or "SDK" in personalized_content:
                adaptations.append("Included API/SDK references")

        # Check for hardware expertise adaptations
        if user_profile.get("primary_expertise") == "hardware" or user_profile.get("technical_focus") == "hardware":
            if "watts" in personalized_content or "voltage" in personalized_content:
                adaptations.append("Added hardware specifications")
            if "physical" in personalized_content or "mechanical" in personalized_content:
                adaptations.append("Included physical constraints")
            if "cpu" in personalized_content or "gpu" in personalized_content:
                adaptations.append("Added hardware architecture details")

        # Check for beginner level adaptations
        if user_profile.get("experience_level") == "beginner":
            if "simply put" in personalized_content.lower():
                adaptations.append("Simplified complex concepts")
            if "think of" in personalized_content.lower():
                adaptations.append("Added explanatory analogies")

        # Check for expert level adaptations
        if user_profile.get("experience_level") == "expert":
            if "advanced" in personalized_content.lower():
                adaptations.append("Included advanced technical details")
            if "optimization" in personalized_content.lower():
                adaptations.append("Added performance optimization insights")

        return adaptations

    def _generate_fallback_personalization(
        self,
        content: str,
        expertise_level: str,
        user_profile: Dict[str, Any]
    ) -> str:
        """
        Generate a simple fallback personalization when the API is not available
        """
        # Log the content length for debugging
        print(f"[DEBUG] Fallback personalization - content length: {len(content)}")
        print(f"[DEBUG] First 200 chars of content: {content[:200]}")

        # If content is empty or too short, provide a more useful message
        if not content or len(content.strip()) < 20:
            return """
            **Content Not Available**

            The content could not be extracted for personalization. This might be due to:
            - The page having mostly UI elements
            - Content filtering being too aggressive
            - The page requiring login to access

            Please try:
            - Selecting specific text to personalize
            - Navigating to a page with more substantial content
            - Checking if the content is properly displayed
            """

        # Generate a structured markdown response
        prefix = f"""## Personalized Explanation

### Overview
This content is adapted for your {expertise_level} level of expertise.

### Content Analysis
{self._format_content_as_markdown(content)}"""

        # Add user-specific context if available
        user_context = ""
        if user_profile.get("technical_focus") == "hardware" or user_profile.get("primary_expertise") == "hardware":
            user_context = """

### ⚙️ Hardware Engineer Focus
Pay attention to the following:
- Physical constraints and material properties
- Power consumption and thermal considerations
- Hardware architecture implications
- Performance metrics (latency, throughput)"""
        elif user_profile.get("technical_focus") == "software" or user_profile.get("primary_expertise") == "software":
            user_context = """

### 💻 Software Engineer Focus
Consider the following:
- Implementation patterns and best practices
- API design and integration
- System architecture implications
- Code optimization techniques"""

        # Add expertise-level specific guidance
        if expertise_level == "beginner":
            guidance = """
### Learning Path
- Start with the basic concepts
- Focus on understanding the "why"
- Use the analogies provided to build mental models"""
        elif expertise_level == "intermediate":
            guidance = """
### Next Steps
- Connect these concepts to what you already know
- Try implementing the examples provided
- Explore the advanced topics mentioned"""
        else:  # advanced
            guidance = """
### Deep Dive
- Analyze the trade-offs and optimizations
- Consider edge cases and failure modes
- Explore related advanced patterns"""

        suffix = f"""
### Key Takeaways
- This explanation was personalized for your {expertise_level} level
- {'Hardware-focused insights have been provided.' if user_profile.get('technical_focus') == 'hardware' else 'Software-focused insights have been provided.' if user_profile.get('technical_focus') == 'software' else 'General insights have been provided.'}
- Continue exploring to deepen your understanding

---

*Generated by AI Personalization Assistant*"""

        return prefix + user_context + guidance + suffix