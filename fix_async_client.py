#!/usr/bin/env python
"""
Fix the async client initialization in get_translation_service().
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Read the service.py file
file_path = backend_path / "src" / "services" / "openai_translation" / "service.py"
content = file_path.read_text(encoding='utf-8')

# Find and replace the get_translation_service function
old_function = """async def get_translation_service() -> OpenAITranslationService:
    \"\"\"Get or create OpenAI translation service instance.\"\"\"
    global _translation_service

    if _translation_service is None:
        _translation_service = OpenAITranslationService()

    return _translation_service"""

new_function = """async def get_translation_service() -> OpenAITranslationService:
    \"\"\"Get or create OpenAI translation service instance.\"\"\"
    global _translation_service

    if _translation_service is None:
        _translation_service = OpenAITranslationService()
        # Initialize the async client
        _translation_service.gemini_client = await get_gemini_client()

    return _translation_service"""

content = content.replace(old_function, new_function)

# Write back to file
file_path.write_text(content, encoding='utf-8')

print("Fixed async client initialization in get_translation_service()")