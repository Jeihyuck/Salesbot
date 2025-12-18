import random
import time

from typing import Generator


def stream_markdown(
    markdown: str,
    chunk_size: int = 10,
    min_delay: float = 0.01,
    max_delay: float = 0.05,
) -> Generator[str, None, None]:
    """Simple streaming - just break at spaces when possible."""

    position = 0
    while position < len(markdown):
        # Calculate chunk end
        chunk_end = min(position + chunk_size, len(markdown))

        # Try to break at a space if we're not at the end
        if chunk_end < len(markdown):
            # Look for the last space in the chunk
            space_pos = markdown.rfind(" ", position, chunk_end)
            if space_pos > position:  # Found a space
                chunk_end = space_pos + 1  # Include the space

        # Extract and yield chunk
        chunk = markdown[position:chunk_end]
        position = chunk_end

        # Random delay
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

        yield chunk
