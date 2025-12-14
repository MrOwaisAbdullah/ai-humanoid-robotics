#!/usr/bin/env python
"""
Replace JSONB with JSON for SQLite compatibility.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Read the translation_openai.py file
model_file = backend_path / "src" / "models" / "translation_openai.py"
content = model_file.read_text(encoding='utf-8')

# Replace all JSONB with JSON
content = content.replace('JSONB', 'JSON')

# Remove JSONB from imports since we're using JSON from sqlalchemy
content = content.replace('from sqlalchemy.dialects.postgresql import UUID, JSONB',
                         'from sqlalchemy.dialects.postgresql import UUID')

# Write back to file
model_file.write_text(content, encoding='utf-8')

print("Fixed JSONB to JSON conversion")