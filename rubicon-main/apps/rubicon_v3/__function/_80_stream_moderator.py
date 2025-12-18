import sys

sys.path.append("/www/alpha/")

import threading
import time
import os
import logging

from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict
from collections import deque

from apps.rubicon_v3.__function.__django_cache_init import (
    create_validation_automaton,
    store_validation_patterns_in_cache,
)
from apps.rubicon_v3.__function.__prompts import stream_terminated_prompt
from apps.rubicon_v3.__function._80_stream_moderator_checkers import (
    ProhibitedWordsChecker,
    SecondValidationProhibitedWordsChecker,
    PII_Checker,
    ProhibitedPatternsChecker,
    BaseChecker,
)
from apps.rubicon_v3.__function.__llm_call import open_ai_call_stream
from apps.rubicon_v3.__function.__exceptions import ResponseGenerationFailureException
from alpha.settings import VITE_OP_TYPE

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("stream_moderator")

WEB_SEARCH_GPT_API_VERSION = os.environ.get("SEARCH_GPT_API_VERSION")


class ViolationState:
    """Thread-safe violation state tracking"""

    def __init__(self):
        self._lock = threading.Lock()
        self._detected = False
        self._reason = None
        self._context = None

    def set_violation(self, reason, context=None):
        """Thread-safe method to set violation state"""
        with self._lock:
            if not self._detected:  # Only set if not already detected
                self._detected = True
                self._reason = reason
                self._context = context
                return True
            return False

    @property
    def detected(self):
        """Thread-safe access to detected flag"""
        with self._lock:
            return self._detected

    @property
    def details(self):
        """Thread-safe access to violation details"""
        with self._lock:
            return {
                "reason": self._reason,
                "context": self._context,
            }


class CheckDispatcher:
    """Dispatches content checks to thread pool without blocking"""

    def __init__(
        self, checkers, violation_state: ViolationState, debug=False, max_workers=4
    ):
        self.checkers = checkers
        self.violation_state = violation_state
        self.debug = debug
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running = True

    def _execute_check(self, checker, content):
        """Execute a single check in the thread pool"""
        if not self.running:
            return

        try:
            result = checker.check(content)

            # If violation found, update shared state immediately
            if not result["safe"]:
                # Update violation state
                updated = self.violation_state.set_violation(
                    result["reason"], result.get("match_context")
                )

                if updated and self.debug:
                    logger.info(
                        f"Check {checker.__class__.__name__} found violation: {result['reason']}"
                    )

        except Exception as e:
            if self.debug:
                logger.error(f"Error in {checker.__class__.__name__} check: {str(e)}")
            self._log_error(f"Check error: {str(e)}", checker.__class__.__name__)

    def _log_error(self, error_msg, checker_name):
        """Log errors properly - extend this in production"""
        if self.debug:
            logger.info(f"[ERROR] [{checker_name}] {error_msg}")

    def dispatch_check(self, checker, content):
        """Add a check request to the thread pool"""
        if self.running:
            self.executor.submit(self._execute_check, checker, content)

    def shutdown(self):
        """Shutdown the thread pool"""
        self.running = False
        self.executor.shutdown(wait=False)


