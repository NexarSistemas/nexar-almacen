from __future__ import annotations

from datetime import date, timedelta


PLAN_DEMO = "DEMO"
PLAN_BASICA = "BASICA"
PLAN_MENSUAL_FULL = "MENSUAL_FULL"

LEGACY_PLAN_ALIASES = {
    "BASIC": PLAN_BASICA,
    "BASICO": PLAN_BASICA,
    "BASICA": PLAN_BASICA,
    "DEMO": PLAN_DEMO,
    "FULL": PLAN_MENSUAL_FULL,
    "MENSUAL": PLAN_MENSUAL_FULL,
    "MENSUAL_FULL": PLAN_MENSUAL_FULL,
    "PRO": PLAN_MENSUAL_FULL,
    "TDA_BASICA": PLAN_BASICA,
    "TDA_PRO": PLAN_MENSUAL_FULL,
}

PLAN_DEFAULTS = {
    PLAN_DEMO: {
        "label": "Demo 30 dias",
        "duration_days": 30,
        "permanent": False,
        "support": False,
        "updates": False,
        "limits": {"productos": None, "clientes": None, "proveedores": None},
    },
    PLAN_BASICA: {
        "label": "Basica permanente",
        "duration_days": None,
        "permanent": True,
        "support": False,
        "updates": False,
        "limits": {"productos": 200, "clientes": 100, "proveedores": 50},
    },
    PLAN_MENSUAL_FULL: {
        "label": "Mensual full",
        "duration_days": 30,
        "permanent": False,
        "support": True,
        "updates": True,
        "limits": {"productos": None, "clientes": None, "proveedores": None},
    },
}


def normalize_plan(value: str | None) -> str:
    raw = (value or PLAN_BASICA).strip().upper().replace("-", "_").replace(" ", "_")
    return LEGACY_PLAN_ALIASES.get(raw, PLAN_BASICA)


def get_plan_defaults(plan: str | None) -> dict:
    normalized = normalize_plan(plan)
    return {"plan": normalized, **PLAN_DEFAULTS[normalized]}


def default_expiration(plan: str | None, issued_at: date | None = None) -> str:
    defaults = get_plan_defaults(plan)
    if defaults["permanent"]:
        return ""

    issued_at = issued_at or date.today()
    days = int(defaults["duration_days"] or 30)
    return (issued_at + timedelta(days=days)).isoformat()


def normalize_license_data(data: dict | None) -> dict:
    data = dict(data or {})
    plan = normalize_plan(data.get("plan") or data.get("tier") or data.get("license_plan"))
    defaults = get_plan_defaults(plan)

    expira = data.get("expira") or data.get("expires_at") or ""
    if plan == PLAN_BASICA:
        expira = ""

    normalized = {
        **data,
        "plan": plan,
        "tier": plan,
        "expira": expira,
        "permanent": defaults["permanent"],
        "support": bool(data.get("support", defaults["support"])),
        "updates": bool(data.get("updates", defaults["updates"])),
        "limits": data.get("limits") or defaults["limits"],
    }
    return normalized
