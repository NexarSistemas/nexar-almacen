class LicensingError(Exception):
    """Error base para el sistema de licencias."""

class NetworkError(LicensingError):
    """Error de conexión con el servidor de licencias."""