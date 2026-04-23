import os
from dotenv import load_dotenv
from urllib.parse import urlsplit, urlunsplit

load_dotenv()

def _clean_supabase_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    parsed = urlsplit(raw if "://" in raw else f"https://{raw}")
    path = parsed.path.rstrip("/")
    lower_path = path.lower()
    marker = "/rest/v1"
    index = lower_path.find(marker)
    if index >= 0:
        path = path[:index]
    return urlunsplit((parsed.scheme, parsed.netloc, path.rstrip("/"), "", "")).rstrip("/")


SUPABASE_URL = _clean_supabase_url(os.getenv("SUPABASE_URL", ""))
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

CACHE_FILE = os.getenv("NEXAR_CACHE_FILE", "license_cache.json")
CACHE_EXPIRATION_DAYS = int(os.getenv("NEXAR_CACHE_DAYS", "3"))

DEFAULT_TIMEOUT = 10