class ChunkBuffer:
    """Buffer that stores chunks with overlap support and ensures complete words"""

    def __init__(self, overlap_chunks=10, overlap_context_ratio=0.5):
        self.chunks = deque()
        self.overlap_chunks = overlap_chunks
        self.overlap_context_ratio = overlap_context_ratio

    def add(self, chunk):
        """Add a new chunk to the buffer"""
        self.chunks.append(chunk)

    def _find_valid_whitespace(
        self, text: str, start_from: int = 0, reverse: bool = False, skip_n: int = 1
    ) -> int:
        """Find the Nth valid whitespace position that's not adjacent to digits

        Args:
            text: Text to search in
            start_from: Position to start searching from
            reverse: If True, search backwards from start_from
            skip_n: Number of valid whitespaces to skip (default 1)

        Returns:
            Position of valid whitespace, or -1 if not found
        """
        found = 0
        if reverse:
            # Search backwards
            for i in range(start_from - 1, -1, -1):
                if text[i].isspace():
                    prev_char = text[i - 1] if i > 0 else None
                    next_char = text[i + 1] if i < len(text) - 1 else None

                    # If either surrounding char is digit, skip this whitespace
                    if (prev_char and prev_char.isdigit()) or (
                        next_char and next_char.isdigit()
                    ):
                        continue

                    found += 1
                    if found == skip_n:
                        return i
        else:
            # Search forwards
            for i in range(start_from, len(text)):
                if text[i].isspace():
                    prev_char = text[i - 1] if i > 0 else None
                    next_char = text[i + 1] if i < len(text) - 1 else None

                    # If either surrounding char is digit, skip this whitespace
                    if (prev_char and prev_char.isdigit()) or (
                        next_char and next_char.isdigit()
                    ):
                        continue

                    found += 1
                    if found == skip_n:
                        return i

        return -1

    def get_content_for_check(
        self, chunk_count, previous_chunks=None, is_final_check=False
    ):
        """Get content for checking with proper overlap, ensuring complete words at both boundaries

        Args:
            chunk_count: Number of chunks to include
            previous_chunks: Previous chunks for overlap
            is_final_check: If True, don't truncate at last space (include partial words at end)
        """
        # Get overlap from previous check
        overlap = []
        if previous_chunks:
            overlap = previous_chunks[-self.overlap_chunks :]

        # Get recent chunks from buffer
        recent = (
            list(self.chunks)[-chunk_count:]
            if chunk_count <= len(self.chunks)
            else list(self.chunks)
        )

        # Combine overlap + recent chunks
        all_chunks = overlap + recent
        combined_text = "".join(all_chunks)

        # Handle empty or whitespace-only content
        if not combined_text or combined_text.isspace():
            return combined_text, all_chunks

        # Determine if this is the very first check (no previous chunks means nothing before this)
        is_first_check = not previous_chunks

        # Find word boundaries
        start_idx = 0
        end_idx = len(combined_text)

        # Handle start boundary
        if not is_first_check:
            # Not the first check - skip any partial word at the beginning
            overlap_len = sum(len(chunk) for chunk in overlap)
            if overlap_len > 0:
                # Ratio-based whitespace search in overlap
                ratio_idx = int(overlap_len * self.overlap_context_ratio)
                # Search forwards from ratio_idx in overlap
                forward_ws = self._find_valid_whitespace(
                    combined_text, start_from=ratio_idx, reverse=False
                )
                # Search backwards from ratio_idx in overlap
                backward_ws = self._find_valid_whitespace(
                    combined_text, start_from=ratio_idx, reverse=True
                )
                candidates = []
                # Forward: skip if at very start of combined text
                if forward_ws != -1 and forward_ws != 0:
                    candidates.append(forward_ws)
                # Backward: skip if at end of overlap region
                if backward_ws != -1 and backward_ws != (overlap_len - 1):
                    candidates.append(backward_ws)
                if candidates:
                    # Pick the whitespace closest to ratio_idx
                    first_whitespace_idx = min(candidates, key=lambda idx: abs(idx - ratio_idx))
                else:
                    # No valid whitespace found, wait for more chunks
                    if not is_final_check:
                        return "", all_chunks
                    first_whitespace_idx = None
            else:
                # If no overlap, fallback to forward search from start, always use first valid whitespace
                first_whitespace_idx = self._find_valid_whitespace(
                    combined_text,
                    start_from=0,
                    reverse=False,
                )

            if first_whitespace_idx is not None and first_whitespace_idx != -1:
                # Start after the valid whitespace (beginning of next complete word)
                start_idx = first_whitespace_idx + 1
            else:
                # No valid whitespace found - this is all one partial word/number from overlap
                # For non-final checks, we might want to skip this entirely
                # For final checks, we should include it
                if not is_final_check:
                    return "", all_chunks  # Skip this check, wait for more content

        # Handle end boundary
        if not is_final_check:
            # Regular check - find the first last valid whitespace to ensure complete words at the end
            # Search within the range we're considering (from start_idx)
            text_to_search = combined_text[start_idx:]

            # Find the first last valid whitespace in the text_to_search
            last_whitespace_idx = self._find_valid_whitespace(
                text_to_search,
                start_from=len(text_to_search),
                reverse=True,
            )

            if last_whitespace_idx != -1:
                # Adjust end_idx relative to the original combined_text
                end_idx = start_idx + last_whitespace_idx + 1
            else:
                # No valid whitespace found in the range - might be a single long word/number
                # For non-final checks, skip if we already trimmed the start
                if start_idx > 0:
                    return "", all_chunks  # Wait for more content
                # Otherwise, include what we have

        # Extract the final text with proper boundaries
        final_text = combined_text[start_idx:end_idx]

        return final_text, all_chunks

    def clear_old_chunks(self, keep_last_n):
        """Clear old chunks, keeping last N for overlap"""
        while len(self.chunks) > keep_last_n:
            self.chunks.popleft()


