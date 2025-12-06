# PowerShell script to generate uv.lock file for reproducible builds

Write-Host "Generating uv.lock file..." -ForegroundColor Green

# Check if uv is installed
$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvCommand) {
    Write-Host "Installing uv..." -ForegroundColor Yellow
    irm https://astral.sh/uv/install.ps1 | iex
}

# Initialize git repository if not exists
if (-not (Test-Path .git)) {
    git init
    git add pyproject.toml
    git commit -m "Initial: Add pyproject.toml"
}

# Generate lock file
Write-Host "Running uv sync..." -ForegroundColor Blue
uv sync --frozen --dev

Write-Host "uv.lock generated successfully!" -ForegroundColor Green
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Commit the lock file to git:"
Write-Host "   git add uv.lock"
Write-Host "   git commit -m 'Add uv.lock for reproducible builds'"
Write-Host ""
Write-Host "2. Your project is ready to use with uv!" -ForegroundColor Green