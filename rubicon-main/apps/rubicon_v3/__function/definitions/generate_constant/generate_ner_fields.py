#!/usr/bin/env python
"""
Environment-aware NER field constants generator script with consistent interface.

Generates a ner_fields.py file that works the same way in all environments:
- Always import with: from apps.rubicon_v3.__function.definitions import ner_fields
- Always access constants with: ner_fields.SOME_FIELD

Usage:
  python generate_ner_fields.py [--force]
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
logger = logging.getLogger("ner_fields_generator")

from apps.rubicon_v3.models import Ner_Expression_Field
from alpha.settings import VITE_OP_TYPE


def generate(
    force=False,
    base_dir=os.path.join("apps", "rubicon_v3", "__function", "definitions"),
):
    """
    Generate the ner_fields.py file based on environment.

    Args:
        force (bool): If True, regenerate the file even if no changes detected
        base_dir (str): Directory path where the ner_fields.py file should be generated

    Returns:
        bool: True if a new file was generated, False if no changes were needed
    """
    try:
        # Get all NER field names from the database where active is True
        ner_fields = (
            Ner_Expression_Field.objects.filter(active=True)
            .values_list("field_name", flat=True)
            .distinct()
        )
        ner_fields = sorted(filter(None, ner_fields))  # Sort for consistent hashing

        # Calculate hash based ONLY on the actual field data
        ner_fields_data = "|".join(ner_fields)
        content_hash = hashlib.md5(ner_fields_data.encode()).hexdigest()[:8]

        # Define paths
        ner_fields_path = os.path.join(base_dir, "ner_fields.py")

        # Generate file content based on environment - WITH timestamp
        # (timestamp won't affect our hash comparison)
        logger.info(
            f"{VITE_OP_TYPE} environment detected - generating static constants for IDE support"
        )
        file_content = _generate_static_constants(ner_fields)

        # Store hash in the file for future reference
        file_content += f"\n# Hash: {content_hash} (NER field data fingerprint)"

        # Check if current file exists and has the same NER field data hash AND environment
        needs_update = True
        if os.path.exists(ner_fields_path) and not force:
            with open(ner_fields_path, "r") as f:
                current_content = f.read()

            # Look for the hash in the current file
            import re

            hash_match = re.search(
                r"# Hash: ([a-f0-9]{8}) \(NER field data fingerprint\)", current_content
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
                    f"NER field data and environment ({VITE_OP_TYPE}) haven't changed (hash: {content_hash}). No update needed."
                )
                needs_update = False

        if not needs_update:
            return False

        # Write the new file
        # First, create a backup if the file exists
        if os.path.exists(ner_fields_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ner_fields_backup_path = os.path.join(
                os.path.dirname(ner_fields_path), "backups", "ner_fields"
            )
            os.makedirs(ner_fields_backup_path, exist_ok=True)
            # Create a backup with a timestamp
            backup_path = os.path.join(
                ner_fields_backup_path, f"ner_fields_{timestamp}.py.bak"
            )
            try:
                with open(ner_fields_path, "r") as src, open(backup_path, "w") as dst:
                    dst.write(src.read())
                logger.info(f"Created backup at {backup_path}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")

        # Write the new file
        os.makedirs(os.path.dirname(ner_fields_path), exist_ok=True)
        with open(ner_fields_path, "w") as f:
            f.write(file_content)

        logger.info(
            f"Generated ner_fields.py ({VITE_OP_TYPE} mode, hash: {content_hash})"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to generate ner_fields.py: {e}", exc_info=True)
        return False


def _generate_static_constants(ner_fields):
    """
    Generate a simple file with direct NER field constants for DEV environment.

    Args:
        ner_fields (list): List of NER field names

    Returns:
        str: The file content with direct constants
    """
    # Generate header
    lines = [
        "# Auto-generated ner_fields.py file (DEV environment - static constants)",
        f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "# Do not modify this file directly - it will be overwritten",
        "",
        '"""',
        "NER field constants loaded from the database.",
        "Usage:",
        "    from apps.rubicon_v3.__function.definitions import ner_fields",
        "    print(ner_fields.SOME_FIELD)",
        '"""',
        "",
    ]

    # Add direct constants for each NER field
    for field in ner_fields:
        if field:
            # Create a valid Python identifier (uppercase with underscores)
            constant_name = slugify(field).upper()
            lines.append(f"{constant_name} = '{field}'")

    return "\n".join(lines)


# Allow running as a script
if __name__ == "__main__":
    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="Generate ner_fields.py file")
    parser.add_argument(
        "--force", action="store_true", help="Force regeneration even if no changes"
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=os.path.join("apps", "rubicon_v3", "__function", "definitions"),
        help="Directory where ner_fields.py should be generated",
    )
    args = parser.parse_args()

    # Generate the file
    success = generate(force=args.force, base_dir=args.dir)

    # Exit with appropriate code
    sys.exit(0 if success else 1)
