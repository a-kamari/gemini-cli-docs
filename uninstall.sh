#!/bin/bash
set -euo pipefail

# Gemini CLI Docs Uninstaller v1.0.0

echo "Gemini CLI Docs Uninstaller"
echo "==========================="
echo ""

INSTALL_DIR="$HOME/.gemini-cli-docs"

echo "This will remove:"
echo "  - The installation directory: $INSTALL_DIR"
echo "  - The /gdocs command from ~/.claude/commands/gdocs.md"
echo "  - The /gdocs command from ~/.gemini/commands/gdocs.md"
echo ""

read -p "Are you sure you want to uninstall? [y/N]: " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

echo ""
echo "Uninstalling..."

# Remove Claude Code command
if [[ -f "$HOME/.claude/commands/gdocs.md" ]]; then
    rm -f "$HOME/.claude/commands/gdocs.md"
    echo "Removed Claude Code /gdocs command"
fi

# Remove Gemini CLI command
if [[ -f "$HOME/.gemini/commands/gdocs.md" ]]; then
    rm -f "$HOME/.gemini/commands/gdocs.md"
    echo "Removed Gemini CLI /gdocs command"
fi

# Remove installation directory
if [[ -d "$INSTALL_DIR" ]]; then
    rm -rf "$INSTALL_DIR"
    echo "Removed installation directory"
fi

echo ""
echo "Gemini CLI Docs has been uninstalled."
echo ""
echo "To reinstall, run:"
echo "  curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/gemini-cli-docs/main/install.sh | bash"
