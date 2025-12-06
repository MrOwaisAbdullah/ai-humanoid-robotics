#!/bin/bash
# Generate uv.lock file for reproducible builds

echo "Generating uv.lock file..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Initialize git repository if not exists
if [ ! -d .git ]; then
    git init
    git add pyproject.toml
    git commit -m "Initial: Add pyproject.toml"
fi

# Generate lock file
uv sync --frozen --dev

echo "uv.lock generated successfully!"
echo ""
echo "Next steps:"
echo "1. Commit the lock file to git:"
echo "   git add uv.lock"
echo "   git commit -m 'Add uv.lock for reproducible builds'"
echo ""
echo "2. Your project is ready to use with uv!"