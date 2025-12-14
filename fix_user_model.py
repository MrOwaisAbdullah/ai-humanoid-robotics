#!/usr/bin/env python
"""
Fix the User model to add translation relationships.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Read the auth.py file
auth_file = backend_path / "src" / "models" / "auth.py"
content = auth_file.read_text(encoding='utf-8')

# Find the User model's relationships section
import_start = content.find("    # Relationships")
if import_start == -1:
    print("Could not find relationships section in User model")
    sys.exit(1)

# Find where the relationships end
relationships_end = content.find("\n\n", import_start)
if relationships_end == -1:
    relationships_end = content.find("\nclass", import_start)

if relationships_end == -1:
    print("Could not find end of relationships section")
    sys.exit(1)

# Extract the relationships section
relationships_section = content[import_start:relationships_end]

# Check if translation relationships already exist
if "translation_jobs" in relationships_section:
    print("Translation relationships already exist in User model")
else:
    # Add the translation relationships
    new_relationships = relationships_section.rstrip()
    if not new_relationships.endswith('\n'):
        new_relationships += '\n'
    new_relationships += """    translation_jobs = relationship("TranslationJob", back_populates="user", cascade="all, delete-orphan")
    translation_sessions = relationship("TranslationSession", back_populates="user", cascade="all, delete-orphan")
    translation_metrics = relationship("TranslationMetrics", back_populates="user", cascade="all, delete-orphan")"""

    # Replace the old relationships section with the new one
    new_content = content[:import_start] + new_relationships + content[relationships_end:]

    # Write back to file
    auth_file.write_text(new_content, encoding='utf-8')
    print("✅ Added translation relationships to User model")