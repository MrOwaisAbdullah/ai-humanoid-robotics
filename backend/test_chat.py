#!/usr/bin/env python3
"""
Test script to check chat functionality directly.
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent))

from rag.qdrant_client import QdrantManager
from rag.chat import ChatHandler
from dotenv import load_dotenv

load_dotenv()

async def test_chat():
    """Test chat functionality."""
    print("=" * 60)
    print("TESTING CHAT FUNCTIONALITY")
    print("=" * 60)

    # Test queries
    test_queries = [
        "What is humanoid robotics?",
        "What are the main components of a humanoid robot?",
        "Explain the kinematics of robotic arms",
        "What sensors do humanoid robots use?"
    ]

    try:
        # Initialize Qdrant manager
        print("\n1. Initializing Qdrant...")
        qdrant_manager = QdrantManager(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        await qdrant_manager.initialize()

        # Initialize chat handler
        print("2. Initializing Chat Handler...")
        chat_handler = ChatHandler(
            qdrant_manager=qdrant_manager,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_MODEL", "gpt-5-nano"),
            embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        )

        # Test each query
        for i, query in enumerate(test_queries):
            print(f"\n3.{i+1} Testing query: {query}")
            print("-" * 40)

            try:
                response = await chat_handler.chat(
                    query=query,
                    k=3,
                    context_window=4000
                )

                print(f"Answer: {response.answer[:300]}...")
                print(f"Sources: {len(response.sources)} citations")
                print(f"Response time: {response.response_time:.2f}s")
                print(f"Tokens used: {response.tokens_used}")

                # Check if answer mentions lack of context
                if "context" in response.answer.lower() and "don't have" in response.answer.lower():
                    print("[WARNING] Chatbot says it doesn't have context!")

                # Check citations
                if response.sources:
                    for j, source in enumerate(response.sources):
                        print(f"  Source {j+1}: {source.document_id} (score: {source.relevance_score:.3f})")

            except Exception as e:
                print(f"[ERROR] Query failed: {str(e)}")

        print("\n" + "=" * 60)
        print("CHAT TEST COMPLETE")
        print("=" * 60)

        # Cleanup
        await chat_handler.close()
        await qdrant_manager.close()

    except Exception as e:
        print(f"[ERROR] Test failed: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_chat())