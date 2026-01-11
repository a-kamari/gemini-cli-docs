#!/bin/bash
set -euo pipefail

# Gemini CLI Documentation Helper Script v1.0.0
# This script handles all /gdocs command functionality
# Installation path: ~/.gemini-cli-docs/gemini-docs-helper.sh

# Script version
SCRIPT_VERSION="1.0.0"

# Fixed installation path
DOCS_PATH="$HOME/.gemini-cli-docs"
MANIFEST="$DOCS_PATH/docs/docs_manifest.json"

# Enhanced sanitize function to prevent command injection
sanitize_input() {
    echo "$1" | sed 's/[^a-zA-Z0-9 _.,'\''?-]//g' | sed 's/  */ /g' | sed 's/^ *//;s/ *$//'
}

# Function to print documentation header
print_doc_header() {
    echo "Community Mirror: https://github.com/a-kamari/gemini-cli-docs"
    echo "Official Docs: https://geminicli.com/docs"
    echo "Source Repo: https://github.com/google-gemini/gemini-cli"
    echo ""
    echo "Documentation content belongs to Google LLC."
    echo ""
}

# Function to auto-update docs if needed
auto_update() {
    cd "$DOCS_PATH" 2>/dev/null || return 1

    local BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")

    # Quick fetch to check for updates
    if ! git fetch --quiet origin "$BRANCH" 2>/dev/null; then
        if ! git fetch --quiet origin main 2>/dev/null; then
            return 2
        fi
        BRANCH="main"
    fi

    local LOCAL=$(git rev-parse HEAD 2>/dev/null)
    local REMOTE=$(git rev-parse origin/"$BRANCH" 2>/dev/null)
    local BEHIND=$(git rev-list HEAD..origin/"$BRANCH" --count 2>/dev/null || echo "0")

    if [[ "$LOCAL" != "$REMOTE" ]] && [[ "$BEHIND" -gt 0 ]]; then
        echo "Updating documentation..." >&2
        git pull --quiet origin "$BRANCH" 2>&1 | grep -v "Merge made by" || true
    fi

    return 0
}

# Function to show documentation sync status
show_freshness() {
    print_doc_header

    if [[ ! -f "$MANIFEST" ]]; then
        echo "Error: Documentation not found at ~/.gemini-cli-docs"
        echo "Please reinstall with:"
        echo "curl -fsSL https://raw.githubusercontent.com/a-kamari/gemini-cli-docs/main/install.sh | bash"
        exit 1
    fi

    auto_update
    local sync_status=$?

    if [[ $sync_status -eq 2 ]]; then
        echo "Could not sync with GitHub (using local cache)"
    else
        cd "$DOCS_PATH" 2>/dev/null || exit 1
        local BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
        local COMPARE_BRANCH="$BRANCH"
        if ! git rev-parse --verify origin/"$BRANCH" >/dev/null 2>&1; then
            COMPARE_BRANCH="main"
        fi
        local AHEAD=$(git rev-list origin/"$COMPARE_BRANCH"..HEAD --count 2>/dev/null || echo "0")
        local BEHIND=$(git rev-list HEAD..origin/"$COMPARE_BRANCH" --count 2>/dev/null || echo "0")

        if [[ "$AHEAD" -gt 0 ]]; then
            echo "Local version is ahead of GitHub by $AHEAD commit(s)"
        elif [[ "$BEHIND" -gt 0 ]]; then
            echo "Local version is behind GitHub by $BEHIND commit(s)"
        else
            echo "You have the latest documentation"
        fi
    fi

    cd "$DOCS_PATH" 2>/dev/null || exit 1
    local BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    echo "Branch: ${BRANCH}"
    echo "Version: ${SCRIPT_VERSION}"
}

