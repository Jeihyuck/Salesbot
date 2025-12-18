#!/usr/bin/env python
"""
Environment-aware sub_intelligence constants generator script with consistent interface.

Generates a sub_intelligences.py file that works the same way in all environments:
- Always import with: from apps.rubicon_v3.__function.definitions import sub_intelligences
- Always access constants with: sub_intelligences.SOME_SUB_INTELLIGENCE

Usage:
  python generate_sub_intelligences.py [--force]
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
logger = logging.getLogger("sub_intelligences_generator")

from apps.rubicon_v3.models import Intelligence_V2
from alpha.settings import VITE_OP_TYPE


def generate(
    force=False,
    base_dir=os.path.join("apps", "rubicon_v3", "__function", "definitions"),
):
    """
    Generate the sub_intelligences.py file based on environment.

    Args:
        force (bool): If True, regenerate the file even if no changes detected
        base_dir (str): Directory path where the sub_intelligences.py file should be generated

    Returns:
        bool: True if a new file was generated, False if no changes were needed
    """
    try:
        # Get all sub_intelligence values from the database
        sub_intel_values = Intelligence_V2.objects.values_list(
            "sub_intelligence", flat=True
        ).distinct()
        sub_intel_values = sorted(
            filter(None, sub_intel_values)
        )  # Sort for consistent hashing

        # Calculate hash based ONLY on the actual sub_intelligence data
        sub_intel_data = "|".join(sub_intel_values)
        content_hash = hashlib.md5(sub_intel_data.encode()).hexdigest()[:8]

        # Define paths
        sub_intelligences_path = os.path.join(base_dir, "sub_intelligences.py")

        # Generate file content based on environment - WITH timestamp
        # (timestamp won't affect our hash comparison)
        logger.info(
            f"{VITE_OP_TYPE} environment detected - generating static constants for IDE support"
        )
        file_content = _generate_static_constants(sub_intel_values)

        # Store hash in the file for future reference
        file_content += f"\n# Hash: {content_hash} (sub_intelligences data fingerprint)"

        # Check if current file exists and has the same sub_intelligence data hash AND environment
        needs_update = True
        if os.path.exists(sub_intelligences_path) and not force:
            with open(sub_intelligences_path, "r") as f:
                current_content = f.read()

            # Look for the hash in the current file
            import re

            hash_match = re.search(
                r"# Hash: ([a-f0-9]{8}) \(sub_intelligences data fingerprint\)",
                current_content,
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
                    f"Sub_Intelligence data and environment ({VITE_OP_TYPE}) haven't changed (hash: {content_hash}). No update needed."
                )
                needs_update = False

        if not needs_update:
            return False

        # Write the new file
        # First, create a backup if the file exists
        if os.path.exists(sub_intelligences_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sub_intelligences_backup_path = os.path.join(
                os.path.dirname(sub_intelligences_path), "backups", "sub_intelligences"
            )
            os.makedirs(sub_intelligences_backup_path, exist_ok=True)
            # Create a backup with a timestamp
            backup_path = os.path.join(
                sub_intelligences_backup_path, f"sub_intelligences_{timestamp}.py.bak"
            )
            try:
                with open(sub_intelligences_path, "r") as src, open(
                    backup_path, "w"
                ) as dst:
                    dst.write(src.read())
                logger.info(f"Created backup at {backup_path}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")

        # Write the new file
        os.makedirs(os.path.dirname(sub_intelligences_path), exist_ok=True)
        with open(sub_intelligences_path, "w") as f:
            f.write(file_content)

        logger.info(
            f"Generated sub_intelligences.py ({VITE_OP_TYPE} mode, hash: {content_hash})"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to generate sub_intelligences.py: {e}", exc_info=True)
        return False


def _generate_static_constants(sub_intel_values):
    """
    Generate a simple file with direct sub_intelligence constants for DEV environment.

    Args:
        sub_intel_values (list): List of sub_intelligence values

    Returns:
        str: The file content with direct constants
    """
    # Generate header
    lines = [
        "# Auto-generated sub_intelligences.py file (DEV environment - static constants)",
        f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "# Do not modify this file directly - it will be overwritten",
        "",
        '"""',
        "Sub_Intelligence constants loaded from the database.",
        "Usage:",
        "    from apps.rubicon_v3.__function.definitions import sub_intelligences",
        "    print(sub_intelligences.SOME_SUB_INTELLIGENCE)",
        '"""',
        "",
    ]

    # Add direct constants for each sub_intelligence value
    for value in sub_intel_values:
        if value:
            # Create a valid Python identifier (uppercase with underscores)
            # Replace special characters before slugify
            processed_value = value.replace("/", "_").replace("-", "_")
            constant_name = slugify(processed_value).replace("-", "_").upper()
            lines.append(f"{constant_name} = '{value}'")

    return "\n".join(lines)


# Allow running as a script
if __name__ == "__main__":
    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="Generate sub_intelligences.py file")
    parser.add_argument(
        "--force", action="store_true", help="Force regeneration even if no changes"
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=os.path.join("apps", "rubicon_v3", "__function", "definitions"),
        help="Directory where sub_intelligences.py should be generated",
    )
    args = parser.parse_args()

    # Generate the file
    success = generate(force=args.force, base_dir=args.dir)

    # Exit with appropriate code
    sys.exit(0 if success else 1)
