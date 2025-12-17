"""
Test script for PersonalizationAgent fallback to OpenRouter
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory (current working directory) to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.agents.personalization_agent import PersonalizationAgent


async def test_fallback():
    """Test the PersonalizationAgent with fallback mechanism"""

    print("Initializing PersonalizationAgent...")

    # Create agent instance
    agent = PersonalizationAgent()

    # Check if OpenRouter is configured
    if not agent.openrouter_client:
        print("WARNING: OpenRouter API key not configured. Please set OPENROUTER_API_KEY environment variable.")
        print("The fallback to OpenRouter will not work without the API key.")

    # Test content and user profile
    test_content = """
    Neural networks are a fundamental concept in machine learning. They consist of layers of interconnected nodes or neurons that process information.
    Each connection has a weight that adjusts during training. The network learns by adjusting these weights to minimize the difference between predicted and actual outputs.
    """

    test_user_profile = {
        "experience_level": "beginner",
        "technical_focus": "software",
        "years_of_experience": 2,
        "preferred_languages": ["Python", "JavaScript"]
    }

    print(f"\nTest content: {test_content[:100]}...")
    print(f"User profile: {test_user_profile}")

    # Test personalization
    print("\nTesting personalization with fallback mechanism...")
    try:
        result = await agent.personalize_content(test_content, test_user_profile)

        print("\n=== PERSONALIZATION RESULT ===")
        print(f"Model used: {result['processing_metadata']['model']}")
        print(f"Fallback used: {result['processing_metadata'].get('fallback_used', False)}")
        print(f"Content length: {result['personalized_length']} words")
        print(f"Adaptations: {result['adaptations_made']}")

        print("\n=== PERSONALIZED CONTENT ===")
        print(result['personalized_content'][:500] + "..." if len(result['personalized_content']) > 500 else result['personalized_content'])

        # Check if fallback was triggered
        if result['processing_metadata'].get('fallback_used'):
            print("\n✓ Fallback to OpenRouter was triggered successfully!")
        else:
            print("\n✓ Primary Gemini model worked successfully!")

    except Exception as e:
        print(f"\nERROR during personalization: {e}")
        import traceback
        traceback.print_exc()


async def test_quota_error_simulation():
    """Test the fallback mechanism by simulating a quota error"""
    print("\n" + "="*60)
    print("Testing quota error simulation...")

    # Create agent instance
    agent = PersonalizationAgent()

    # Temporarily invalidate Gemini API key to simulate quota error
    original_gemini_key = os.getenv("GEMINI_API_KEY")
    os.environ["GEMINI_API_KEY"] = "invalid-key-to-simulate-quota-error"

    # Re-initialize the agent with invalid key
    agent_with_error = PersonalizationAgent()

    if not agent_with_error.openrouter_client:
        print("Skipping quota error test - OpenRouter not configured")
        # Restore original key
        if original_gemini_key:
            os.environ["GEMINI_API_KEY"] = original_gemini_key
        return

    test_content = "Machine learning is a method of data analysis that automates analytical model building."
    test_user_profile = {
        "experience_level": "intermediate",
        "technical_focus": "software"
    }

    try:
        result = await agent_with_error.personalize_content(test_content, test_user_profile)

        print("\n=== QUOTA ERROR TEST RESULT ===")
        print(f"Model used: {result['processing_metadata']['model']}")
        print(f"Fallback used: {result['processing_metadata'].get('fallback_used', False)}")

        if result['processing_metadata'].get('fallback_used'):
            print("✓ Fallback mechanism worked correctly!")
        elif result['processing_metadata']['model'] == 'simple_fallback':
            print("⚠ Both APIs failed - used simple fallback")
        else:
            print("❌ Fallback was not triggered as expected")

    except Exception as e:
        print(f"\nERROR during quota error test: {e}")

    # Restore original key
    if original_gemini_key:
        os.environ["GEMINI_API_KEY"] = original_gemini_key


if __name__ == "__main__":
    print("PersonalizationAgent Fallback Test")
    print("=" * 60)

    # Check environment
    print("\nEnvironment Check:")
    print(f"GEMINI_API_KEY: {'✓ Set' if os.getenv('GEMINI_API_KEY') else '✗ Not set'}")
    print(f"OPENROUTER_API_KEY: {'✓ Set' if os.getenv('OPENROUTER_API_KEY') else '✗ Not set'}")

    # Run tests
    asyncio.run(test_fallback())
    asyncio.run(test_quota_error_simulation())

    print("\n" + "="*60)
    print("Test complete!")
    print("\nTo get an OpenRouter API key:")
    print("1. Go to https://openrouter.ai/keys")
    print("2. Sign up or log in")
    print("3. Generate a new API key")
    print("4. Set the OPENROUTER_API_KEY environment variable")