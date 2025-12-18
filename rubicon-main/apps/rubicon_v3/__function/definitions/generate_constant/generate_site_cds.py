#!/usr/bin/env python
"""
Environment-aware site_cd constants generator script with consistent interface.

Generates a site_cds.py file that works the same way in all environments:
- Always import with: from apps.rubicon_v3.__function.definitions import site_cds
- Always access constants with: site_cds.SOME_SITE_CD

Usage:
  python generate_site_cds.py [--force]
"""
import sys

sys.path.append("/www/alpha/")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from django.utils.text import slugify

import hashlib
import logging

from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("site_cds_generator")

from apps.rubicon_v3.models import Channel
from alpha.settings import VITE_OP_TYPE


def generate(
    force=False,
    base_dir=os.path.join("apps", "rubicon_v3", "__function", "definitions"),
):
    """
    Generate the site_cds.py file based on environment.

    Args:
        force (bool): If True, regenerate the file even if no changes detected
        base_dir (str): Directory path where the site_cds.py file should be generated

    Returns:
        bool: True if a new file was generated, False if no changes were needed
    """
    try:
        # Get all site_cd values from the database
        site_cds = Channel.objects.values_list("site_cd", flat=True).distinct()
        site_cds = sorted(filter(None, site_cds))  # Sort for consistent hashing

        # Calculate hash based ONLY on the actual site_cds data
        site_cds_data = "|".join(site_cds)
        content_hash = hashlib.md5(site_cds_data.encode()).hexdigest()[:8]

        # Define paths
        site_cds_path = os.path.join(base_dir, "site_cds.py")

        # Generate file content based on environment - WITH timestamp
        # (timestamp won't affect our hash comparison)
        logger.info(
            f"{VITE_OP_TYPE} environment detected - generating static constants for IDE support"
        )
        file_content = _generate_static_constants(site_cds)

        # Store hash in the file for future reference
        file_content += f"\n# Hash: {content_hash} (site_cd data fingerprint)"

        # Check if current file exists and has the same site_cd data hash AND environment
        needs_update = True
        if os.path.exists(site_cds_path) and not force:
            with open(site_cds_path, "r") as f:
                current_content = f.read()

            # Look for the hash in the current file
            import re

            hash_match = re.search(
                r"# Hash: ([a-f0-9]{8}) \(site_cd data fingerprint\)", current_content
            )

            # Look for the environment type in the current file
            env_match = re.search(r"\(([A-Z]+) environment", current_content)

            if (
                hash_match
                and hash_match.group(1) == content_hash
                and env_match
                and env_match.group(1) == VITE_OP_TYPE
            ):
                logger.info(
                    f"Site code data and environment ({VITE_OP_TYPE}) haven't changed (hash: {content_hash}). No update needed."
                )
                needs_update = False

        if not needs_update:
            return False

        # Write the new file
        # First, create a backup if the file exists
        if os.path.exists(site_cds_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            site_cds_backup_path = os.path.join(
                os.path.dirname(site_cds_path), "backups", "site_cds"
            )
            os.makedirs(site_cds_backup_path, exist_ok=True)
            # Create a backup with a timestamp
            backup_path = os.path.join(
                site_cds_backup_path, f"site_cds_{timestamp}.py.bak"
            )
            try:
                with open(site_cds_path, "r") as src, open(backup_path, "w") as dst:
                    dst.write(src.read())
                logger.info(f"Created backup at {backup_path}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")

        # Write the new file
        os.makedirs(os.path.dirname(site_cds_path), exist_ok=True)
        with open(site_cds_path, "w") as f:
            f.write(file_content)

        logger.info(
            f"Generated site_cds.py ({VITE_OP_TYPE} mode, hash: {content_hash})"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to generate site_cds.py: {e}", exc_info=True)
        return False


def _generate_static_constants(site_cds):
    """
    Generate a simple file with direct site_cd constants for DEV environment.

    Args:
        site_cds (list): List of site_cd values to include as constants

    Returns:
        str: The file content with direct constants
    """
    # Generate header
    lines = [
        "# Auto-generated site_cds.py file (DEV environment - static constants)",
        f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "# Do not modify this file directly - it will be overwritten",
        "",
        '"""',
        "Site code constants loaded from the database.",
        "Usage:",
        "    from apps.rubicon_v3.__function.definitions import site_cds",
        "    print(site_cds.SOME_SITE_CD)",
        '"""',
        "",
    ]

    # Add direct constants for each site_cd
    for site_cd in site_cds:
        if site_cd:
            # Create a valid Python identifier (uppercase with underscores)
            constant_name = slugify(site_cd).replace("-", "_").upper()
            lines.append(f"{constant_name} = '{site_cd}'")

    return "\n".join(lines)


# Allow running as a script
if __name__ == "__main__":
    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="Generate site_cds.py file")
    parser.add_argument(
        "--force", action="store_true", help="Force regeneration even if no changes"
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=os.path.join("apps", "rubicon_v3", "__function", "definitions"),
        help="Directory where site_cds.py should be generated",
    )
    args = parser.parse_args()

    # Generate the file
    success = generate(force=args.force, base_dir=args.dir)

    # Exit with appropriate code
    sys.exit(0 if success else 1)
