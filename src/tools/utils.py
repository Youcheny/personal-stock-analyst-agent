import time
from functools import wraps

def rate_limited(calls_per_second=4):
    min_interval = 1.0 / calls_per_second
    def deco(fn):
        last = [0.0]
        @wraps(fn)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            try:
                return fn(*args, **kwargs)
            finally:
                last[0] = time.time()
        return wrapper
    return deco
