import importlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from flask import abort

from licensing.planes import get_env_modules, get_env_tier, get_modules_for_tier, normalize_license_tier


logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent.parent
VENDORED_SDK_PACKAGE = BASE_DIR / "nexar_licencias"
SIBLING_SDK_REPO_PATH = BASE_DIR.parent / "nexar_licencias"
_last_modules_source = "fallback_demo"
_last_error = ""


def _set_last_source(source: str) -> None:
    global _last_modules_source
    _last_modules_source = source


def _set_last_error(message: str) -> None:
    global _last_error
    _last_error = message


def _normalize_modules(value: Any) -> set[str]:
    if not value:
        return set()
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return set()
        if raw.startswith("["):
            try:
                value = json.loads(raw)
            except Exception:
                return set()
        else:
            return {module.strip().lower() for module in raw.split(",") if module.strip()}
    try:
        return {str(module).strip().lower() for module in value if str(module).strip()}
    except TypeError:
        return set()


def _load_database_module():
    import database as db

    return db


def _get_modules_from_db() -> set[str]:
    try:
        db = _load_database_module()
        return _normalize_modules(db.get_license_modules_from_db())
    except Exception as exc:
        logger.debug("No se pudieron leer modulos persistidos: %s", exc)
        _set_last_error(str(exc))
        return set()


def _get_tier_from_db() -> str:
    try:
        db = _load_database_module()
        return normalize_license_tier(db.get_license_tier_from_db(), default="DEMO")
    except Exception as exc:
        logger.debug("No se pudo leer tier desde DB: %s", exc)
        _set_last_error(str(exc))
        return "DEMO"


def _ensure_sdk_path() -> None:
    candidates = []
    if VENDORED_SDK_PACKAGE.exists():
        candidates.append(BASE_DIR)
    if SIBLING_SDK_REPO_PATH.exists():
        candidates.append(SIBLING_SDK_REPO_PATH)
    for path in candidates:
        sdk_path = str(path)
        if sdk_path not in sys.path:
            sys.path.append(sdk_path)


def _get_sdk_modules() -> set[str]:
    try:
        _ensure_sdk_path()
        sdk = importlib.import_module("nexar_licencias")
    except Exception as exc:
        logger.debug("SDK nexar_licencias no disponible para modulos: %s", exc)
        return set()

    candidates = (
        "get_modulos_activos",
        "obtener_modulos_activos",
        "get_active_modules",
        "active_modules",
    )
    for attr_name in candidates:
        attr = getattr(sdk, attr_name, None)
        try:
            value = attr() if callable(attr) else attr
        except Exception:
            continue
        modules = _normalize_modules(value)
        if modules:
            return modules
    return set()


def get_modulos_activos() -> set[str]:
    mode = os.getenv("NEXAR_LICENSE_MODE", "prod").strip().lower()
    if mode == "dev":
        env_tier = get_env_tier()
        env_modules = get_modules_for_tier(env_tier) | get_env_modules()
        _set_last_source("env")
        return env_modules or {"core"}

    db = _load_database_module()
    license_info = db.get_license_info()
    tier = str(license_info.get("tier", "DEMO")).strip().upper()
    if tier == "SIN_PLAN":
        _set_last_source("db_effective_none")
        return set()

    tier_modules = get_modules_for_tier(tier)
    persisted_modules = _get_modules_from_db()
    if persisted_modules:
        effective_modules = persisted_modules & tier_modules
        if effective_modules:
            source = "db_modules" if effective_modules == persisted_modules else "db_modules_filtered"
            _set_last_source(source)
            return effective_modules

    tier_modules = get_modules_for_tier(tier)
    if tier_modules:
        _set_last_source("db_tier")
        return tier_modules

    env_tier = get_env_tier()
    env_modules = get_modules_for_tier(env_tier) | get_env_modules()
    if env_modules:
        _set_last_source("env")
        return env_modules

    _set_last_source("fallback_demo")
    return {"core"}


def get_modulos_debug_info() -> dict[str, object]:
    mode = os.getenv("NEXAR_LICENSE_MODE", "prod").strip().lower()
    persisted_modules = sorted(_get_modules_from_db())
    db_tier = _get_tier_from_db()
    env_tier = get_env_tier()
    env_extra = sorted(get_env_modules())
    sdk_modules = sorted(_get_sdk_modules())
    final_modules = sorted(get_modulos_activos())
    tier_for_final = env_tier if mode == "dev" else db_tier
    return {
        "mode": mode,
        "tier": tier_for_final,
        "db_tier": db_tier,
        "env_tier": env_tier,
        "tier_modules": sorted(get_modules_for_tier(tier_for_final)),
        "persisted_modules": persisted_modules,
        "env_modules": env_extra,
        "sdk_modules": sdk_modules,
        "final_modules": final_modules,
        "final_source": _last_modules_source,
        "aliases": {
            "BASIC": "BASICA",
            "BASICO": "BASICA",
            "ALM_BASICA": "BASICA",
            "PRO": "PRO",
            "ALM_PRO": "PRO",
            "FULL": "MENSUAL_FULL",
            "MENSUAL": "MENSUAL_FULL",
            "MENSUAL_FULL": "MENSUAL_FULL",
            "ALM_FULL": "MENSUAL_FULL",
        },
        "last_error": _last_error,
    }


def modulo_activo(nombre: str) -> bool:
    return str(nombre).strip().lower() in get_modulos_activos()


def require_modulo(nombre: str) -> bool:
    if not modulo_activo(nombre):
        abort(403)
    return True
