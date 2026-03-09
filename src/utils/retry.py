import time

def retry_llm_call(func, max_retries=2, delay=2):
    """Retry an LLM call with exponential backoff."""
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries:
                raise RuntimeError(f"LLM call failed after {max_retries+1} attempts: {e}")
            time.sleep(delay*(attempt+1))