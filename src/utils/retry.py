import time
from src.utils.logger import get_logger

logger = get_logger("retry")

def retry_llm_call(func, max_retries=2, delay=2):
    """Retry an LLM call with exponential backoff."""
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries:
                logger.warning("LLM call failed after %d attempts: %s", max_retries+1, e)
                raise RuntimeError(f"LLM call failed after {max_retries+1} attempts: {e}")
            logger.warning("LLM call failed (attempt %d/%d): %s. Retrying...", attempt+1, max_retries+1, e)
            time.sleep(delay*(attempt+1))