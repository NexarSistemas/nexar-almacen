def obtener_license_key(licencia: dict) -> str:
    return licencia.get("license_key", "")