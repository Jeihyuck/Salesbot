import sys

sys.path.append("/www/alpha/")

from apps.rubicon_v3.__function.definitions.generate_constant import (
    generate_channels,
    generate_site_cds,
    generate_ner_fields,
    generate_intelligences,
    generate_sub_intelligences,
)


def generate_constants():
    """
    Generate constants for channels and NER fields.
    """
    # Generate channels
    generate_channels.generate()

    # Generate site codes
    generate_site_cds.generate()

    # Generate NER fields
    generate_ner_fields.generate()

    # Generate intelligences
    generate_intelligences.generate()

    # Generate sub-intelligences
    generate_sub_intelligences.generate()


if __name__ == "__main__":
    generate_constants()
