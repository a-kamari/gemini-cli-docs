#!/bin/bash
set -euo pipefail

# Gemini CLI Docs Installer v1.0.0
# This script installs gemini-cli-docs to ~/.gemini-cli-docs

echo "Gemini CLI Docs Installer v1.0.0"
echo "================================="

# Fixed installation location
INSTALL_DIR="$HOME/.gemini-cli-docs"
REPO_URL="https://github.com/YOUR_USERNAME/gemini-cli-docs.git"
INSTALL_BRANCH="main"

# Detect OS type
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
    echo "Detected macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="linux"
    echo "Detected Linux"
else
    echo "Error: Unsupported OS type: $OSTYPE"
    echo "This installer supports macOS and Linux only"
    exit 1
fi

# Check dependencies
echo "Checking dependencies..."
for cmd in git jq curl; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "Error: $cmd is required but not installed"
        echo "Please install $cmd and try again"
        exit 1
    fi
done
echo "All dependencies satisfied"

# Main installation logic
echo ""

if [[ -d "$INSTALL_DIR" && -f "$INSTALL_DIR/docs/docs_manifest.json" ]]; then
    echo "Found existing installation at ~/.gemini-cli-docs"
    echo "Updating to latest version..."

    cd "$INSTALL_DIR"

    # Set git config for pull strategy
    if ! git config pull.rebase >/dev/null 2>&1; then
        git config pull.rebase false
    fi

    # Try regular pull
    if git pull --quiet origin "$INSTALL_BRANCH" 2>/dev/null; then
        echo "Updated successfully"
    else
        echo "Standard update failed, trying harder..."
        git fetch origin "$INSTALL_BRANCH" 2>/dev/null || true
        git reset --hard "origin/$INSTALL_BRANCH" 2>/dev/null || true
        echo "Updated to clean state"
    fi
else
    echo "Installing fresh to ~/.gemini-cli-docs..."
    git clone -b "$INSTALL_BRANCH" "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Set up the helper script
echo ""
echo "Setting up Gemini CLI Docs v1.0.0..."

echo "Installing helper script..."
if [[ -f "$INSTALL_DIR/scripts/gemini-docs-helper.sh.template" ]]; then
    cp "$INSTALL_DIR/scripts/gemini-docs-helper.sh.template" "$INSTALL_DIR/gemini-docs-helper.sh"
    chmod +x "$INSTALL_DIR/gemini-docs-helper.sh"
    echo "Helper script installed"
else
    echo "Template file missing, attempting recovery..."
    if curl -fsSL "https://raw.githubusercontent.com/YOUR_USERNAME/gemini-cli-docs/$INSTALL_BRANCH/scripts/gemini-docs-helper.sh.template" -o "$INSTALL_DIR/gemini-docs-helper.sh" 2>/dev/null; then
        chmod +x "$INSTALL_DIR/gemini-docs-helper.sh"
        echo "Helper script downloaded directly"
    else
        echo "Failed to install helper script"
        exit 1
    fi
fi

# Create /gdocs command for Claude Code
if [[ -d "$HOME/.claude" ]] || mkdir -p "$HOME/.claude/commands" 2>/dev/null; then
    echo "Setting up /gdocs command for Claude Code..."
    mkdir -p "$HOME/.claude/commands"

    cat > "$HOME/.claude/commands/gdocs.md" << 'EOF'
Execute the Gemini CLI Docs helper script at ~/.gemini-cli-docs/gemini-docs-helper.sh

Usage:
- /gdocs - List all available documentation topics
- /gdocs <topic> - Read specific documentation with link to official docs
- /gdocs -t - Check sync status without reading a doc
- /gdocs -t <topic> - Check freshness then read documentation
- /gdocs what's new - Show recent documentation changes
- /gdocs search <term> - Search across all documentation
- /gdocs changelog - View Gemini CLI version history

Every request checks for the latest documentation from GitHub (takes ~0.4s).
The helper script handles all functionality including auto-updates.

Execute: ~/.gemini-cli-docs/gemini-docs-helper.sh "$ARGUMENTS"
EOF

    echo "Created /gdocs command for Claude Code"
fi

# Create /gdocs command for Gemini CLI (if .gemini directory exists)
if [[ -d "$HOME/.gemini" ]] || mkdir -p "$HOME/.gemini/commands" 2>/dev/null; then
    echo "Setting up /gdocs command for Gemini CLI..."
    mkdir -p "$HOME/.gemini/commands"

    cat > "$HOME/.gemini/commands/gdocs.md" << 'EOF'
Execute the Gemini CLI Docs helper script at ~/.gemini-cli-docs/gemini-docs-helper.sh

Usage:
- /gdocs - List all available documentation topics
- /gdocs <topic> - Read specific documentation
- /gdocs -t - Check sync status
- /gdocs what's new - Show recent documentation changes
- /gdocs search <term> - Search across all documentation

Execute: ~/.gemini-cli-docs/gemini-docs-helper.sh "$ARGUMENTS"
EOF

    echo "Created /gdocs command for Gemini CLI"
fi

# Success message
echo ""
echo "Gemini CLI Docs v1.0.0 installed successfully!"
echo ""
echo "Command: /gdocs"
echo "Location: ~/.gemini-cli-docs"
echo ""
echo "Usage examples:"
echo "  /gdocs quickstart     # Read quickstart documentation"
echo "  /gdocs -t             # Check when docs were last updated"
echo "  /gdocs what's new     # See recent documentation changes"
echo "  /gdocs search hooks   # Search for 'hooks' in all docs"
echo ""
echo "Available topics:"
if [[ -d "$INSTALL_DIR/docs" ]]; then
    ls "$INSTALL_DIR/docs" 2>/dev/null | grep '\.md$' | sed 's/\.md$//' | sort | column -c 60
else
    echo "(Run the fetcher to populate documentation)"
fi
echo ""
echo "Restart your CLI tool for the /gdocs command to take effect"
