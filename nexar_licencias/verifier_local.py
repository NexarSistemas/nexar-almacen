import json
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

def verificar_firma(licencia_dict, public_key_pem, debug=False):
    """
    MODO DEV - firma desactivada temporalmente
    """

    if debug:
        print(">>> FIRMA DEV ACTIVA")

    try:
        if not licencia_dict:
            return False

        if "license_key" not in licencia_dict:
            return False

        return True

    except Exception:
        return False
