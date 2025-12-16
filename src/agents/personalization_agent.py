"""
Personalization Agent for Content Adaptation
Handles AI-powered content personalization based on user background
"""

import os
import json
from typing import Dict, Any, List
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled


class PersonalizationAgent:
    """
    AI Agent for personalizing technical content based on user expertise
    """

    def __init__(self):
        """Initialize the personalization agent with Gemini configuration"""
        # Disable tracing for non-OpenAI providers
        set_tracing_disabled(True)

        # Configure Gemini client using OpenAI compatibility
        self.client = AsyncOpenAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            timeout=60.0,
            max_retries=3
        )

        # Configure the model wrapper
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.model = OpenAIChatCompletionsModel(
            model=model_name,
            openai_client=self.client
        )

        # Initialize the agent
        self.agent = Agent(
            name="ContentPersonalizer",
            instructions=self._get_personalization_instructions(),
            model=self.model
        )

    def _get_personalization_instructions(self) -> str:
        """
        Get the instructions for the personalization agent
        """
        return """
        You are a Content Personalization AI that adapts technical content based on user expertise.

        Your task is to personalize technical explanations while maintaining accuracy and clarity.

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

        Guidelines:
        - Maintain technical accuracy above all
        - Add context-specific analogies when helpful
        - Include "For [background]:" prefixes when making specialized references
        - Preserve the original content length approximately
        - Use clear section headers and bullet points
        - Include practical examples relevant to the user's background
        - Start with a brief overview
        - Break into logical sections
        - Use code blocks for technical details when relevant to software
        - Include hardware specifications when relevant to hardware focus
        - End with a summary of key takeaways
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

        try:
            # Run the agent using the correct API
            result = await Runner.run(
                self.agent,
                personalized_input,
                max_turns=3  # Limit turns for content generation
            )

            # Extract adaptations made
            adaptations = self._extract_adaptations(
                content,
                result.final_output,
                user_profile
            )

            return {
                "personalized_content": result.final_output,
                "adaptations_made": adaptations,
                "original_length": len(content.split()),
                "personalized_length": len(result.final_output.split()),
                "processing_metadata": {
                    "model": "gemini-2.0-flash",
                    "max_turns": 3
                }
            }

        except Exception as e:
            # Log error and provide fallback response
            print(f"Error in personalization: {str(e)}")

            # Fallback simple personalization
            expertise_level = user_profile.get("experience_level", "Beginner").lower()
            fallback_response = self._generate_fallback_personalization(content, expertise_level, user_profile)

            return {
                "personalized_content": fallback_response,
                "adaptations_made": ["Generated fallback personalization due to API limitation"],
                "original_length": len(content.split()),
                "personalized_length": len(fallback_response.split()),
                "processing_metadata": {
                    "model": "fallback",
                    "max_turns": 1,
                    "note": "Fallback generated due to API limitation"
                }
            }

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
        # Simple prefix based on expertise level
        if expertise_level == "beginner":
            prefix = """📚 **For Beginners**: Let me break this down in simple terms.

This content is being presented with additional context to help you understand the fundamentals. """

        elif expertise_level == "intermediate":
            prefix = """🔧 **For Intermediate Learners**: Building on your existing knowledge.

This explanation assumes you're familiar with basic concepts and focuses on practical applications. """

        else:  # advanced
            prefix = """⚡ **For Advanced Users**: Deep technical insights.

This content is tailored for those with extensive experience in the field. """

        # Add user-specific context if available
        user_context = ""
        if user_profile.get("technical_focus") == "hardware" or user_profile.get("primary_expertise") == "hardware":
            user_context = "\n\n⚙️ **Hardware Engineer Focus**: Pay attention to the physical constraints, power consumption, and hardware architecture implications."
        elif user_profile.get("technical_focus") == "software" or user_profile.get("primary_expertise") == "software":
            user_context = "\n\n💻 **Software Engineer Focus**: Consider how these concepts apply to software implementation, APIs, and system design."

        suffix = f"""

---
*This personalized explanation was generated for a {expertise_level} level user{', ' + user_profile.get('primary_expertise', '') if user_profile.get('primary_expertise') else ''}.*

**Key Points to Remember:**
• Focus on understanding the core concepts
• Relate this to your specific interests and background
• Practice applying these concepts in real scenarios
• Don't hesitate to seek additional resources if needed"""

        return prefix + content + user_context + suffix