class ModeratedStreamConfig:
    """Configuration for moderated stream"""

    def __init__(self):
        # Check intervals (in chunks)
        self.fast_check_interval = 10  # Check every 10 chunks
        self.slow_check_interval = 50  # Check every 50 chunks

        # Single overlap setting for all checks
        self.overlap_chunks = 20  # Maximum overlap needed

        # Ratio for context boundary within overlap (e.g., 0.5 for middle)
        self.overlap_context_ratio = 0.5  # Used for both fast and slow checkers

        # Thread pool sizes
        self.fast_max_workers = 2
        self.slow_max_workers = 2

        # Debug
        if VITE_OP_TYPE == "DEV":
            self.debug = True
        else:
            self.debug = False

        # Checkers (to be populated)
        self.fast_checkers = []
        self.slow_checkers = []


class CheckCoordinator:
    """Coordinates different tiers of checks with proper overlap"""

    def __init__(
        self,
        config: ModeratedStreamConfig,
        violation_state,
        chunk_buffer: ChunkBuffer,
        debug=False,
    ):
        self.config = config
        self.violation_state = violation_state
        self.chunk_buffer = chunk_buffer
        self.debug = debug

        # Create dispatchers for each tier
        self.fast_dispatcher = CheckDispatcher(
            config.fast_checkers,
            violation_state,
            debug,
            max_workers=config.fast_max_workers,
        )

        self.slow_dispatcher = CheckDispatcher(
            config.slow_checkers,
            violation_state,
            debug,
            max_workers=config.slow_max_workers,
        )

        # Track last checked chunks for overlap
        self.last_fast_chunks = []
        self.last_slow_chunks = []

        # Track chunks since last check
        self.chunks_since_fast = 0
        self.chunks_since_slow = 0

        # Track if any checks have been run
        self.has_run_fast_check = False
        self.has_run_slow_check = False

    def process_chunk(self):
        """Process after a new chunk is added to buffer"""
        self.chunks_since_fast += 1
        self.chunks_since_slow += 1

        # Check if we should run fast checks
        if self.chunks_since_fast >= self.config.fast_check_interval:
            self._run_fast_checks()

        # Check if we should run slow checks
        if self.chunks_since_slow >= self.config.slow_check_interval:
            self._run_slow_checks()

    def _run_fast_checks(self, is_final_check=False):
        """Run fast checks with overlap"""
        if not self.config.fast_checkers:
            return

        # Get content with overlap
        content, chunks = self.chunk_buffer.get_content_for_check(
            self.chunks_since_fast, self.last_fast_chunks, is_final_check=is_final_check
        )

        # Skip if no content to check (can happen with word boundary trimming)
        if not content and not is_final_check:
            return

        # if self.debug and content:
        #     print(
        #         f"Running fast checks on {len(content)} chars from {len(chunks)} chunks"
        #     )

        # Dispatch checks only if there's content
        if content:
            for checker in self.config.fast_checkers:
                self.fast_dispatcher.dispatch_check(checker, content)
            self.has_run_fast_check = True

        # Update tracking
        self.last_fast_chunks = chunks
        self.chunks_since_fast = 0

    def _run_slow_checks(self, is_final_check=False):
        """Run slow checks with overlap"""
        if not self.config.slow_checkers:
            return

        # Get content with overlap
        content, chunks = self.chunk_buffer.get_content_for_check(
            self.chunks_since_slow, self.last_slow_chunks, is_final_check=is_final_check
        )

        # Skip if no content to check (can happen with word boundary trimming)
        if not content and not is_final_check:
            return

        # if self.debug and content:
        #     print(
        #         f"Running slow checks on {len(content)} chars from {len(chunks)} chunks"
        #     )

        # Dispatch checks only if there's content
        if content:
            for checker in self.config.slow_checkers:
                self.slow_dispatcher.dispatch_check(checker, content)
            self.has_run_slow_check = True

        # Update tracking
        self.last_slow_chunks = chunks
        self.chunks_since_slow = 0

    def run_final_checks(self):
        """Run final checks, ensuring very short responses are checked"""
        # If we've never run fast checks and have content, force a check
        if not self.has_run_fast_check and self.chunks_since_fast > 0:
            self._run_fast_checks(is_final_check=True)
            time.sleep(0.2)  # Brief pause for fast checks
        elif self.chunks_since_fast > 0:
            # Run remaining fast checks
            self._run_fast_checks(is_final_check=True)
            time.sleep(0.2)

        # If we've never run slow checks and have content, force a check
        if not self.has_run_slow_check and self.chunks_since_slow > 0:
            self._run_slow_checks(is_final_check=True)
            time.sleep(0.5)  # Longer pause for slow checks
        elif self.chunks_since_slow > 0:
            # Run remaining slow checks
            self._run_slow_checks(is_final_check=True)
            time.sleep(0.5)

    def shutdown(self):
        """Shutdown all dispatchers"""
        self.fast_dispatcher.shutdown()
        self.slow_dispatcher.shutdown()