# Function to read documentation
read_doc() {
    local topic=$(sanitize_input "$1")

    # Strip .md extension if user included it
    topic="${topic%.md}"

    local doc_path="$DOCS_PATH/docs/${topic}.md"

    if [[ -f "$doc_path" ]]; then
        print_doc_header

        cd "$DOCS_PATH" 2>/dev/null || exit 1
        local BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
        local VERSION=$SCRIPT_VERSION

        # Do the fetch to check status
        local COMPARE_BRANCH="$BRANCH"
        if ! git fetch --quiet origin "$BRANCH" 2>/dev/null; then
            if git fetch --quiet origin main 2>/dev/null; then
                COMPARE_BRANCH="main"
            else
                echo "Could not check GitHub for updates - using cached docs (v$VERSION, $BRANCH)"
                echo ""
                cat "$doc_path"
                echo ""
                echo "Official page: https://geminicli.com/docs/$topic"
                return
            fi
        fi

        local LOCAL=$(git rev-parse HEAD 2>/dev/null)
        local REMOTE=$(git rev-parse origin/"$COMPARE_BRANCH" 2>/dev/null)
        local BEHIND=$(git rev-list HEAD..origin/"$COMPARE_BRANCH" --count 2>/dev/null || echo "0")

        if [[ "$LOCAL" != "$REMOTE" ]] && [[ "$BEHIND" -gt 0 ]]; then
            echo "Updating to latest documentation..."
            git pull --quiet origin "$COMPARE_BRANCH" 2>&1 | grep -v "Merge made by" || true
            echo "Updated to latest (v$VERSION, $BRANCH)"
        else
            local AHEAD=$(git rev-list origin/"$COMPARE_BRANCH"..HEAD --count 2>/dev/null || echo "0")
            if [[ "$AHEAD" -gt 0 ]]; then
                echo "Using local development version (v$VERSION, $BRANCH, +$AHEAD commits)"
            else
                echo "You have the latest docs (v$VERSION, $BRANCH)"
            fi
        fi
        echo ""

        cat "$doc_path"
        echo ""

        # Generate appropriate official link
        if [[ "$topic" == "changelog" ]]; then
            echo "Official source: https://github.com/google-gemini/gemini-cli/blob/main/CHANGELOG.md"
        else
            # Convert filename back to path for official docs
            local url_path=$(echo "$topic" | sed 's/__/\//g')
            echo "Official page: https://geminicli.com/docs/$url_path"
        fi
    else
        # Search interface
        print_doc_header
        echo "Searching for: $topic"
        echo ""

        local keywords=$(echo "$topic" | grep -o '[a-zA-Z0-9_-]\+' | grep -v -E '^(tell|me|about|explain|what|is|are|how|do|to|show|find|search|the|for|in)$' | tr '\n' ' ')

        if [[ -n "$keywords" ]]; then
            local escaped_keywords=$(echo "$keywords" | sed 's/[[\.*^$()+?{|]/\\&/g')
            local matches=$(ls "$DOCS_PATH/docs" | grep '\.md$' | sed 's/\.md$//' | grep -i -E "$(echo "$escaped_keywords" | tr ' ' '|')" | sort)

            if [[ -n "$matches" ]]; then
                echo "Found these related topics:"
                echo "$matches" | sed 's/^/  - /'
                echo ""
                echo "Try: /gdocs <topic> to read a specific document"
            else
                echo "No exact matches found. Here are all available topics:"
                ls "$DOCS_PATH/docs" | grep '\.md$' | sed 's/\.md$//' | sort | column -c 80
            fi
        else
            echo "Available topics:"
            ls "$DOCS_PATH/docs" | grep '\.md$' | sed 's/\.md$//' | sort | column -c 80
        fi
        echo ""
        echo "Tip: Use /gdocs search <term> to search across all docs"
    fi
}

# Function to list available documentation
list_docs() {
    print_doc_header

    auto_update

    echo "Available Gemini CLI documentation topics:"
    echo ""
    ls "$DOCS_PATH/docs" | grep '\.md$' | sed 's/\.md$//' | sort | column -c 80
    echo ""
    echo "Usage: /gdocs <topic> or /gdocs -t to check freshness"
}

# Function to search documentation
search_docs() {
    local search_term=$(sanitize_input "$1")

    if [[ -z "$search_term" ]]; then
        echo "Usage: /gdocs search <term>"
        return 1
    fi

    print_doc_header
    echo "Searching for: $search_term"
    echo ""

    cd "$DOCS_PATH/docs" 2>/dev/null || exit 1

    local results=$(grep -l -i "$search_term" *.md 2>/dev/null | sed 's/\.md$//')

    if [[ -n "$results" ]]; then
        echo "Found in these documents:"
        echo "$results" | while read -r doc; do
            echo "  - $doc"
            # Show first matching line as context
            local context=$(grep -i -m 1 "$search_term" "${doc}.md" 2>/dev/null | head -c 100)
            if [[ -n "$context" ]]; then
                echo "    \"$context...\""
            fi
        done
    else
        echo "No matches found for: $search_term"
    fi
}

