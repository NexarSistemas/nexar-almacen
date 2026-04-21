import json
import os
from datetime import datetime, timedelta
from .config import CACHE_FILE, CACHE_EXPIRATION_DAYS

def save_cache(license_data):
    cache = {
        "data": license_data,
        "last_check": datetime.now().isoformat()
    }
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

def get_cache():
    if not os.path.exists(CACHE_FILE):
        return None
    
    try:
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
        
        last_check = datetime.fromisoformat(cache["last_check"])
        if datetime.now() > last_check + timedelta(days=CACHE_EXPIRATION_DAYS):
            return None # Cache expirado
            
        return cache["data"]
    except:
        return None