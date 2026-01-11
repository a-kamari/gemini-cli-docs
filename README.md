# Gemini CLI Documentation Mirror

Community-maintained local mirror of [Google Gemini CLI](https://github.com/google-gemini/gemini-cli) documentation for fast, offline access.

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/gemini-cli-docs/main/install.sh | bash
```

## Usage

After installation, use the `/gdocs` command in Claude Code or Gemini CLI:

```bash
/gdocs                  # List all available topics
/gdocs quickstart       # Read specific documentation
/gdocs -t               # Check sync status
/gdocs what's new       # Show recent documentation changes
/gdocs changelog        # View version history
/gdocs search hooks     # Search across all docs
```

## Features

- **Fast Local Access**: Documentation cached locally for instant reading
- **Auto-Updates**: Syncs with GitHub automatically (~0.4s check)
- **Change Tracking**: Full git history shows what changed and when
- **Cross-CLI Support**: Works with both Gemini CLI and Claude Code
- **Offline Capable**: Read docs without internet (sync check skipped)

## Documentation Sources

This mirror fetches documentation from:
- **Primary**: [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) `/docs` folder

## Available Topics

After installation, run `/gdocs` to see all available topics.

## How It Works

1. **GitHub Actions** fetches documentation every 6 hours from the Gemini CLI repository
2. **Markdown files** are stored in the `docs/` folder
3. **Local helper script** provides the `/gdocs` command interface
4. **Git sync** ensures you always have the latest content

## Uninstall

```bash
~/.gemini-cli-docs/uninstall.sh
```

Or manually:
```bash
rm -rf ~/.gemini-cli-docs
rm -f ~/.claude/commands/gdocs.md
rm -f ~/.gemini/commands/gdocs.md
```

## Attribution

Documentation content belongs to **Google LLC** and is sourced from the [official Gemini CLI repository](https://github.com/google-gemini/gemini-cli).

This is a **community mirror** for convenience - not affiliated with Google.

## License

- **Wrapper code** (installer, helper scripts): MIT License
- **Documentation content**: Copyright Google LLC, see [original repository](https://github.com/google-gemini/gemini-cli) for terms

## Related

- [Official Gemini CLI](https://github.com/google-gemini/gemini-cli)
- [Official Documentation](https://geminicli.com/docs/)
- [Claude Code Docs](https://github.com/ericbuess/claude-code-docs) - Similar project for Claude Code