# Function for hook check (auto-update)
hook_check() {
    exit 0
}

# Function to show what's new
whats_new() {
    set +e

    print_doc_header
    auto_update || true

    cd "$DOCS_PATH" 2>/dev/null || {
        echo "Error: Could not access documentation directory"
        return 1
    }

    echo "Recent documentation updates:"
    echo ""

    local count=0

    while IFS= read -r commit_line && [[ $count -lt 5 ]]; do
        local hash=$(echo "$commit_line" | cut -d' ' -f1)
        local date=$(git show -s --format=%cr "$hash" 2>/dev/null || echo "unknown")

        echo "- $date:"
        echo "  https://github.com/a-kamari/gemini-cli-docs/commit/$hash"

        local changed_docs=$(git diff-tree --no-commit-id --name-only -r "$hash" -- docs/*.md 2>/dev/null | sed 's|docs/||' | sed 's|\.md$||' | head -5)
        if [[ -n "$changed_docs" ]]; then
            echo "$changed_docs" | while read -r doc; do
                [[ -n "$doc" ]] && echo "    $doc"
            done
        fi
        echo ""
        ((count++))
    done < <(git log --oneline -10 -- docs/*.md 2>/dev/null | grep -v "Merge" || true)

    if [[ $count -eq 0 ]]; then
        echo "No recent documentation updates found."
        echo ""
    fi

    echo "Full changelog: https://github.com/a-kamari/gemini-cli-docs/commits/main/docs"
    echo "COMMUNITY MIRROR - NOT AFFILIATED WITH GOOGLE"

    set -e
    return 0
}

# Function for uninstall
uninstall() {
    print_doc_header
    echo "To uninstall Gemini CLI Documentation Mirror"
    echo "============================================="
    echo ""

    echo "This will remove:"
    echo "  - The /gdocs command from ~/.claude/commands/gdocs.md"
    echo "  - The /gdocs command from ~/.gemini/commands/gdocs.md (if exists)"
    echo "  - The installation directory ~/.gemini-cli-docs"
    echo ""

    echo "Run this command in your terminal:"
    echo ""
    echo "  ~/.gemini-cli-docs/uninstall.sh"
    echo ""
}

# Store original arguments for flag checking
FULL_ARGS="$*"

# Check if arguments start with -t flag
if [[ "$FULL_ARGS" =~ ^-t([[:space:]]+(.*))?$ ]]; then
    show_freshness
    remaining_args="${BASH_REMATCH[2]}"
    if [[ "$remaining_args" =~ ^what.?s?[[:space:]]?new.*$ ]]; then
        echo ""
        whats_new
    elif [[ -n "$remaining_args" ]]; then
        echo ""
        read_doc "$(sanitize_input "$remaining_args")"
    fi
    exit 0
fi

# Main command handling
case "${1:-}" in
    -t|--check)
        show_freshness
        shift
        remaining_args="$*"
        if [[ "$remaining_args" =~ ^what.?s?[[:space:]]?new.*$ ]]; then
            echo ""
            whats_new
        elif [[ -n "$remaining_args" ]]; then
            echo ""
            read_doc "$(sanitize_input "$remaining_args")"
        fi
        ;;
    hook-check)
        hook_check
        ;;
    uninstall)
        uninstall
        ;;
    search)
        shift
        search_docs "$*"
        ;;
    whats-new|whats|what)
        shift
        remaining="$*"
        if [[ "$remaining" =~ new ]] || [[ "$FULL_ARGS" =~ what.*new ]]; then
            whats_new
        else
            read_doc "$(sanitize_input "$1")"
        fi
        ;;
    "")
        list_docs
        ;;
    *)
        if [[ "$FULL_ARGS" =~ what.*new ]]; then
            whats_new
        else
            read_doc "$(sanitize_input "$1")"
        fi
        ;;
esac

exit 0
