"""Capa de licencias y modulos para Nexar Almacen."""

from .permisos import get_modulos_activos, get_modulos_debug_info, modulo_activo, require_modulo
from .planes import PLANES, get_modules_for_tier, normalize_license_tier

__all__ = [
    "PLANES",
    "get_modules_for_tier",
    "get_modulos_activos",
    "get_modulos_debug_info",
    "modulo_activo",
    "normalize_license_tier",
    "require_modulo",
]
