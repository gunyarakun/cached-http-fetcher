from email.utils import formatdate
from requests.structures import CaseInsensitiveDict
from cached_http_fetcher.content import put_content, parse_cache_control, calc_expired_at

def test_parse_cache_control():
    directives = parse_cache_control("no-cache")
    assert "no-cache" in directives
    assert directives["no-cache"] is None

    directives = parse_cache_control("max-age=12345")
    assert "max-age" in directives
    assert directives["max-age"] == "12345"

    directives = parse_cache_control("max-stale")
    assert "max-stale" in directives
    assert directives["max-stale"] is None

    directives = parse_cache_control("max-stale=23456")
    assert "max-stale" in directives
    assert directives["max-stale"] == "23456"


def test_calc_expired_at():
    now = 1617355068
    min_cache_age = 47387

    # Cache-Control: no-store
    expired_at = calc_expired_at(CaseInsensitiveDict({"cache-control": "no-store"}), now, min_cache_age)
    assert expired_at == now + min_cache_age

    # Cache-Control: max-age=xxxxx, larger than min_cache_age
    max_age = min_cache_age + 4346
    expired_at = calc_expired_at(CaseInsensitiveDict({"cache-control": f"max-age={max_age}"}), now, min_cache_age)
    assert expired_at == now + max_age

    # Cache-Control: max-age=xxxxx, smaller than min_cache_age
    max_age = min_cache_age - 4346
    expired_at = calc_expired_at(CaseInsensitiveDict({"cache-control": f"max-age={max_age}"}), now, min_cache_age)
    assert expired_at == now + min_cache_age

    # Expires: <now on RFC 2822>
    expired_at = calc_expired_at(CaseInsensitiveDict({"expires": formatdate(now)}), now, min_cache_age)
    assert expired_at == now + min_cache_age

    # Expires: <now on RFC 2822>
    expires = now + min_cache_age + 434553
    expired_at = calc_expired_at(CaseInsensitiveDict({"expires": formatdate(expires)}), now, min_cache_age)
    assert expired_at == expires
