from __future__ import annotations

import getpass
import hashlib
import os
import platform
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import requests

from licensing.planes import normalize_license_tier


_SUPABASE_DEBUG = {
    "last_operation": "",
    "status": "",
    "status_code": None,
    "last_error": "",
}


def normalize_plan(plan: str = "") -> str:
    return normalize_license_tier(plan, default="BASICA")


def _product_default() -> str:
    return os.getenv("LICENSE_PRODUCT", "nexar-almacen").strip() or "nexar-almacen"


def _set_debug(*, operation: str, status: str, status_code=None, last_error: str = "") -> None:
    _SUPABASE_DEBUG["last_operation"] = operation
    _SUPABASE_DEBUG["status"] = status
    _SUPABASE_DEBUG["status_code"] = status_code
    _SUPABASE_DEBUG["last_error"] = last_error


def get_supabase_debug_state() -> dict[str, Any]:
    return {
        "configured": is_configured(),
        "has_url": bool(os.getenv("SUPABASE_URL", "").strip()),
        "has_anon_key": bool(_anon_key().strip()),
        "last_operation": _SUPABASE_DEBUG["last_operation"],
        "status": _SUPABASE_DEBUG["status"],
        "status_code": _SUPABASE_DEBUG["status_code"],
        "last_error": _SUPABASE_DEBUG["last_error"],
    }


def _clean_base_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""

    parsed = urlsplit(raw if "://" in raw else f"https://{raw}")
    path = parsed.path.rstrip("/")
    lower_path = path.lower()
    for marker in ("/rest/v1", "/rest/v1/"):
        index = lower_path.find(marker.rstrip("/"))
        if index >= 0:
            path = path[:index]
            break

    return urlunsplit((parsed.scheme, parsed.netloc, path.rstrip("/"), "", "")).rstrip("/")


def _table_url() -> str:
    base = _clean_base_url(os.getenv("SUPABASE_URL", ""))
    return f"{base}/rest/v1/licencias" if base else ""


def _requests_table_url() -> str:
    base = _clean_base_url(os.getenv("SUPABASE_URL", ""))
    return f"{base}/rest/v1/solicitudes_licencia" if base else ""


def _support_requests_table_url() -> str:
    base = _clean_base_url(os.getenv("SUPABASE_URL", ""))
    return f"{base}/rest/v1/solicitudes_soporte" if base else ""


def _upgrade_requests_table_url() -> str:
    base = _clean_base_url(os.getenv("SUPABASE_URL", ""))
    return f"{base}/rest/v1/solicitudes_upgrade" if base else ""


def _anon_key() -> str:
    return os.getenv("SUPABASE_ANON_KEY", "") or os.getenv("SUPABASE_KEY", "")


def _headers() -> dict[str, str]:
    key = _anon_key()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def is_configured() -> bool:
    return bool(os.getenv("SUPABASE_URL") and _anon_key())


def build_machine_id(raw: str) -> str:
    value = (raw or "").strip().lower()
    return "".join(ch for ch in value if ch.isalnum() or ch in "-_")[:120]


def _read_first(paths: list[str]) -> str:
    for path in paths:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    data = fh.read().strip()
                    if data:
                        return data
        except Exception:
            continue
    return ""


def generate_activation_id(user_hint: str = "") -> tuple[str, dict[str, str]]:
    username = user_hint or getpass.getuser() or os.getenv("USERNAME", "") or os.getenv("USER", "")
    host = platform.node()
    machine_id = _read_first(["/etc/machine-id", "/var/lib/dbus/machine-id"])
    product_uuid = _read_first(["/sys/class/dmi/id/product_uuid"])
    disk_hint = os.path.abspath(os.sep)
    try:
        disk_hint = str(os.stat(disk_hint).st_dev)
    except Exception:
        pass

    raw = "|".join([username, host, machine_id, product_uuid, disk_hint])
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()
    activation_id = f"NXID-{digest[:24]}"
    details = {
        "username": username,
        "host": host,
        "machine_id": machine_id or "(sin machine-id)",
        "disk_hint": disk_hint,
    }
    return activation_id, details


