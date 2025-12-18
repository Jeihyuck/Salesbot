#!/usr/bin/env python
"""
Environment-aware intelligence constants generator script with consistent interface.

Generates an intelligences.py file that works the same way in all environments:
- Always import with: from apps.rubicon_v3.__function.definitions import intelligences
- Always access constants with: intelligences.SOME_INTELLIGENCE

Usage:
  python generate_intelligences.py [--force]
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
logger = logging.getLogger("intelligences_generator")

from apps.rubicon_v3.models import Intelligence_V2
from alpha.settings import VITE_OP_TYPE


def generate(
    force=False,
    base_dir=os.path.join("apps", "rubicon_v3", "__function", "definitions"),
):
    """
    Generate the intelligences.py file based on environment.

    Args:
        force (bool): If True, regenerate the file even if no changes detected
        base_dir (str): Directory path where the intelligences.py file should be generated

    Returns:
        bool: True if a new file was generated, False if no changes were needed
    """
    try:
        # Get all intelligence values from the database
        intel_values = Intelligence_V2.objects.values_list(
            "intelligence", flat=True
        ).distinct()
        intel_values = sorted(filter(None, intel_values))  # Sort for consistent hashing

        # Calculate hash based ONLY on the actual intelligence data
        intel_data = "|".join(intel_values)
        content_hash = hashlib.md5(intel_data.encode()).hexdigest()[:8]

        # Define paths
        intelligences_path = os.path.join(base_dir, "intelligences.py")

        # Generate file content based on environment - WITH timestamp
        # (timestamp won't affect our hash comparison)
        logger.info(
            f"{VITE_OP_TYPE} environment detected - generating static constants for IDE support"
        )
        file_content = _generate_static_constants(intel_values)

        # Store hash in the file for future reference
        file_content += f"\n# Hash: {content_hash} (intelligences data fingerprint)"

        # Check if current file exists and has the same intelligence data hash AND environment
        needs_update = True
        if os.path.exists(intelligences_path) and not force:
            with open(intelligences_path, "r") as f:
                current_content = f.read()

            # Look for the hash in the current file
            import re

            hash_match = re.search(
                r"# Hash: ([a-f0-9]{8}) \(intelligences data fingerprint\)",
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
                    f"Intelligence data and environment ({VITE_OP_TYPE}) haven't changed (hash: {content_hash}). No update needed."
                )
                needs_update = False

        if not needs_update:
            return False

        # Write the new file
        # First, create a backup if the file exists
        if os.path.exists(intelligences_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            intelligences_backup_path = os.path.join(
                os.path.dirname(intelligences_path), "backups", "intelligences"
            )
            os.makedirs(intelligences_backup_path, exist_ok=True)
            # Create a backup with a timestamp
            backup_path = os.path.join(
                intelligences_backup_path, f"intelligences_{timestamp}.py.bak"
            )
            try:
                with open(intelligences_path, "r") as src, open(
                    backup_path, "w"
                ) as dst:
                    dst.write(src.read())
                logger.info(f"Created backup at {backup_path}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")

        # Write the new file
        os.makedirs(os.path.dirname(intelligences_path), exist_ok=True)
        with open(intelligences_path, "w") as f:
            f.write(file_content)

        logger.info(
            f"Generated intelligences.py ({VITE_OP_TYPE} mode, hash: {content_hash})"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to generate intelligences.py: {e}", exc_info=True)
        return False


def _generate_static_constants(intel_values):
    """
    Generate a simple file with direct intelligence constants for DEV environment.

    Args:
        intel_values (list): List of intelligence values

    Returns:
        str: The file content with direct constants
    """
    # Generate header
    lines = [
        "# Auto-generated intelligences.py file (DEV environment - static constants)",
        f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "# Do not modify this file directly - it will be overwritten",
        "",
        '"""',
        "Intelligence constants loaded from the database.",
        "Usage:",
        "    from apps.rubicon_v3.__function.definitions import intelligences",
        "    print(intelligences.SOME_INTELLIGENCE)",
        '"""',
        "",
    ]

    # Add direct constants for each intelligence value
    for value in intel_values:
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

    parser = argparse.ArgumentParser(description="Generate intelligences.py file")
    parser.add_argument(
        "--force", action="store_true", help="Force regeneration even if no changes"
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=os.path.join("apps", "rubicon_v3", "__function", "definitions"),
        help="Directory where intelligences.py should be generated",
    )
    args = parser.parse_args()

    # Generate the file
    success = generate(force=args.force, base_dir=args.dir)

    # Exit with appropriate code
    sys.exit(0 if success else 1)
