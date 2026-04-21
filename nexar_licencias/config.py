import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

CACHE_FILE = os.getenv("NEXAR_CACHE_FILE", "license_cache.json")
CACHE_EXPIRATION_DAYS = int(os.getenv("NEXAR_CACHE_DAYS", "3"))

DEFAULT_TIMEOUT = 10