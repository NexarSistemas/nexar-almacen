"""
license_verifier.py
====================
Verifica la licencia online contra Google Drive al arrancar.

Flujo:
  1. Si la app esta en modo demo -> no hace nada (demo tiene su propio control)
  2. Si tiene licencia activada -> consulta Drive con el machine_id
  3. Descarga el JSON publico y verifica la firma RSA
  4. Si Drive confirma -> actualiza fecha del ultimo chequeo exitoso
  5. Sin internet -> periodo de gracia de 7 dias desde el ultimo chequeo exitoso
  6. Si pasan los 7 dias sin verificar -> vuelve a modo demo (sin borrar datos)

El archivo index_almacen.json en Drive tiene el formato:
  { "ALM-XXXXXXXX-001": "file_id_del_json_publico", ... }

El JSON publico de cada licencia tiene:
  { "license_key": ..., "hardware_id": ..., "type": ...,
    "max_machines": ..., "product": "almacen", "public_signature": ... }

IMPORTANTE: La carpeta publica de Drive debe tener acceso publico de lectura.
El ID del index se configura en database.py como 'license_drive_index_id'.
"""

import urllib.request
import urllib.error
import json
import ssl
import hashlib
import base64
from datetime import date, datetime

# ── Configuracion ─────────────────────────────────────────────────────────────

# ID del archivo index_almacen.json en Drive (carpeta publica)
# Se obtiene del generador la primera vez y se guarda en la DB.
# URL de descarga directa de Google Drive:
_DRIVE_DOWNLOAD = "https://drive.google.com/uc?export=download&id={file_id}"

# Dias de gracia sin conexion antes de revocar
DIAS_GRACIA = 7

# Timeout de conexion en segundos
TIMEOUT = 8


# ── Helpers de red ────────────────────────────────────────────────────────────

