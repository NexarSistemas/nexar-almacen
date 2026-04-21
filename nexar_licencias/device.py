import platform
import uuid
import hashlib

def get_hwid():
    data = f"{platform.node()}-{platform.system()}-{uuid.getnode()}"
    return hashlib.sha256(data.encode()).hexdigest()


def get_product_hwid(product_name):
    """
    Devuelve un HWID estable pero aislado por producto.

    La misma PC puede tener Nexar Tienda y Nexar Almacen sin compartir cupo
    accidentalmente, mientras que get_hwid() queda como compatibilidad legacy.
    """
    product = (product_name or "").strip().lower() or "nexar"
    return hashlib.sha256(f"{product}:{get_hwid()}".encode()).hexdigest()
