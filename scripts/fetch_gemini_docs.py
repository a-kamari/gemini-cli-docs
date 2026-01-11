#!/usr/bin/env python3
"""
Gemini CLI documentation fetcher.
Fetches documentation from the google-gemini/gemini-cli GitHub repository.
"""

import requests
import time
from pathlib import Path
from typing import List, Tuple, Set, Optional, Dict
import logging
from datetime import datetime
import sys
import json
import hashlib
import os
import re
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# GitHub API configuration
GITHUB_API_BASE = "https://api.github.com/repos/google-gemini/gemini-cli"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/google-gemini/gemini-cli/main"
MANIFEST_FILE = "docs_manifest.json"

# Headers for GitHub API
HEADERS = {
    'User-Agent': 'Gemini-CLI-Docs-Fetcher/1.0',
    'Accept': 'application/vnd.github.v3+json',
}

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2
MAX_RETRY_DELAY = 30
RATE_LIMIT_DELAY = 0.3


def get_github_headers() -> dict:
    """Get headers with optional GitHub token for higher rate limits."""
    headers = HEADERS.copy()
    github_token = os.environ.get('GITHUB_TOKEN')
    if github_token:
        headers['Authorization'] = f'token {github_token}'
        logger.info("Using GitHub token for authentication")
    return headers


def load_manifest(docs_dir: Path) -> dict:
    """Load the manifest of previously fetched files."""
    manifest_path = docs_dir / MANIFEST_FILE
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
            if "files" not in manifest:
                manifest["files"] = {}
            return manifest
        except Exception as e:
            logger.warning(f"Failed to load manifest: {e}")
    return {"files": {}, "last_updated": None}


def save_manifest(docs_dir: Path, manifest: dict) -> None:
    """Save the manifest of fetched files."""
    manifest_path = docs_dir / MANIFEST_FILE
    manifest["last_updated"] = datetime.now().isoformat()

    # Get GitHub repository from environment or use default
    github_repo = os.environ.get('GITHUB_REPOSITORY', 'YOUR_USERNAME/gemini-cli-docs')
    github_ref = os.environ.get('GITHUB_REF_NAME', 'main')

    # Validate repository name format
    if not re.match(r'^[\w.-]+/[\w.-]+$', github_repo):
        logger.warning(f"Invalid repository format: {github_repo}")
        github_repo = 'YOUR_USERNAME/gemini-cli-docs'

    manifest["base_url"] = f"https://raw.githubusercontent.com/{github_repo}/{github_ref}/docs/"
    manifest["github_repository"] = github_repo
    manifest["github_ref"] = github_ref
    manifest["source_repository"] = "google-gemini/gemini-cli"
    manifest["description"] = "Gemini CLI documentation manifest. Community mirror - not affiliated with Google."
    manifest_path.write_text(json.dumps(manifest, indent=2))


def path_to_safe_filename(file_path: str) -> str:
    """
    Convert a file path to a safe filename.
    Example: docs/cli/commands.md -> cli__commands.md
    """
    # Remove 'docs/' prefix if present
    if file_path.startswith('docs/'):
        file_path = file_path[5:]

    # Remove .md extension for processing
    if file_path.endswith('.md'):
        file_path = file_path[:-3]

    # Replace directory separators with double underscores
    safe_name = file_path.replace('/', '__')

    # Add .md extension back
    return safe_name + '.md'


def discover_docs_from_github(session: requests.Session, headers: dict) -> List[str]:
    """
    Discover all documentation files from the GitHub repository tree.
    Returns list of file paths like: docs/cli/commands.md
    """
    logger.info("Discovering documentation files from GitHub...")

    tree_url = f"{GITHUB_API_BASE}/git/trees/main?recursive=1"

    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(tree_url, headers=headers, timeout=30)

            if response.status_code == 403:
                # Rate limited
                reset_time = response.headers.get('X-RateLimit-Reset')
                if reset_time:
                    wait_time = int(reset_time) - int(time.time()) + 1
                    logger.warning(f"Rate limited. Resets in {wait_time}s")
                    if wait_time > 0 and wait_time < 300:
                        time.sleep(wait_time)
                        continue
                raise Exception("GitHub API rate limit exceeded")

            response.raise_for_status()
            data = response.json()

            docs_files = []
            for item in data.get('tree', []):
                path = item.get('path', '')
                item_type = item.get('type', '')

                # Only include markdown files in docs/ directory
                if (item_type == 'blob' and
                    path.startswith('docs/') and
                    path.endswith('.md')):
                    docs_files.append(path)

            logger.info(f"Discovered {len(docs_files)} documentation files")
            return sorted(docs_files)

        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                delay = min(RETRY_DELAY * (2 ** attempt), MAX_RETRY_DELAY)
                time.sleep(delay * random.uniform(0.5, 1.0))
            else:
                raise Exception(f"Failed to discover docs after {MAX_RETRIES} attempts: {e}")

    return []


