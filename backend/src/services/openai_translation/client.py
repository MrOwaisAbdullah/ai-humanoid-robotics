"""
OpenAI Agents SDK Client for Gemini API.
"""

import os
from agents import AsyncOpenAI, OpenAIChatCompletionsModel


class GeminiOpenAIClient:
    """OpenAI Agents SDK client for Gemini API."""

    def __init__(self):
        """Initialize Gemini OpenAI client."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured")

        # Initialize AsyncOpenAI client for Gemini
        self.provider = AsyncOpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=api_key,
        )

        # Define the chat completions model using Gemini
        self.model = OpenAIChatCompletionsModel(
            openai_client=self.provider,
            model="gemini-2.0-flash-lite",
        )

    def get_provider(self) -> AsyncOpenAI:
        """Get the AsyncOpenAI provider."""
        return self.provider

    def get_client(self) -> AsyncOpenAI:
        """Get the AsyncOpenAI client (alias for get_provider)."""
        return self.provider

    def get_model(self) -> OpenAIChatCompletionsModel:
        """Get the OpenAI chat completions model."""
        return self.model

    async def test_connection(self) -> bool:
        """Test the connection to Gemini API."""
        try:
            # Try a simple completion request
            response = await self.provider.chat.completions.create(
                model="gemini-2.0-flash-lite",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False


def get_gemini_client() -> GeminiOpenAIClient:
    """Get the Gemini client instance."""
    return GeminiOpenAIClient()