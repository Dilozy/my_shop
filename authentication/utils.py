from django.core.cache import caches


def add_to_blacklist(jti, expires_in):
    cache = caches["default"]
    cache.set(jti, "revoked", timeout=expires_in)


def is_blacklisted(jti):
    return bool(caches["default"].get(jti))
