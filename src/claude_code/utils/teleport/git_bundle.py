"""
Git bundle utilities for teleporting code to remote sessions.

Migrated from: utils/teleport/gitBundle.ts
"""

import asyncio
import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


async def create_git_bundle(
    repo_path: str,
    output_path: str | None = None,
    ref: str = "HEAD",
) -> str | None:
    """Create a git bundle from a repository.

    A git bundle is a portable archive of a git repository that can
    be used to transfer commits without network access.

    Args:
        repo_path: Path to the git repository
        output_path: Where to save the bundle (auto-generated if not specified)
        ref: Git ref to bundle (default: HEAD)

    Returns:
        Path to the created bundle, or None if failed
    """
    if not os.path.isdir(repo_path):
        logger.error(f"Repository path does not exist: {repo_path}")
        return None

    # Check if it's a git repository
    git_dir = Path(repo_path) / ".git"
    if not git_dir.exists():
        logger.error(f"Not a git repository: {repo_path}")
        return None

    # Generate output path if not specified
    if not output_path:
        output_path = os.path.join(tempfile.gettempdir(), f"claude-bundle-{os.getpid()}.bundle")

    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "bundle",
            "create",
            output_path,
            ref,
            cwd=repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.error(f"Git bundle failed: {stderr.decode()}")
            return None

        if os.path.exists(output_path):
            logger.info(f"Created git bundle: {output_path}")
            return output_path

        return None

    except Exception as e:
        logger.error(f"Failed to create git bundle: {e}")
        return None


async def extract_git_bundle(
    bundle_path: str,
    target_path: str,
    branch: str = "main",
) -> bool:
    """Extract a git bundle into a directory.

    Args:
        bundle_path: Path to the git bundle
        target_path: Directory to extract into
        branch: Branch to checkout after extraction

    Returns:
        True if successful, False otherwise
    """
    if not os.path.isfile(bundle_path):
        logger.error(f"Bundle file does not exist: {bundle_path}")
        return False

    try:
        # Create target directory
        os.makedirs(target_path, exist_ok=True)

        # Initialize git repo
        proc = await asyncio.create_subprocess_exec(
            "git",
            "init",
            cwd=target_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()

        if proc.returncode != 0:
            logger.error("Failed to initialize git repository")
            return False

        # Fetch from bundle
        proc = await asyncio.create_subprocess_exec(
            "git",
            "fetch",
            bundle_path,
            f"{branch}:{branch}",
            cwd=target_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.error(f"Failed to fetch from bundle: {stderr.decode()}")
            return False

        # Checkout branch
        proc = await asyncio.create_subprocess_exec(
            "git",
            "checkout",
            branch,
            cwd=target_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()

        if proc.returncode != 0:
            logger.error("Failed to checkout branch")
            return False

        logger.info(f"Extracted git bundle to: {target_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to extract git bundle: {e}")
        return False


def get_bundle_info(bundle_path: str) -> dict | None:
    """Get information about a git bundle.

    Args:
        bundle_path: Path to the git bundle

    Returns:
        Dict with bundle info, or None if failed
    """
    if not os.path.isfile(bundle_path):
        return None

    try:
        import subprocess

        result = subprocess.run(
            ["git", "bundle", "list-heads", bundle_path],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return None

        heads = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split()
                if len(parts) >= 2:
                    heads.append({"sha": parts[0], "ref": parts[1]})

        return {
            "path": bundle_path,
            "size": os.path.getsize(bundle_path),
            "heads": heads,
        }

    except Exception as e:
        logger.error(f"Failed to get bundle info: {e}")
        return None
