"""
license_verifier.py
====================
Verifica la licencia online contra Supabase usando el SDK nexar_licencias.
"""

from datetime import date, datetime
import sys
import os

# Añadir el path del SDK unificado
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'nexar_licencias')))
from nexar_licencias import validar_licencia

# ── Configuracion ─────────────────────────────────────────────────────────────
# Dias de gracia sin conexion antes de revocar
DIAS_GRACIA = 7

_PUB_KEY_PEM = (
    b"-----BEGIN PUBLIC KEY-----\n"
    b"MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEApLcG8Uq6+sV4E1mlWY5z\n"
    b"zZC8H2i4EM0s2jGq8XCcVOJipamw+1rvzHSoAjgmtnJCw8+218yR3PXK90NqSguO\n"
    b"9blAfsxswwtlid9RxwPQ1y8jU1LuZd65DeowgGtu+4lrNjeIZqmesarPbgOIMZ3q\n"
    b"PZpurtOUjy74moR5pwGIPQk9TLl685MeyYcDdV9UO0uiiYyxS+yopRvvOrhXJlH0\n"
    b"C5I+KeCqjOLXglTXOXoYFXOUXwWajT/FFjXHabWO/yCA8igXqn+rdt+bPoLBfmYk\n"
    b"0FjjYn2HrwRB8NZ4Lv4pQc30EukM32Nyri80Dak8/dtjNLPrc0wTzAvqeyUDHHKu\n"
    b"dQIDAQAB\n"
    b"-----END PUBLIC KEY-----"
)

# ── Logica principal ──────────────────────────────────────────────────────────

def verificar_licencia_online(db_module) -> dict:
    cfg = db_module.get_config()

    if cfg.get('demo_mode', '1') == '1':
        return {'ok': True, 'modo': 'demo', 'dias_gracia': 0,
                'mensaje': 'Modo demo activo'}

    # Obtenemos la licencia completa guardada (JSON)
    import json
    lic_json = cfg.get('license_data_full', '{}')
    try:
        licencia = json.loads(lic_json)
    except:
        licencia = {"license_key": cfg.get('license_key', ''), "public_signature": cfg.get('license_signature', '')}

    ok = validar_licencia(licencia, _PUB_KEY_PEM.decode(), "almacen", debug=True)

    if not ok:
        _revocar(db_module)
        return {'ok': False, 'modo': 'revocada', 'mensaje': 'Licencia inválida o revocada.'}

    return {'ok': True, 'modo': 'online_ok', 'mensaje': 'Licencia verificada.'}


def _revocar(db_module):
    """Vuelve a modo demo sin borrar datos del negocio."""
    db_module.set_config({
        'demo_mode':            '1',
        'license_type':         'DEMO',
        'license_max_machines': '1',
        'license_last_check':   '',
    })
