import os


TIER_ALIASES = {
    "BASIC": "BASICA",
    "BASICO": "BASICA",
    "ALM_BASICA": "BASICA",
    "PRO": "PRO",
    "ALM_PRO": "PRO",
    "FULL": "MENSUAL_FULL",
    "MENSUAL": "MENSUAL_FULL",
    "MENSUAL_FULL": "MENSUAL_FULL",
    "ALM_FULL": "MENSUAL_FULL",
}


PLANES = {
    "DEMO": {
        "core",
        "productos",
        "ventas",
        "stock",
        "caja",
        "clientes",
        "proveedores",
        "compras",
        "gastos",
        "reportes",
        "unidades",
        "openfood",
    },
    "BASICA": {
        "core",
        "productos",
        "stock",
        "ventas",
        "caja",
        "clientes",
        "proveedores",
        "gastos",
        "unidades",
    },
    "PRO": {
        "core",
        "productos",
        "stock",
        "ventas",
        "caja",
        "clientes",
        "proveedores",
        "gastos",
        "unidades",
        "compras",
        "historial",
        "reportes",
        "export",
        "multiusuario",
        "openfood",
        "analisis",
    },
    "MENSUAL_FULL": {
        "core",
        "productos",
        "stock",
        "ventas",
        "caja",
        "clientes",
        "proveedores",
        "gastos",
        "unidades",
        "compras",
        "historial",
        "reportes",
        "export",
        "multiusuario",
        "openfood",
        "analisis",
        "multinegocio",
        "ia_productos",
        "integraciones",
        "arca_facturacion",
        "backup_sync",
    },
}


def normalize_license_tier(tier: str | None = None, default: str = "DEMO") -> str:
    raw = (tier or default).strip().upper().replace("-", "_").replace(" ", "_")
    normalized = TIER_ALIASES.get(raw, raw)
    return normalized if normalized in PLANES else default


def get_modules_for_tier(tier: str | None = None) -> set[str]:
    tier_key = normalize_license_tier(tier or "DEMO")
    return set(PLANES.get(tier_key, PLANES["DEMO"]))


def get_env_tier() -> str:
    return normalize_license_tier(os.getenv("NEXAR_PLAN", "DEMO"))


def get_env_modules() -> set[str]:
    raw_modules = os.getenv("NEXAR_MODULES", "")
    return {module.strip().lower() for module in raw_modules.split(",") if module.strip()}
