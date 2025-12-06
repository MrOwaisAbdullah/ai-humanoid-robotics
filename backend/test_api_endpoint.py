#!/usr/bin/env python3
"""
Test script to check the API endpoint directly.
"""

import asyncio
import aiohttp
import json
import sys

async def test_chat_api():
    """Test the /chat API endpoint."""
    print("=" * 60)
    print("TESTING CHAT API ENDPOINT")
    print("=" * 60)

    base_url = "http://localhost:7860"

    test_cases = [
        {
            "name": "Simple query",
            "payload": {
                "question": "What is humanoid robotics?",
                "stream": False
            }
        },
        {
            "name": "With session ID",
            "payload": {
                "question": "What are the main components of a humanoid robot?",
                "session_id": "test-session-123",
                "stream": False
            }
        },
        {
            "name": "With custom k value",
            "payload": {
                "question": "Explain robot sensors",
                "k": 5,
                "stream": False
            }
        }
    ]

    async with aiohttp.ClientSession() as session:
        for test_case in test_cases:
            print(f"\n{test_case['name']}:")
            print(f"Request: {test_case['payload']['question']}")
            print("-" * 40)

            try:
                async with session.post(
                    f"{base_url}/chat",
                    json=test_case["payload"],
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"Status: {response.status}")
                        print(f"Answer: {data.get('answer', 'No answer')[:200]}...")
                        print(f"Sources: {len(data.get('sources', []))}")
                        print(f"Response time: {data.get('response_time', 0):.2f}s")

                        # Check for common issues
                        if "context" in data.get('answer', '').lower() and "don't" in data.get('answer', '').lower():
                            print("[WARNING] Chatbot indicates no context available!")
                    else:
                        error_text = await response.text()
                        print(f"Error: {response.status} - {error_text}")

            except aiohttp.ClientError as e:
                print(f"[ERROR] Could not connect to API: {str(e)}")
                print("\nMake sure the API server is running:")
                print("  cd backend && uv run python main.py")
                break

    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_chat_api())