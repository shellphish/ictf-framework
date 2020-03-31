from collections import OrderedDict

class LRUCache(object):
    def __init__(self, capacity):
        self.max_capacity = capacity
        self.cached = OrderedDict()

    def __contains__(self, k):
        return k in self.cached

    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, key, value):
        return self.set(key, value)

    def get(self, k):
        if k in self.cached:
            v = self.cached.pop(k)
            self.cached[k] = v
            return v
        raise ValueError("Key {} was not cached, only {} were".format(k, list(self.cached.keys())))

    def set(self, k, v):
        self.cached[k] = v
        if len(self.cached) > self.max_capacity:
            return self.cached.popitem(last=False) # FIFO behavior
        return None


def func_args_to_cache_key(args, kwargs):
    return tuple(args), tuple(kwargs.items())


def lru_cache_decorator(capacity=32, cache=None):
    cache = LRUCache(capacity) if cache is None else cache

    def wrapper_f(f):
        def wrapped_f(*args, **kwargs):
            key = func_args_to_cache_key(args, kwargs)
            if key in cache:
                return cache.get(key)

            val = f(*args, **kwargs)
            cache.set(key, val)
            return val
        wrapped_f.uncached = f
        wrapped_f.cache = cache
        return wrapped_f
    return wrapper_f
