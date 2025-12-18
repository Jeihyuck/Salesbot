from functools import wraps
from django.core.cache import cache
from alpha.__log import debug, error, info

def alpha_cache(timeout=3600):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            try: 
                cache_key = request['request']['requestHash']
            except Exception as e:
                cache_key = f'{func.__name__}-{request.path}-{args}-{kwargs}'
            # debug(cache_key)
            cached_response = cache.get(cache_key)
            if cached_response:
                return cached_response
            response = func(request, *args, **kwargs)
            cache.set(cache_key, response, timeout=timeout)
            return response
        return wrapper
    return decorator