def _ssl_ctx():
    """Contexto SSL compatible con PyInstaller."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode    = ssl.CERT_NONE
        return ctx


def _descargar_json(file_id: str) -> dict | None:
    """Descarga y parsea un JSON desde Google Drive por file_id."""
    url = _DRIVE_DOWNLOAD.format(file_id=file_id)
    try:
        req  = urllib.request.Request(url, headers={"User-Agent": "nexaralmacen/1.5.4"})
        resp = urllib.request.urlopen(req, timeout=TIMEOUT, context=_ssl_ctx())
        return json.loads(resp.read().decode())
    except Exception:
        return None


# ── Verificacion RSA (misma implementacion stdlib que en database.py) ─────────

_SHA256_HEADER = bytes([
    0x30,0x31,0x30,0x0d,0x06,0x09,0x60,0x86,0x48,0x01,
    0x65,0x03,0x04,0x02,0x01,0x05,0x00,0x04,0x20
])

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

def _parse_len(data, pos):
    b = data[pos]; pos += 1
    if b < 0x80: return b, pos
    n = b & 0x7f
    return int.from_bytes(data[pos:pos+n], 'big'), pos + n

def _parse_int(data, pos):
    assert data[pos] == 0x02; pos += 1
    l, pos = _parse_len(data, pos)
    return int.from_bytes(data[pos:pos+l], 'big'), pos + l

def _load_pubkey():
    lines = _PUB_KEY_PEM.strip().split(b'\n')
    der   = base64.b64decode(b''.join(l for l in lines if not l.startswith(b'-----')))
    pos = 0
    assert der[pos] == 0x30; pos += 1
    _, pos = _parse_len(der, pos)
    assert der[pos] == 0x30; pos += 1
    al, pos = _parse_len(der, pos); pos += al
    assert der[pos] == 0x03; pos += 1
    _, pos = _parse_len(der, pos); pos += 1
    assert der[pos] == 0x30; pos += 1
    _, pos = _parse_len(der, pos)
    n, pos = _parse_int(der, pos)
    e, _   = _parse_int(der, pos)
    return n, e

def _verificar_firma(message: bytes, signature: bytes) -> bool:
    try:
        n, e = _load_pubkey()
        k = (n.bit_length() + 7) // 8
        if len(signature) != k: return False
        m = pow(int.from_bytes(signature, 'big'), e, n).to_bytes(k, 'big')
        if m[0] != 0x00 or m[1] != 0x01: return False
        sep = m.find(b'\x00', 2)
        if sep < 0 or any(b != 0xFF for b in m[2:sep]): return False
        return m[sep+1:] == _SHA256_HEADER + hashlib.sha256(message).digest()
    except Exception:
        return False


# ── Logica principal ──────────────────────────────────────────────────────────

def verificar_licencia_online(db_module) -> dict:
    """
    Verifica la licencia contra Drive.

    Retorna dict con:
      ok        : bool — True si la licencia es valida
      modo      : 'online_ok' | 'gracia' | 'revocada' | 'demo'
      dias_gracia: int — dias restantes de gracia (si aplica)
      mensaje   : str — descripcion del resultado
    """
    cfg = db_module.get_config()

    # Si esta en demo, no verificar — el demo tiene su propio control
    if cfg.get('demo_mode', '1') == '1':
        return {'ok': True, 'modo': 'demo', 'dias_gracia': 0,
                'mensaje': 'Modo demo activo'}

    machine_id  = db_module.get_machine_id()
    license_key = cfg.get('license_key', '')
    index_id    = cfg.get('license_drive_index_id', '')

    # Sin index_id configurado -> usar gracia (instalacion antigua o sin Drive)
    if not index_id:
        return _evaluar_gracia(db_module, cfg,
            "No hay ID de indice Drive configurado. Usando periodo de gracia.")

    # ── Paso 1: descargar index_almacen.json ──────────────────────────────────
    index = _descargar_json(index_id)
    if index is None:
        return _evaluar_gracia(db_module, cfg,
            "No se pudo conectar con Drive.")

    # ── Paso 2: buscar la licencia en el indice ───────────────────────────────
    file_id = index.get(license_key)
    if not file_id:
        # La licencia no esta en Drive -> revocada
        _revocar(db_module)
        return {'ok': False, 'modo': 'revocada', 'dias_gracia': 0,
                'mensaje': 'Licencia no encontrada en el servidor. Contacta al desarrollador.'}

    # ── Paso 3: descargar el JSON de la licencia ──────────────────────────────
    lic_data = _descargar_json(file_id)
    if lic_data is None:
        return _evaluar_gracia(db_module, cfg,
            "No se pudo descargar la licencia desde Drive.")

    # ── Paso 4: verificar firma RSA ───────────────────────────────────────────
    sig_hex = lic_data.get('signature') or lic_data.get('public_signature', '')
    if not sig_hex:
        _revocar(db_module)
        return {'ok': False, 'modo': 'revocada', 'dias_gracia': 0,
                'mensaje': 'Licencia en Drive no tiene firma digital valida.'}

    try:
        signature = bytes.fromhex(sig_hex)
    except ValueError:
        _revocar(db_module)
        return {'ok': False, 'modo': 'revocada', 'dias_gracia': 0,
                'mensaje': 'Firma digital corrupta en Drive.'}

    is_multi = 'hardware_ids' in lic_data
    if is_multi:
        payload_dict = {
            'hardware_ids': sorted(lic_data['hardware_ids']),
            'license_key':  lic_data['license_key'],
            'max_machines': lic_data['max_machines'],
            'product':      'almacen',
            'type':         lic_data['type'],
        }
    else:
        payload_dict = {
            'hardware_id':  lic_data.get('hardware_id', ''),
            'license_key':  lic_data['license_key'],
            'max_machines': lic_data['max_machines'],
            'product':      'almacen',
            'type':         lic_data['type'],
        }

    payload_bytes = json.dumps(payload_dict, sort_keys=True).encode()
    if not _verificar_firma(payload_bytes, signature):
        _revocar(db_module)
        return {'ok': False, 'modo': 'revocada', 'dias_gracia': 0,
                'mensaje': 'Firma digital invalida. Licencia alterada o no autorizada.'}

    # ── Paso 5: verificar que esta PC esta autorizada ─────────────────────────
    if is_multi:
        autorizada = machine_id in lic_data.get('hardware_ids', [])
    else:
        autorizada = (machine_id == lic_data.get('hardware_id', ''))

    if not autorizada:
        _revocar(db_module)
        return {'ok': False, 'modo': 'revocada', 'dias_gracia': 0,
                'mensaje': 'Esta computadora no esta autorizada para esta licencia.'}

    # ── Todo OK: actualizar fecha de ultimo chequeo ───────────────────────────
    db_module.set_config({'license_last_check': date.today().isoformat()})
    return {'ok': True, 'modo': 'online_ok', 'dias_gracia': 0,
            'mensaje': 'Licencia verificada correctamente.'}


def _evaluar_gracia(db_module, cfg: dict, motivo: str) -> dict:
    """
    Sin conexion: evalua si estamos dentro del periodo de gracia.
    """
    ultimo_str = cfg.get('license_last_check', '')
    hoy = date.today()

    if not ultimo_str:
        # Nunca se verifico online -> dar gracia desde hoy
        db_module.set_config({'license_last_check': hoy.isoformat()})
        dias_restantes = DIAS_GRACIA
    else:
        try:
            ultimo = date.fromisoformat(ultimo_str)
            dias_pasados   = (hoy - ultimo).days
            dias_restantes = max(0, DIAS_GRACIA - dias_pasados)
        except Exception:
            dias_restantes = DIAS_GRACIA

    if dias_restantes > 0:
        return {
            'ok':          True,
            'modo':        'gracia',
            'dias_gracia': dias_restantes,
            'mensaje':     f'{motivo} Periodo de gracia: {dias_restantes} dias restantes.'
        }
    else:
        _revocar(db_module)
        return {
            'ok':          False,
            'modo':        'revocada',
            'dias_gracia': 0,
            'mensaje':     f'Periodo de gracia vencido. {motivo} Contacta al desarrollador.'
        }


def _revocar(db_module):
    """Vuelve a modo demo sin borrar datos del negocio."""
    db_module.set_config({
        'demo_mode':            '1',
        'license_type':         'DEMO',
        'license_max_machines': '1',
        'license_last_check':   '',
    })
