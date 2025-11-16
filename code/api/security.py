import logging
import os
import time
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

DEFAULT_RATE_LIMIT_MAX = int(os.environ.get("SEARCH_RATE_LIMIT_MAX", "60"))
DEFAULT_RATE_LIMIT_WINDOW = int(os.environ.get("SEARCH_RATE_LIMIT_WINDOW", "60"))

_api_key = os.environ.get("MSD_SEARCH_API_KEY") or os.environ.get("SEARCH_API_KEY")
if not _api_key:
    _api_key = os.environ.get("MSD_SEARCH_DEFAULT_KEY", "dev-msd-api-key")
    logger.warning("未配置 MSD_SEARCH_API_KEY；正在使用开发默认密钥，切勿在生产环境中暴露")


def get_expected_api_key():
    """返回应该匹配的 API Key。"""
    return _api_key


def extract_api_key(request):
    """从请求头中提取 API Key。"""
    header = request.headers.get("Authorization") or request.headers.get("X-API-Key")
    if not header:
        return None
    header = header.strip()
    if header.lower().startswith("bearer "):
        return header.split(" ", 1)[1]
    return header


def is_valid_api_key(provided_key):
    """验证提供的 API Key 是否有效。"""
    expected = get_expected_api_key()
    return bool(provided_key) and provided_key == expected


def get_client_identifier(request, scope=None):
    """构建基于 IP（以及可选作用域）的客户端标识符。"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",", 1)[0].strip()
    else:
        ip = getattr(request, "remote_addr", None) or "unknown"
    if scope:
        return f"{ip}:{scope}"
    return ip


class RateLimiter:
    """简单的滑动窗口限流器。"""

    def __init__(self, max_requests=DEFAULT_RATE_LIMIT_MAX, window_seconds=DEFAULT_RATE_LIMIT_WINDOW):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._access_log = defaultdict(deque)

    def allow(self, client_id):
        """判断给定 client_id 是否可以继续请求。"""
        now = time.monotonic()
        window_start = now - self.window_seconds
        log = self._access_log[client_id]

        while log and log[0] <= window_start:
            log.popleft()

        if len(log) >= self.max_requests:
            return False

        log.append(now)
        return True


rate_limiter = RateLimiter()

__all__ = [
    "rate_limiter",
    "extract_api_key",
    "get_client_identifier",
    "get_expected_api_key",
    "is_valid_api_key",
]
