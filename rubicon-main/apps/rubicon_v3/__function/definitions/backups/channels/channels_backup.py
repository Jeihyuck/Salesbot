import sys

sys.path.append("/www/alpha/")

from django.utils.text import slugify

from apps.rubicon_v3.models import Channel


class Channels:
    """Channel constants loaded dynamically from the Channel model."""

    _initialized = False

    @classmethod
    def initialize(cls):
        """Initialize channel constants from the database."""
        if cls._initialized:
            return

        try:
            # Get all distinct channel names from the database
            channels = Channel.objects.values_list("channel", flat=True).distinct()

            # Create constants for each channel
            for channel in channels:
                if channel:
                    # Create a valid Python identifier (uppercase with underscores)
                    constant_name = slugify(channel).replace("-", "_").upper()
                    # Set the constant value on the class
                    setattr(cls, constant_name, channel)

            cls._initialized = True
        except Exception as e:
            import logging

            logging.error(f"Failed to initialize channel constants: {e}")

    @classmethod
    def refresh(cls):
        """Refresh channel constants from the database."""
        import logging

        try:
            # Clear existing dynamic attributes first
            if cls._initialized:
                # Get current attributes that were added dynamically
                channels = Channel.objects.values_list("channel", flat=True).distinct()
                for channel in channels:
                    if channel:
                        constant_name = slugify(channel).replace("-", "_").upper()
                        if hasattr(cls, constant_name):
                            delattr(cls, constant_name)

            # Reset initialization flag
            cls._initialized = False

            # Re-initialize
            cls.initialize()
            logging.info("Channel constants have been refreshed successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to refresh channel constants: {e}")
            return False


# Initialize the constants when the module is loaded
Channels.initialize()


# Add a __getattr__ method to handle attribute access before Django is fully loaded
def __getattr__(name):
    """Handle attribute access before Django is ready."""
    Channels.initialize()
    if hasattr(Channels, name):
        return getattr(Channels, name)
    raise AttributeError(f"'{Channels.__name__}' has no attribute '{name}'")
