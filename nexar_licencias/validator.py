from .verifier_local import verificar_firma
from .verifier_online import check_supabase
from .cache import save_cache, get_cache
from .plans import normalize_license_data

def validar_licencia_detalle(licencia_dict, public_key, product_name, debug=False):

    if debug:
        print(f"[DEBUG] Validando producto: {product_name}")

    # 1. FIRMA (DEV OK)
    if not verificar_firma(licencia_dict, public_key, debug=debug):
        if debug:
            print("[DEBUG] Fallo de firma local.")
        return {"ok": False, "reason": "firma_invalida", "source": "local"}

    license_key = licencia_dict.get("license_key")

    # 2. ONLINE (SUPABASE)
    online_data = check_supabase(license_key, product_name, debug=debug)

    if online_data is False:
        if debug:
            print("[DEBUG] Licencia NO existe en Supabase.")
        return {"ok": False, "reason": "no_existe", "source": "online"}
    if isinstance(online_data, dict) and online_data.get("_lic_error"):
        return {"ok": False, "reason": online_data.get("_lic_error"), "source": "online"}

    from datetime import datetime

    if online_data:
        if debug: print("[DEBUG] Licencia válida online.")
        online_data = normalize_license_data(online_data)

        # 🔴 verificar activa
        if not online_data.get("activa", True):
            if debug: print("[DEBUG] Licencia desactivada.")
            return {"ok": False, "reason": "revocada", "source": "online", "license": online_data}

        # 🔴 verificar expiración
        expira = online_data.get("expira")
        if expira:
            if datetime.now().date() > datetime.fromisoformat(expira).date():
                if debug: print("[DEBUG] Licencia expirada.")
                return {"ok": False, "reason": "expirada", "source": "online", "license": online_data}

        save_cache(online_data)
        return {"ok": True, "source": "online", "license": online_data}

    # 3. OFFLINE (CACHE)
    cached = get_cache()

    if cached and cached.get("license_key") == license_key:
        if debug:
            print("[DEBUG] Usando cache offline.")
        return {"ok": True, "source": "cache", "license": normalize_license_data(cached)}

    return {"ok": False, "reason": "sin_cache", "source": "cache"}


def validar_licencia(licencia_dict, public_key, product_name, debug=False):
    return bool(validar_licencia_detalle(licencia_dict, public_key, product_name, debug).get("ok"))