def validate_markdown_content(content: str, filename: str) -> None:
    """Validate that content is proper markdown."""
    # Check for HTML content (indicates fetch failure)
    if not content or content.startswith('<!DOCTYPE') or '<html' in content[:100]:
        raise ValueError("Received HTML instead of markdown")

    # Check minimum length
    if len(content.strip()) < 50:
        raise ValueError(f"Content too short ({len(content)} bytes)")

    # Check for markdown indicators
    markdown_patterns = ['# ', '## ', '### ', '```', '- ', '* ', '1. ', '[', '**', '_', '> ']
    indicator_count = sum(1 for line in content.split('\n')[:50]
                         for p in markdown_patterns if p in line)

    if indicator_count < 2:
        raise ValueError(f"Content doesn't appear to be markdown (only {indicator_count} indicators)")


def fetch_markdown_content(file_path: str, session: requests.Session, headers: dict) -> Tuple[str, str]:
    """
    Fetch markdown content from GitHub.
    Returns tuple of (safe_filename, content).
    """
    raw_url = f"{GITHUB_RAW_BASE}/{file_path}"
    filename = path_to_safe_filename(file_path)

    logger.info(f"Fetching: {file_path} -> {filename}")

    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(raw_url, headers=headers, timeout=30)

            if response.status_code == 429:
                wait_time = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            content = response.text
            validate_markdown_content(content, filename)

            logger.info(f"Successfully fetched {filename} ({len(content)} bytes)")
            return filename, content

        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed for {filename}: {e}")
            if attempt < MAX_RETRIES - 1:
                delay = min(RETRY_DELAY * (2 ** attempt), MAX_RETRY_DELAY)
                time.sleep(delay * random.uniform(0.5, 1.0))
            else:
                raise Exception(f"Failed to fetch {filename} after {MAX_RETRIES} attempts: {e}")

        except ValueError as e:
            logger.error(f"Content validation failed for {filename}: {e}")
            raise

    raise Exception(f"Failed to fetch {filename}")


def fetch_changelog(session: requests.Session, headers: dict) -> Optional[Tuple[str, str]]:
    """
    Fetch CHANGELOG.md from the Gemini CLI repository.
    Returns tuple of (filename, content) or None if not found.
    """
    changelog_url = f"{GITHUB_RAW_BASE}/CHANGELOG.md"
    filename = "changelog.md"

    logger.info(f"Fetching changelog: {changelog_url}")

    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(changelog_url, headers=headers, timeout=30)

            if response.status_code == 404:
                logger.info("No CHANGELOG.md found in repository")
                return None

            if response.status_code == 429:
                wait_time = int(response.headers.get('Retry-After', 60))
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            content = response.text

            # Add header
            header = """# Gemini CLI Changelog

> **Source**: https://github.com/google-gemini/gemini-cli/blob/main/CHANGELOG.md
>
> This is the official Gemini CLI changelog, automatically fetched from the repository.

---

"""
            content = header + content

            if len(content.strip()) < 100:
                logger.warning("Changelog content too short")
                return None

            logger.info(f"Successfully fetched changelog ({len(content)} bytes)")
            return filename, content

        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed for changelog: {e}")
            if attempt < MAX_RETRIES - 1:
                delay = min(RETRY_DELAY * (2 ** attempt), MAX_RETRY_DELAY)
                time.sleep(delay * random.uniform(0.5, 1.0))
            else:
                logger.warning(f"Failed to fetch changelog: {e}")
                return None

    return None


def content_has_changed(content: str, old_hash: str) -> bool:
    """Check if content has changed based on hash."""
    new_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    return new_hash != old_hash


def save_markdown_file(docs_dir: Path, filename: str, content: str) -> str:
    """Save markdown content and return its hash."""
    file_path = docs_dir / filename

    try:
        file_path.write_text(content, encoding='utf-8')
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        logger.info(f"Saved: {filename}")
        return content_hash
    except Exception as e:
        logger.error(f"Failed to save {filename}: {e}")
        raise


def cleanup_old_files(docs_dir: Path, current_files: Set[str], manifest: dict) -> None:
    """Remove files that were previously fetched but no longer exist."""
    previous_files = set(manifest.get("files", {}).keys())
    files_to_remove = previous_files - current_files

    for filename in files_to_remove:
        if filename == MANIFEST_FILE:
            continue

        file_path = docs_dir / filename
        if file_path.exists():
            logger.info(f"Removing obsolete file: {filename}")
            file_path.unlink()


