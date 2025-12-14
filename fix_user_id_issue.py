#!/usr/bin/env python
"""
Fix the user_id issue in translation service.
The User.id is a string but the foreign key expects a UUID.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Read the translation_openai.py file
file_path = backend_path / "src" / "models" / "translation_openai.py"
content = file_path.read_text(encoding='utf-8')

# Change user_id from UUID to String to match the User model
content = content.replace(
    'user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)',
    'user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)'
)

# Also fix TranslationSession and TranslationMetrics user_id fields
content = content.replace(
    'user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)',
    'user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)'
)

# Write back to file
file_path.write_text(content, encoding='utf-8')

print("Fixed user_id to use String instead of UUID to match User.id field")