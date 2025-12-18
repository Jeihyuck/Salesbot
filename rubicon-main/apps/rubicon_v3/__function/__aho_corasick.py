import sys

sys.path.append("/www/alpha/")

import logging

from collections import deque
from typing import List, Dict

from apps.rubicon_v3.__function.__django_cache import DjangoCacheClient, CacheKey

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("aho_corasick_automaton")

cache = DjangoCacheClient()


class AhoCorasickAutomaton:
    """
    Aho-Corasick automaton that auto-initializes from Django cache on instantiation.
    """

    def __init__(self, pattern_location: str):
        self.pattern_location = pattern_location

        # Core data structures
        self.trie = [{}]  # List of dictionaries, index is node_id
        self.failure_links = [0]  # Failure link for each node
        self.output = [set()]  # Set of pattern IDs that end at each node
        self.patterns = []  # List of patterns (pattern_id -> pattern string)
        self.node_count = 1  # Number of nodes in trie

        # Auto-initialize from cache
        self._load_and_build()

    def _load_and_build(self):
        """Load patterns from cache and build the automaton."""
        try:
            # Get patterns from Django Redis cache
            patterns_data = cache.get(CacheKey.moderator_prohibited_words_data(), {})

            # Extract patterns from the cached data using the specified location (dot notation)
            keys = self.pattern_location.split(".")
            patterns = patterns_data

            try:
                for key in keys:
                    patterns = patterns[key]
            except KeyError:
                logger.error(
                    f"Key '{self.pattern_location}' not found in cached patterns data"
                )
                return

            if not patterns:
                logger.warning("No moderator patterns found")
                return

            # Build the automaton
            self._build_from_patterns(patterns)
            logger.info(
                f"Initialized AhoCorasickAutomaton with {len(patterns)} patterns"
            )

        except Exception as e:
            logger.error(f"Failed to initialize AhoCorasickAutomaton: {e}")

    def _build_from_patterns(self, patterns: List[str]):
        """Build the automaton from a list of patterns."""
        # Reset to initial state
        self.trie = [{}]
        self.failure_links = [0]
        self.output = [set()]
        self.patterns = []
        self.node_count = 1

        # Add all patterns
        for pattern in patterns:
            if pattern:  # Skip empty patterns
                self._add_pattern(pattern.lower())  # Case-insensitive

        # Build failure links
        self._build_failure_links()

    def _add_pattern(self, pattern: str) -> int:
        """Add a pattern to the automaton."""
        if not pattern:
            return -1

        # Add pattern to trie
        node = 0
        for char in pattern:
            if char not in self.trie[node]:
                # Create new node
                self.trie.append({})
                self.failure_links.append(0)
                self.output.append(set())
                self.trie[node][char] = self.node_count
                self.node_count += 1
            node = self.trie[node][char]

        # Mark end of pattern
        pattern_id = len(self.patterns)
        self.patterns.append(pattern)
        self.output[node].add(pattern_id)

        return pattern_id

    def _build_failure_links(self):
        """Build failure links using BFS."""
        # Initialize queue with all nodes at depth 1
        queue = deque()

        # Set failure links for depth 1 nodes to root
        for char, node in self.trie[0].items():
            self.failure_links[node] = 0
            queue.append(node)

        # BFS to build failure links for remaining nodes
        while queue:
            current = queue.popleft()

            for char, child in self.trie[current].items():
                queue.append(child)

                # Find failure link for child
                failure = self.failure_links[current]

                while failure != 0 and char not in self.trie[failure]:
                    failure = self.failure_links[failure]

                if char in self.trie[failure] and self.trie[failure][char] != child:
                    self.failure_links[child] = self.trie[failure][char]
                else:
                    self.failure_links[child] = 0

                # Merge output from failure link
                failure_node = self.failure_links[child]
                if failure_node != 0:
                    self.output[child] |= self.output[failure_node]

    def find_all_matches(self, text: str) -> List[Dict[str, any]]:
        """
        Find all pattern matches in the text.

        Args:
            text: The text to search in

        Returns:
            List of dictionaries containing:
            - pattern: The matched pattern string (lowercase)
            - start_pos: Starting position of match (0-indexed)
            - end_pos: Ending position of match (exclusive)
            - matched_text: The actual matched text from input (preserves case)
        """
        if not text or not self.patterns:
            return []

        matches = []
        node = 0
        text_lower = text.lower()  # Case-insensitive matching

        for i, char in enumerate(text_lower):
            # Follow failure links until we find a match or reach root
            while node != 0 and char not in self.trie[node]:
                node = self.failure_links[node]

            # Move to next node if edge exists
            if char in self.trie[node]:
                node = self.trie[node][char]

            # Check for matches at current node
            for pattern_id in self.output[node]:
                pattern = self.patterns[pattern_id]
                start_pos = i - len(pattern) + 1
                end_pos = i + 1
                matches.append(
                    {
                        "pattern": pattern,
                        "start_pos": start_pos,
                        "end_pos": end_pos,
                        "matched_text": text[start_pos:end_pos],  # Original case
                    }
                )

            # Also check matches reachable through failure links
            temp_node = self.failure_links[node]
            while temp_node != 0:
                for pattern_id in self.output[temp_node]:
                    pattern = self.patterns[pattern_id]
                    start_pos = i - len(pattern) + 1
                    end_pos = i + 1
                    matches.append(
                        {
                            "pattern": pattern,
                            "start_pos": start_pos,
                            "end_pos": end_pos,
                            "matched_text": text[start_pos:end_pos],  # Original case
                        }
                    )
                temp_node = self.failure_links[temp_node]

        return matches

    def search(self, text: str) -> List[Dict[str, any]]:
        """Alias for find_all_matches for convenience."""
        return self.find_all_matches(text)

    def contains_any(self, text: str) -> bool:
        """Quick check if text contains any pattern."""
        if not text or not self.patterns:
            return False

        node = 0
        text_lower = text.lower()

        for char in text_lower:
            while node != 0 and char not in self.trie[node]:
                node = self.failure_links[node]

            if char in self.trie[node]:
                node = self.trie[node][char]

            # Check current node
            if self.output[node]:
                return True

            # Check failure links
            temp_node = self.failure_links[node]
            while temp_node != 0:
                if self.output[temp_node]:
                    return True
                temp_node = self.failure_links[temp_node]

        return False

    def reload(self):
        """Manually reload patterns from cache and rebuild automaton."""
        self._load_and_build()

    def get_patterns(self) -> List[str]:
        """Get the list of loaded patterns."""
        return self.patterns.copy()

    def get_stats(self) -> Dict[str, any]:
        """Get statistics about the automaton."""
        return {
            "pattern_count": len(self.patterns),
            "node_count": self.node_count,
            "is_initialized": len(self.patterns) > 0,
        }