def create_license_request(
    *,
    nombre: str,
    email: str = "",
    whatsapp: str = "",
    activation_id: str,
    producto: str = "",
    plan: str = "BASICA",
    machine_details: dict[str, Any] | None = None,
) -> tuple[bool, str, dict[str, Any] | None]:
    operation = "create_license_request"
    if not is_configured():
        _set_debug(operation=operation, status="not_configured", last_error="not_configured")
        return False, "Falta configurar SUPABASE_URL y SUPABASE_ANON_KEY para enviar solicitudes.", None

    nombre = (nombre or "").strip()
    email = (email or "").strip().lower()
    whatsapp = (whatsapp or "").strip()
    activation_id = build_machine_id(activation_id)
    plan = normalize_plan(plan)
    producto = (producto or _product_default()).strip() or _product_default()

    if not nombre or not activation_id:
        _set_debug(operation=operation, status="validation_error", last_error="missing_required_fields")
        return False, "Nombre e ID del equipo son obligatorios.", None

    payload = {
        "producto": producto,
        "activation_id": activation_id,
        "nombre": nombre,
        "email": email,
        "whatsapp": whatsapp,
        "plan": plan,
        "estado": "pendiente",
        "machine_details": machine_details or {},
    }
    headers = {**_headers(), "Prefer": "return=minimal"}
    try:
        resp = requests.post(_requests_table_url(), headers=headers, json=payload, timeout=12)
    except requests.RequestException:
        _set_debug(operation=operation, status="network_error", last_error="network_error")
        return False, "No se pudo conectar con Supabase para enviar la solicitud.", None
    if resp.status_code >= 300:
        _set_debug(operation=operation, status="http_error", status_code=resp.status_code, last_error=resp.text[:120])
        return False, f"Error al registrar solicitud en Supabase ({resp.status_code}): {resp.text[:240]}", None

    _set_debug(operation=operation, status="ok", status_code=resp.status_code)
    return True, "Solicitud enviada correctamente. El administrador debe aprobarla.", None


def create_support_request(
    *,
    nombre: str,
    email: str,
    mensaje: str,
    whatsapp: str = "",
    motivo: str = "consulta",
    producto: str = "",
    app_version: str = "",
    negocio: str = "",
    plan: str = "",
    user_name: str = "",
    technical_details: dict[str, Any] | None = None,
) -> tuple[bool, str, dict[str, Any] | None]:
    operation = "create_support_request"
    if not is_configured():
        _set_debug(operation=operation, status="not_configured", last_error="not_configured")
        return False, "Falta configurar SUPABASE_URL y SUPABASE_ANON_KEY para enviar solicitudes de soporte.", None

    nombre = (nombre or "").strip()
    email = (email or "").strip().lower()
    whatsapp = (whatsapp or "").strip()
    motivo = (motivo or "consulta").strip().lower()
    mensaje = (mensaje or "").strip()
    producto = (producto or _product_default()).strip() or _product_default()

    motivos_validos = {"consulta", "error", "licencia", "actualizacion", "respaldo", "otro"}
    if motivo not in motivos_validos:
        motivo = "consulta"

    if not nombre or not email or not mensaje:
        _set_debug(operation=operation, status="validation_error", last_error="missing_required_fields")
        return False, "Nombre, email y mensaje son obligatorios.", None

    payload = {
        "producto": producto,
        "app_version": app_version,
        "negocio": negocio,
        "nombre": nombre,
        "email": email,
        "whatsapp": whatsapp,
        "motivo": motivo,
        "mensaje": mensaje,
        "plan": plan,
        "user_name": user_name,
        "estado": "pendiente",
        "technical_details": technical_details or {},
    }
    headers = {**_headers(), "Prefer": "return=minimal"}
    try:
        resp = requests.post(_support_requests_table_url(), headers=headers, json=payload, timeout=12)
    except requests.RequestException:
        _set_debug(operation=operation, status="network_error", last_error="network_error")
        return False, "No se pudo conectar con Supabase para enviar la solicitud de soporte.", None
    if resp.status_code >= 300:
        _set_debug(operation=operation, status="http_error", status_code=resp.status_code, last_error=resp.text[:120])
        return False, f"Error al registrar solicitud de soporte ({resp.status_code}): {resp.text[:240]}", None

    _set_debug(operation=operation, status="ok", status_code=resp.status_code)
    return True, "Solicitud de soporte enviada correctamente.", None