def main():
    """Main function."""
    start_time = datetime.now()
    logger.info("Starting Gemini CLI documentation fetch")

    # Get GitHub repository info
    github_repo = os.environ.get('GITHUB_REPOSITORY', 'YOUR_USERNAME/gemini-cli-docs')
    logger.info(f"Target repository: {github_repo}")

    # Create docs directory
    docs_dir = Path(__file__).parent.parent / 'docs'
    docs_dir.mkdir(exist_ok=True)
    logger.info(f"Output directory: {docs_dir}")

    # Load existing manifest
    manifest = load_manifest(docs_dir)

    # Statistics
    successful = 0
    failed = 0
    failed_pages = []
    fetched_files: Set[str] = set()
    new_manifest: Dict = {"files": {}}

    # Get headers with optional token
    headers = get_github_headers()

    with requests.Session() as session:
        # Discover documentation files
        try:
            doc_files = discover_docs_from_github(session, headers)
        except Exception as e:
            logger.error(f"Failed to discover docs: {e}")
            sys.exit(1)

        if not doc_files:
            logger.error("No documentation files discovered!")
            sys.exit(1)

        # Fetch each documentation file
        for i, file_path in enumerate(doc_files, 1):
            logger.info(f"Processing {i}/{len(doc_files)}: {file_path}")

            try:
                filename, content = fetch_markdown_content(file_path, session, headers)

                # Check if content changed
                old_hash = manifest.get("files", {}).get(filename, {}).get("hash", "")
                old_entry = manifest.get("files", {}).get(filename, {})

                if content_has_changed(content, old_hash):
                    content_hash = save_markdown_file(docs_dir, filename, content)
                    logger.info(f"Updated: {filename}")
                    last_updated = datetime.now().isoformat()
                else:
                    content_hash = old_hash
                    logger.info(f"Unchanged: {filename}")
                    last_updated = old_entry.get("last_updated", datetime.now().isoformat())

                new_manifest["files"][filename] = {
                    "original_path": file_path,
                    "github_url": f"https://github.com/google-gemini/gemini-cli/blob/main/{file_path}",
                    "hash": content_hash,
                    "last_updated": last_updated
                }

                fetched_files.add(filename)
                successful += 1

                # Rate limiting
                if i < len(doc_files):
                    time.sleep(RATE_LIMIT_DELAY)

            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                failed += 1
                failed_pages.append(file_path)

        # Fetch changelog
        logger.info("Fetching changelog...")
        changelog_result = fetch_changelog(session, headers)
        if changelog_result:
            filename, content = changelog_result

            old_hash = manifest.get("files", {}).get(filename, {}).get("hash", "")
            old_entry = manifest.get("files", {}).get(filename, {})

            if content_has_changed(content, old_hash):
                content_hash = save_markdown_file(docs_dir, filename, content)
                last_updated = datetime.now().isoformat()
            else:
                content_hash = old_hash
                last_updated = old_entry.get("last_updated", datetime.now().isoformat())

            new_manifest["files"][filename] = {
                "original_path": "CHANGELOG.md",
                "github_url": "https://github.com/google-gemini/gemini-cli/blob/main/CHANGELOG.md",
                "hash": content_hash,
                "last_updated": last_updated,
                "source": "gemini-cli-repository"
            }

            fetched_files.add(filename)
            successful += 1

    # Clean up old files
    cleanup_old_files(docs_dir, fetched_files, manifest)

    # Add metadata
    new_manifest["fetch_metadata"] = {
        "last_fetch_completed": datetime.now().isoformat(),
        "fetch_duration_seconds": (datetime.now() - start_time).total_seconds(),
        "total_files_discovered": len(doc_files),
        "files_fetched_successfully": successful,
        "files_failed": failed,
        "failed_files": failed_pages,
        "source_repository": "google-gemini/gemini-cli",
        "total_files": len(fetched_files),
        "fetch_tool_version": "1.0"
    }

    # Save manifest
    save_manifest(docs_dir, new_manifest)

    # Summary
    duration = datetime.now() - start_time
    logger.info("\n" + "=" * 50)
    logger.info(f"Fetch completed in {duration}")
    logger.info(f"Discovered files: {len(doc_files)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")

    if failed_pages:
        logger.warning("\nFailed files (will retry next run):")
        for page in failed_pages:
            logger.warning(f"  - {page}")
        if successful == 0:
            logger.error("No files were fetched successfully!")
            sys.exit(1)
    else:
        logger.info("\nAll files fetched successfully!")


if __name__ == "__main__":
    main()
