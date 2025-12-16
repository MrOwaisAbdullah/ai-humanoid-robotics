import asyncio
from openai import AsyncOpenAI
import os

async def test_gemini():
    # Configure Gemini client using OpenAI compatibility
    client = AsyncOpenAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        timeout=60.0,
        max_retries=3
    )

    try:
        # Simple test message
        response = await client.chat.completions.create(
            model="gemini-2.0-flash-lite",
            messages=[{"role": "user", "content": "What is AI?"}],
            max_tokens=100
        )
        print("Success! Response:", response.choices[0].message.content)
    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    asyncio.run(test_gemini())