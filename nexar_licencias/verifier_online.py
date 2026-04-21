from .device import get_hwid, get_product_hwid

import requests
from .config import SUPABASE_URL, SUPABASE_KEY, DEFAULT_TIMEOUT


def check_supabase(license_key, product, debug=False):

    if not SUPABASE_URL or not SUPABASE_KEY:
        if debug:
            print("[ERROR] Supabase no configurado")
        return None

    url = f"{SUPABASE_URL}/rest/v1/licencias"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    params = {
        "license_key": f"eq.{license_key}",
        "producto": f"eq.{product}",
        "select": "*"
    }

    # 🔥 DEBUG
    if debug:
        print("\n[DEBUG SUPABASE]")
        print("URL:", url)
        print("PARAMS:", params)
        print("LICENSE:", license_key)
        print("PRODUCT:", product)

    try:
        r = requests.get(url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT)

        if debug:
            print("[DEBUG] STATUS:", r.status_code)

        if r.status_code != 200:
            if debug:
                print("[ERROR] Supabase status:", r.status_code)
                print("[ERROR BODY]:", r.text)
            return None

        data = r.json()

        if debug:
            print("[DEBUG] RESPONSE:", data)

        if not data:
            return False

        lic = data[0]

        # 🔥 obtener HWID actual
        hwid_actual = get_product_hwid(product)
        hwid_legacy_actual = get_hwid()

        if debug:
            print("[DEBUG] HWID ACTUAL:", hwid_actual)
            print("[DEBUG] HWID LEGACY ACTUAL:", hwid_legacy_actual)
            print("[DEBUG] HWID BD:", lic.get("hwid"))
            print("[DEBUG] HWIDS BD:", lic.get("hwids"))

        hwids = lic.get("hwids") or []
        if isinstance(hwids, str):
            hwids = [hwids] if hwids else []
        hwid_legacy = lic.get("hwid")
        if hwid_legacy and hwid_legacy not in hwids:
            hwids = [hwid_legacy, *hwids]
        max_devices = int(lic.get("max_devices") or 1)

        # 🔥 CASO 1: ya autorizado
        if (
            lic.get("hwid") in {hwid_actual, hwid_legacy_actual}
            or hwid_actual in hwids
            or hwid_legacy_actual in hwids
        ):
            if debug:
                print("[DEBUG] HWID correcto")
            lic["hwids"] = sorted(set(hwids))[:max_devices]
            return lic

        # 🔥 CASO 2: primera activación o cupo disponible
        if not lic.get("hwid") or len(hwids) < max_devices:
            if debug:
                print("[DEBUG] Guardando HWID en cupo disponible")
            ok_update = asignar_hwid(lic["id"], hwid_actual, hwids, max_devices, debug=debug)

            if not ok_update:
                if debug:
                    print("[ERROR] No se pudo guardar HWID")
                return {"_lic_error": "no_se_pudo_vincular_dispositivo", "license_key": license_key}

            lic["hwid"] = lic.get("hwid") or hwid_actual
            lic["hwids"] = sorted(set([*hwids, hwid_actual]))[:max_devices]
            if debug:
                print("[DEBUG] HWID guardado correctamente")
            return lic

        # 🔥 CASO 3: sin cupo
        if debug:
            print("[DEBUG] Limite de dispositivos alcanzado")
        return {"_lic_error": "limite_dispositivos", "license_key": license_key}

    except Exception as e:
        if debug:
            print("[ERROR SUPABASE]", e)
        return None
    
def asignar_hwid(lic_id, hwid, hwids=None, max_devices=1, debug=False):
    url = f"{SUPABASE_URL}/rest/v1/licencias"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    params = {
        "id": f"eq.{lic_id}"   # 👈 CAMBIO CLAVE
    }

    hwids = sorted(set([*(hwids or []), hwid]))[:max_devices]
    data = {
        "hwid": hwids[0] if hwids else hwid,
        "hwids": hwids
    }

    try:
        r = requests.patch(
            url,
            headers=headers,
            params=params,
            json=data,
            timeout=DEFAULT_TIMEOUT
        )

        if debug:
            print("[DEBUG] UPDATE STATUS:", r.status_code)
            print("[DEBUG] UPDATE RESPONSE:", r.text)

        return r.status_code in (200, 204)

    except Exception as e:
        if debug:
            print("[ERROR UPDATE HWID]", e)
        return False