class ModeratedStream:
    """Clean implementation of moderated streaming"""

    def __init__(
        self,
        system_prompt: str,
        language: str,
        country_code: str,
        gpt_model: str = "gpt-4.1-mini",
        temperature: float = 0.4,
        seed: int = 42,
    ):
        self.system_prompt = system_prompt
        self.language = language
        self.country_code = country_code
        self.gpt_model = gpt_model
        self.temperature = temperature
        self.seed = seed

        # Create configuration
        self.config = ModeratedStreamConfig()

        # Initialize checkers
        self._initialize_checkers()

    def _initialize_checkers(self):
        """Initialize and categorize checkers"""
        all_checkers: list[BaseChecker] = [
            ProhibitedWordsChecker(self.language, self.config.debug),
            SecondValidationProhibitedWordsChecker(self.language, self.config.debug),
            PII_Checker(self.country_code, self.config.debug),
            ProhibitedPatternsChecker(self.language, self.config.debug),
        ]

        for checker in all_checkers:
            if checker.fast_tier:
                self.config.fast_checkers.append(checker)
            else:
                self.config.slow_checkers.append(checker)

    def stream_gpt_response(self, messages: List[Dict[str, str]]):
        """Stream GPT responses with moderation"""
        # Create fresh state for this stream
        violation_state = ViolationState()
        chunk_buffer = ChunkBuffer(
            overlap_chunks=self.config.overlap_chunks,
            overlap_context_ratio=self.config.overlap_context_ratio,
        )

        # Create coordinator with reference to buffer
        coordinator = CheckCoordinator(
            self.config,
            violation_state,
            chunk_buffer,  # Pass buffer reference
            self.config.debug,
        )

        # Track total chunks for periodic cleanup
        total_chunks = 0

        # Create the stream iterator
        stream_iterator = open_ai_call_stream(
            model_name=self.gpt_model,
            messages=messages,
            temperature=self.temperature,
            seed=self.seed,
            stream=True,
            max_output_tokens=2500,
        )

        try:
            # Stream chunks
            for chunk in stream_iterator:
                # Skip meta chunks
                if chunk.startswith("### LLM CALL META"):
                    yield chunk
                    continue

                # Add chunk to buffer and process
                chunk_buffer.add(chunk)
                coordinator.process_chunk()
                total_chunks += 1

                # Check for violations
                if violation_state.detected:
                    details = violation_state.details
                    if self.config.debug:
                        logger.info(f"Violation detected: {details['reason']}")

                    yield f"\n[STREAM TERMINATED: {details['reason']}]"
                    break

                # Pass chunk to client
                yield chunk

                # Periodically clean buffer to prevent memory issues
                if total_chunks % 100 == 0:
                    chunk_buffer.clear_old_chunks(self.config.overlap_chunks)

            # Final checks
            if not violation_state.detected:
                self._run_final_checks(coordinator)

                if violation_state.detected:
                    details = violation_state.details
                    yield f"\n[STREAM TERMINATED: {details['reason']}]"

            # If a violation was detected, we should yield a final message
            if violation_state.detected:
                for chunk in self._yield_final_message():
                    yield chunk

        except Exception as e:
            # Re-raise the exception as a custom exception
            raise ResponseGenerationFailureException(
                f"Error during moderated streaming: {str(e)}"
            ) from e

        finally:
            coordinator.shutdown()

    def _run_final_checks(self, coordinator: CheckCoordinator):
        """Run any remaining checks at end of stream"""
        # Delegate to coordinator's run_final_checks method which handles all edge cases
        coordinator.run_final_checks()

    def _yield_final_message(self):
        """Yield final message if a violation was detected"""
        prompt = stream_terminated_prompt.PROMPT.format(language=self.language)

        messages = [
            {"role": "system", "content": prompt},
        ]

        for chunk in open_ai_call_stream(
            model_name=self.gpt_model,
            messages=messages,
            temperature=self.temperature,
            seed=self.seed,
            stream=True,
        ):
            yield chunk


