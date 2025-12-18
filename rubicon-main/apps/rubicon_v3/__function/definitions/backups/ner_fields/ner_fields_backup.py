import sys

sys.path.append("/www/alpha/")

from django.utils.text import slugify

from apps.rubicon_v3.models import Ner_Expression_Field


class NerFields:
    """Channel constants loaded dynamically from the Ner_Expression_Field model."""

    _initialized = False

    @classmethod
    def initialize(cls):
        """Initialize channel constants from the database."""
        if cls._initialized:
            return

        try:
            # Get all distinct channel names from the database
            ner_field_names = Ner_Expression_Field.objects.values_list(
                "field_name", flat=True
            ).distinct()

            # Create constants for each channel
            for ner_field_name in ner_field_names:
                if ner_field_name:
                    # Create a valid Python identifier (uppercase with underscores)
                    constant_name = slugify(ner_field_name).upper()
                    # Set the constant value on the class
                    setattr(cls, constant_name, ner_field_name)

            cls._initialized = True
        except Exception as e:
            import logging

            logging.error(f"Failed to initialize ner field name constants: {e}")

    @classmethod
    def refresh(cls):
        """Refresh ner field name constants from the database."""
        import logging

        try:
            # Clear existing dynamic attributes first
            if cls._initialized:
                # Get current attributes that were added dynamically
                ner_field_names = Ner_Expression_Field.objects.values_list(
                    "field_name", flat=True
                ).distinct()
                for ner_field_name in ner_field_names:
                    if ner_field_name:
                        constant_name = slugify(ner_field_name).upper()
                        if hasattr(cls, constant_name):
                            delattr(cls, constant_name)

            # Reset initialization flag
            cls._initialized = False

            # Re-initialize
            cls.initialize()
            logging.info("Ner field name constants have been refreshed successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to refresh ner field name constants: {e}")
            return False


# Initialize the constants when the module is loaded
NerFields.initialize()


# Add a __getattr__ method to handle attribute access before Django is fully loaded
def __getattr__(name):
    """Handle attribute access before Django is ready."""
    NerFields.initialize()
    if hasattr(NerFields, name):
        return getattr(NerFields, name)
    raise AttributeError(f"'{NerFields.__name__}' has no attribute '{name}'")
