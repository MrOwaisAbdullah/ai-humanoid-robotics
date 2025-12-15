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
        self.model = OpenAIChatCompletionsModel(
            model="gemini-2.0-flash",
            openai_client=self.client,
            temperature=0.7,
            top_p=0.9,
            max_tokens=2048
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

        1. For Software Engineers:
           - Use code examples and API references
           - Include implementation patterns
           - Reference relevant frameworks/libraries
           - Focus on practical application

        2. For Hardware Engineers:
           - Include physical constraints and considerations
           - Reference material properties and specifications
           - Include performance metrics (power, latency, throughput)
           - Focus on system-level implications

        3. For Mixed Background:
           - Balance between hardware and software aspects
           - Provide layered explanations (high-level → detailed)
           - Include both implementation and system considerations

        Guidelines:
        - Maintain technical accuracy above all
        - Add context-specific analogies when helpful
        - Include "For [background]:" prefixes when making specialized references
        - Preserve the original content length (target ~2000 words)
        - Use clear section headers and bullet points
        - Include practical examples relevant to the user's background
        - Start with a brief overview
        - Break into logical sections
        - Use code blocks for technical details
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
            # Log error and return error response
            print(f"Error in personalization: {str(e)}")
            return {
                "personalized_content": None,
                "error": f"Personalization failed: {str(e)}",
                "adaptations_made": [],
                "original_length": len(content.split()),
                "personalized_length": 0
            }

    def _build_personalization_prompt(
        self,
        content: str,
        user_profile: Dict[str, Any]
    ) -> str:
        """
        Build the input prompt for personalization
        """
        profile_text = json.dumps(user_profile, indent=2)

        prompt = f"""
        Please personalize the following content for a user with this background:

        User Profile:
        {profile_text}

        Content to Personalize:
        {content}

        Instructions:
        - Adapt the content to match the user's expertise level
        - Use examples and analogies relevant to their background
        - Maintain all technical details and accuracy
        - Target approximately {len(content.split())} words
        - Use clear, accessible language while preserving technical depth
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
        if user_profile.get("hardware_expertise") and user_profile["hardware_expertise"] != "none":
            if "watts" in personalized_content or "voltage" in personalized_content:
                adaptations.append("Added hardware specifications")
            if "physical" in personalized_content or "mechanical" in personalized_content:
                adaptations.append("Included physical constraints")

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