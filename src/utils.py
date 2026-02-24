import re
import time
import logging
import functools

logger = logging.getLogger(__name__)

# Global state to track attempts across all Gemini calls
_retry_state = {"attempts": 0}

class QuotaObserverHandler(logging.Handler):
    """
    Listens to logs to detect successful responses and reset the quota counter.
    Works for internal library calls (like LangChain) that use httpx or direct SDKs.
    """
    def emit(self, record):
        try:
            msg = record.getMessage()
            # Reset on successful HTTP responses (200 OK)
            if '"HTTP/1.1 200 OK"' in msg or "status: 200" in msg.lower():
                if _retry_state["attempts"] > 0:
                    # We don't log here to avoid potential log loops, 
                    # just silently reset the global attempt counter.
                    _retry_state["attempts"] = 0
        except Exception:
            pass

# Attach the observer to relevant loggers to catch successful 200s from internal calls
for logger_name in ["httpx", "google.genai", "langchain_google_genai"]:
    logging.getLogger(logger_name).addHandler(QuotaObserverHandler())


def gemini_retry(max_attempts=5, default_delay=10):
    """
    Decorator that catches Gemini quota errors (429) and waits 
    the amount of time suggested by the API (retryDelay).
    Uses a global counter that resets on any 200 OK detected in logs.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            while _retry_state["attempts"] < max_attempts:
                try:
                    result = func(*args, **kwargs)
                    # After a success, reset the global counter
                    _retry_state["attempts"] = 0
                    return result
                except Exception as e:
                    error_msg = str(e)
                    
                    # Check if it's a quota error (429 / RESOURCE_EXHAUSTED)
                    if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                        _retry_state["attempts"] += 1
                        if _retry_state["attempts"] >= max_attempts:
                            logger.error("Max retry attempts reached for Gemini API. Resetting and failing.")
                            _retry_state["attempts"] = 0
                            raise e
                        
                        # Try to extract retryDelay from the error message
                        delay = default_delay
                        match = re.search(r"retryDelay': '(\d+)s'", error_msg)
                        if match:
                            delay = int(match.group(1))
                        else:
                            match = re.search(r"retry in ([\d\.]+)s", error_msg)
                            if match:
                                delay = int(float(match.group(1)))
                        
                        # Add a small buffer
                        wait_time = delay + 2
                        logger.warning(
                            "Gemini Quota Exceeded (429). Global Attempt %d/%d.", 
                            _retry_state["attempts"], max_attempts
                        )
                        # Explicit log before sleep showing the duration as requested
                        logger.info(f"Respecting retryDelay: sleeping for {wait_time} seconds before retrying...")
                        time.sleep(wait_time)
                    else:
                        # Not a quota error, raise normally
                        raise e
            return None
        return wrapper
    return decorator

def sanitize_filename(filename: str) -> str:
    r"""
    Removes or replaces characters that are illegal in Windows filenames.
    Forbidden characters: / \ : * ? " < > |
    """
    return re.sub(r'[\\/:\*\?"<>\|]', "_", filename)
