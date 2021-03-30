class Cache(object):
    @dataclass(frozen=True)
    class CacheDirective:
        value_type: type
        required: bool

    # https://tools.ietf.org/html/rfc7234#section-5.2
    CACHE_DIRECTIVES: dict[str, CacheDirective] = {
        "max-age": CacheDirective(int, True),
        "max-stale": CacheDirective(int, False),
        "min-fresh": CacheDirective(int, True),
        "no-cache": CacheDirective(None, False),
        "no-store": CacheDirective(None, False),
        "no-transform": CacheDirective(None, False),
        "only-if-cached": CacheDirective(None, False),
        "must-revalidate": CacheDirective(None, False),
        "public": CacheDirective(None, False),
        "private": CacheDirective(None, False),
        "proxy-revalidate": CacheDirective(None, False),
        "s-maxage": CacheDirective(int, True),
    }

    def __init__(self):
        pass

    def parse_cache_control_header(self, cache_control):
        result = {}

        for raw_directive_str in cache_control.split(","):
            try:
                directive_strs = raw_directive_str.strip().split("=", 1)
                directive_key = directive_strs[0]
                directive = CACHE_DIRECTIVES[directive_key]

                if directive.value_type is None or not directive.required:
                    result[directive_key] = None
                if directive.value_type:
                    result[directive_key] = directive.value_type(directive_strs[1])
            except:
                # TODO: logging error directives
                continue

        return result

    def is_cacheable(parsed_cache_control):
        if "no-cache" in parsed_cache_control:
            return False

        if "max-age" in parsed_cache_control and parsed_cache_control["max-age"] == 0:
            return False


    def do_cached_request(self, request):
        url = request.url
        cache_control = request.headers.get("cache-control", request.headers.get("Cache-Control", ""))
        parsed_cache_control = self.parse_cache_control(cache_control)
        if not is_cacheable(parsed_cache_control):
            return False

        # Redisでurlチェック、ないとFalse
        # Redisでメタ情報取得、デコード失敗でFalse
        # 永久リダイレクトの場合は、etagとか日付とかチェックせずにすぐ返す
        # S3でurlチェック、ないとFalse
