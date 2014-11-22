import hashlib
from datetime import datetime, timedelta
try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit

from django.core.cache import get_cache
from django.core.cache.backends.memcached import MemcachedCache, PyLibMCCache
from django import VERSION

import dumper.settings


def cache_key(path, method):
    # remove fragment from path
    path = urlsplit(path)[2]

    path_hash = hashlib.md5(path.encode('utf-8')).hexdigest()

    return '{prefix}{path_hash}.{method}'.format(
        prefix=dumper.settings.KEY_PREFIX,
        path_hash=path_hash,
        method=method
    )


def cache_key_from_request(request):
    return cache_key(request.path, request.method)

cache = get_cache(dumper.settings.CACHE_ALIAS)

# Consider "forever" to be the maximum representable datetime on this system
# less 2 days for timezone vs. UTC conflicts, processing time, and a little
# superstition. What's two days to virtual eternity?
forever = datetime.max - timedelta(days=2)


def get_forever(cache_instance=cache):
    forever_from_now = forever - datetime.utcnow()
    forever_from_now -= timedelta(microseconds=forever_from_now.microseconds)
    forever_from_now = forever_from_now.total_seconds()

    if VERSION >= (1, 6):
        # Let Django do the work for us.
        cache_forever = None
    elif isinstance(cache_instance, (MemcachedCache, PyLibMCCache)):
        # memcached treats any amount of seconds over 30 days as a literal
        # Unix timestamp. As such, we must find the literal Unix timestamp
        # of our chosen datetime.
        cache_forever = forever - datetime(1970, 1, 1)
        cache_forever -= timedelta(microseconds=cache_forever.microseconds)
        cache_forever = cache_forever.total_seconds()
    else:
        cache_forever = forever_from_now

    return forever_from_now, cache_forever