def create_upgrade_request(data: dict[str, Any]) -> dict[str, Any]:
    operation = "create_upgrade_request"
    if not is_configured():
        _set_debug(operation=operation, status="not_configured", last_error="not_configured")
        return {"ok": False, "message": "Falta configurar SUPABASE_URL y SUPABASE_ANON_KEY para enviar solicitudes."}

    payload = dict(data or {})
    payload["producto"] = str(payload.get("producto") or _product_default()).strip() or _product_default()
    payload["license_key"] = str(payload.get("license_key") or "").strip()
    payload["activation_id"] = build_machine_id(payload.get("activation_id") or "")
    payload["nombre"] = str(payload.get("nombre") or "").strip() or "Administrador"
    payload["email"] = str(payload.get("email") or "").strip().lower()
    payload["whatsapp"] = str(payload.get("whatsapp") or "").strip()
    payload["plan_actual"] = normalize_plan(payload.get("plan_actual") or "")
    payload["plan_solicitado"] = normalize_plan(payload.get("plan_solicitado") or "")
    payload["estado"] = "pendiente"
    payload["machine_details"] = payload.get("machine_details") or {}

    if payload["plan_actual"] not in {"BASICA", "PRO"}:
        _set_debug(operation=operation, status="validation_error", last_error="invalid_current_plan")
        return {"ok": False, "message": "El plan actual no admite solicitudes de actualización."}

    expected_target = "PRO" if payload["plan_actual"] == "BASICA" else "MENSUAL_FULL"
    if payload["plan_solicitado"] != expected_target:
        _set_debug(operation=operation, status="validation_error", last_error="invalid_target_plan")
        return {"ok": False, "message": "La actualización solicitada no es válida para el plan actual."}

    if not payload["activation_id"] and not payload["license_key"]:
        _set_debug(operation=operation, status="validation_error", last_error="missing_activation_id_and_license_key")
        return {"ok": False, "message": "La solicitud requiere al menos un ID de equipo o una licencia asociada."}

    headers = {**_headers(), "Prefer": "return=minimal"}
    try:
        resp = requests.post(_upgrade_requests_table_url(), headers=headers, json=payload, timeout=12)
    except requests.RequestException:
        _set_debug(operation=operation, status="network_error", last_error="network_error")
        return {"ok": False, "message": "No se pudo conectar con Supabase para enviar la solicitud."}

    if resp.status_code >= 300:
        _set_debug(operation=operation, status="http_error", status_code=resp.status_code, last_error=resp.text[:120])
        return {"ok": False, "message": f"Error al registrar solicitud de upgrade ({resp.status_code})."}

    _set_debug(operation=operation, status="ok", status_code=resp.status_code)
    return {"ok": True, "message": "Solicitud de actualización enviada."}


def activate_license(license_key: str, machine_id: str, producto: str = "") -> tuple[bool, str, dict[str, Any] | None]:
    operation = "activate_license"
    if not is_configured():
        _set_debug(operation=operation, status="not_configured", last_error="not_configured")
        return False, "Falta configurar SUPABASE_URL y SUPABASE_ANON_KEY.", None

    key = (license_key or "").strip()
    machine_id = build_machine_id(machine_id)
    producto = (producto or _product_default()).strip() or _product_default()
    if not key or not machine_id:
        _set_debug(operation=operation, status="validation_error", last_error="missing_required_fields")
        return False, "La clave y el ID de maquina son obligatorios.", None

    params = {"license_key": f"eq.{key}", "producto": f"eq.{producto}", "select": "*"}
    try:
        resp = requests.get(_table_url(), headers=_headers(), params=params, timeout=12)
    except requests.RequestException:
        _set_debug(operation=operation, status="network_error", last_error="network_error")
        return False, "No se pudo conectar con Supabase para consultar la licencia.", None
    if resp.status_code >= 300:
        _set_debug(operation=operation, status="http_error", status_code=resp.status_code, last_error=resp.text[:120])
        return False, f"Error consultando licencia ({resp.status_code}): {resp.text[:240]}", None

    rows = resp.json() if resp.text else []
    if not rows:
        _set_debug(operation=operation, status="not_found", status_code=resp.status_code, last_error="not_found")
        return False, "No existe esa licencia para este producto.", None

    row = rows[0]
    if not row.get("activa", True):
        _set_debug(operation=operation, status="inactive", status_code=resp.status_code, last_error="inactive")
        return False, "La licencia esta desactivada/revocada.", row

    db_hwid = row.get("hwid") or ""
    db_hwids = row.get("hwids") or []
    if isinstance(db_hwids, str):
        db_hwids = [db_hwids] if db_hwids else []
    max_devices = max(int(row.get("max_devices") or 1), 1)

    if db_hwid == machine_id or machine_id in db_hwids:
        update_hwids = sorted(set([*db_hwids, machine_id]))
    elif not db_hwid or len(db_hwids) < max_devices:
        update_hwids = sorted(set([*db_hwids, machine_id]))[:max_devices]
    else:
        _set_debug(operation=operation, status="limit_reached", status_code=resp.status_code, last_error="device_limit")
        return False, "La licencia alcanzo el limite de dispositivos.", row

    upd = requests.patch(
        _table_url(),
        headers={**_headers(), "Prefer": "return=representation"},
        params={"id": f"eq.{row['id']}"},
        json={"hwid": db_hwid or machine_id, "hwids": update_hwids},
        timeout=12,
    )
    if upd.status_code >= 300:
        _set_debug(operation=operation, status="patch_error", status_code=upd.status_code, last_error=upd.text[:120])
        return False, f"Licencia encontrada, pero no se pudo actualizar HWID ({upd.status_code}).", row

    updated_rows = upd.json() if upd.text else [row]
    updated = updated_rows[0] if updated_rows else row
    _set_debug(operation=operation, status="ok", status_code=upd.status_code)
    return True, "Licencia activada correctamente para esta maquina.", updated
