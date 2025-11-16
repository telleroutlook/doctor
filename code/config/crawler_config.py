# 爬虫配置
import random

# 支持的语言版本及入口URL
def _language_entry(start_url, extra_urls=None):
    """统一生成语言入口配置"""
    entry = {"start_url": start_url}
    if extra_urls:
        entry["extra_urls"] = list(extra_urls)
    return entry


LANGUAGE_VERSION_URLS = {
    "home": {
        "en": _language_entry(
            "https://www.msdmanuals.com/home/",
            extra_urls=["health-topics/"]
        ),
        "zh": _language_entry(
            "https://www.msdmanuals.cn/home/",
            extra_urls=["health-topics/", "https://www.msdmanuals.cn/"]
        )
    },
    "professional": {
        "en": _language_entry("https://www.msdmanuals.com/professional/"),
        "zh": _language_entry("https://www.msdmanuals.cn/professional/")
    },
    "veterinary": {
        "en": _language_entry("https://www.msdvetmanual.com/")
    }
}

# 爬虫基础配置
CRAWLER_CONFIG = {
    "max_workers": 3,
    "delay_between_requests": 5.0,
    "max_retries": 3,
    "timeout": 30,
    "respect_robots_txt": True,
    "download_timeout": 60,
    "download_delay": 5,
    "randomize_download_delay": True,
    "download_delay_range": (4, 6),
}

# 用户代理轮换
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
]

# 请求头配置
DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5,zh-CN;q=0.3",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

# 域名特定配置
DOMAIN_CONFIGS = {
    "www.msdmanuals.com": {
        "delay": 5.0,
        "max_concurrent": 3,
        "priority": "high"
    },
    "www.msdmanuals.cn": {
        "delay": 6.0,
        "max_concurrent": 2,
        "priority": "high"
    },
    "www.msdvetmanual.com": {
        "delay": 7.0,
        "max_concurrent": 1,
        "priority": "medium"
    }
}

# 重试配置
RETRY_CONFIG = {
    "max_retries": 3,
    "retry_delay_range": (1, 5),
    "backoff_factor": 2,
    "retry_status_codes": [429, 500, 502, 503, 504],
    "give_up_status_codes": [403, 404, 451]
}

# 状态文件配置
STATE_CONFIG = {
    "state_file": "crawler_state.json",
    "save_interval": 100,
    "checkpoints_dir": "checkpoints",
    "backup_enabled": True,
    "backup_interval": 500
}
