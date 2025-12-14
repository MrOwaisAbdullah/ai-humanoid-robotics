#!/usr/bin/env python
"""
Fix translation endpoint to handle User objects properly.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Read the translation.py file
file_path = backend_path / "src" / "api" / "v1" / "translation.py"
content = file_path.read_text(encoding='utf-8')

# Add User import
if "from src.models.auth import User" not in content:
    # Add User import after other imports
    content = content.replace(
        "from src.security.dependencies import get_current_user_or_anonymous",
        "from src.security.dependencies import get_current_user_or_anonymous\nfrom src.models.auth import User"
    )

# Fix type hints
content = content.replace(
    "current_user: Optional[Dict] = Depends(get_current_user_or_anonymous),",
    "current_user: Optional[User] = Depends(get_current_user_or_anonymous),"
)

# Fix current_user.get() calls
content = content.replace(
    'current_user.get("id") if current_user else None',
    'current_user.id if current_user else None'
)
content = content.replace(
    'current_user.get("is_admin", False)',
    'getattr(current_user, "is_admin", False)'
)

# Write back to file
file_path.write_text(content, encoding='utf-8')

print("Fixed translation endpoint to handle User objects")