#!/bin/bash

# Deploy backend to Hugging Face Spaces
# Usage: ./deploy_hf.sh [space-name]

set -e

# Default space name
SPACE_NAME=${1:-"mrowaisabdullah-ai-humanoid-robotics"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying backend to Hugging Face Spaces${NC}"
echo "Space name: ${SPACE_NAME}"
echo ""

# Check if HF_TOKEN is set
if [ -z "$HF_TOKEN" ]; then
    echo -e "${RED}Error: HF_TOKEN environment variable is not set${NC}"
    echo "Please set it with: export HF_TOKEN=your_token_here"
    exit 1
fi

# Create temporary directory for the space
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: ${TEMP_DIR}"

# Function to cleanup
cleanup() {
    rm -rf "$TEMP_DIR"
    echo -e "${YELLOW}Cleaned up temporary directory${NC}"
}
trap cleanup EXIT

# Clone the space repository
echo -e "${YELLOW}Cloning Hugging Face Space...${NC}"
git clone https://huggingface.co/spaces/$SPACE_NAME "$TEMP_DIR"

# Copy backend files
echo -e "${YELLOW}Copying backend files...${NC}"
cp -r backend/* "$TEMP_DIR/"
cp -r backend/.* "$TEMP_DIR/" 2>/dev/null || true

# Create app.py if it doesn't exist
if [ ! -f "$TEMP_DIR/app.py" ]; then
    echo -e "${YELLOW}Creating app.py for HF Spaces...${NC}"
    cat > "$TEMP_DIR/app.py" << EOF
# Entry point for HF Spaces
import uvicorn
from main import app

if __name__ == '__main__':
    uvicorn(app, host='0.0.0.0', port=7860)
EOF
fi

# Change to the space directory
cd "$TEMP_DIR"

# Configure git
git config user.email "actions@github.com"
git config user.name "Deploy Script"

# Add and commit changes
echo -e "${YELLOW}Committing changes...${NC}"
git add .

# Check if there are changes
if git diff --staged --quiet; then
    echo -e "${GREEN}No changes to commit${NC}"
    exit 0
fi

git commit -m "Deploy backend from local development

🚀 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to Hugging Face
echo -e "${YELLOW}Pushing to Hugging Face Spaces...${NC}"
git push origin main

echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo "Space URL: https://huggingface.co/spaces/$SPACE_NAME"
echo "API Endpoint: https://$SPACE_NAME.hf.space"
echo ""
echo "The space will take a few minutes to build and start."
echo "You can monitor the build progress at the URL above."