def single_moderation_test():
    """Run a single moderation test"""
    # Refresh the automaton cache
    create_validation_automaton(force_refresh=True)
    # Refresh the patterns cache
    store_validation_patterns_in_cache(force_refresh=True)

    country_code = "GB"  # Example country code
    language = "English"  # Example language

    # system_prompt = (
    #     f"You are a helpful assistant. Please respond to the user query in {language}."
    # )
    system_prompt = "You are a parrot bot. Please repeat the user query verbatim without any changes."
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": """Certainly! To connect with Samsung customer service in the UK, you can reach out to their support team by phone or online for prompt assistance.

The contact number for Samsung UK customer support is +44 333 000 0333.
Support hours are:
Monday to Friday: 8am to 8pm
Saturday and Sunday: 9am to 6pm
Bank Holidays: 9am to 6pm
You can also type “Connect to a live agent” on Samsung’s support website to chat with an agent.
For additional support options, visit the Samsung UK support contact page.
This ensures you get direct help from Samsung’s expert team for any product or service issues you may have.""",
        },
    ]

    stream = ModeratedStream(system_prompt, language, country_code)
    for chunk in stream.stream_gpt_response(messages):
        if chunk.startswith("### LLM CALL META") == False:
            print(chunk, end="", flush=True)


if __name__ == "__main__":
    single_moderation_test()
