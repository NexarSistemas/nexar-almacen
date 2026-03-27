"""
services/openfood_importer.py
─────────────────────────────
Módulo de importación de productos desde OpenFoodFacts.
Diseñado para usarse en forma independiente de Flask.
Toda la lógica de red, filtrado e inserción vive aquí.

Columnas relevantes del schema existente
-----------------------------------------
productos : id, codigo_interno, codigo_barras TEXT, descripcion TEXT,
            marca TEXT, categoria TEXT, costo REAL, precio_venta REAL, ...
categorias: id INTEGER, nombre TEXT UNIQUE, activa INTEGER

Reglas estrictas
-----------------
• Nunca modificar: costo, precio_venta, stock, categoria (en update).
• Nunca lanzar error por UNIQUE constraint.
• Usar siempre transacciones explícitas y cerrar la conexión.
"""

import sqlite3
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import logging
import os
import ssl

# ─── Logging ─────────────────────────────────────────────────────────────────
logger = logging.getLogger("openfood_importer")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[OFI] %(levelname)s %(message)s"))
    logger.addHandler(_h)
logger.setLevel(logging.INFO)

# ─── Configuración ────────────────────────────────────────────────────────────
API_BASE    = "https://world.openfoodfacts.org/cgi/search.pl"
API_TIMEOUT = 45           # segundos por request (OFF puede tardar en primera respuesta)
API_RETRIES = 3            # reintentos automáticos por página
PAGE_SIZE   = 100          # max permitido por OFF
DELAY_S     = 0.5          # pausa entre páginas (respeto al rate-limit)
USER_AGENT  = "nexaralmacen/1.5.1 (contacto: nexarsistemas@outlook.com.ar)"

def _ssl_context():
    """Contexto SSL que funciona tanto en Python normal como en exe PyInstaller."""
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
        return ctx
    except Exception:
        # Fallback: deshabilitar verificación SSL
        # (ocurre en exe PyInstaller donde no hay certs del sistema)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

# Ruta de la base de datos — misma lógica que database.py:
# 1. Variable de entorno ALMACEN_DB_PATH (instaladores Windows/deb y exe PyInstaller)
# 2. En Windows sin env var: %APPDATA%\nexaralmacen\almacen.db
# 3. Fallback: junto al proyecto (portable/Linux)
def _resolve_db_path() -> str:
    env = os.environ.get("ALMACEN_DB_PATH", "")
    if env:
        return env
    if os.name == "nt":
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        data_dir = os.path.join(appdata, "nexaralmacen")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "almacen.db")
    _HERE = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(_HERE, "..", "almacen.db")

DB_PATH = _resolve_db_path()


# ─── Mapeo OpenFoodFacts → categorías del sistema ────────────────────────────
# Clave: fragmento en minúsculas que puede aparecer en categories_tags de OFF
# Valor: nombre exacto de la categoría en la tabla `categorias`
_CAT_MAP = [
    # (fragmento_off,                 categoria_sistema)          # orden: más específico primero
    ("baby",                         "Otros"),
    ("tobacco",                      "Tabaco / Cigarrillos"),
    ("cigarette",                    "Tabaco / Cigarrillos"),
    ("pet-food",                     "Mascotas"),
    ("pet food",                     "Mascotas"),
    ("dog",                          "Mascotas"),
    ("cat-food",                     "Mascotas"),
    ("frozen",                       "Congelados"),
    ("helado",                       "Congelados"),
    ("ice cream",                    "Congelados"),
    ("alcohol",                      "Bebidas Alcohólicas"),
    ("beer",                         "Bebidas Alcohólicas"),
    ("wine",                         "Bebidas Alcohólicas"),
    ("spirits",                      "Bebidas Alcohólicas"),
    ("cervez",                       "Bebidas Alcohólicas"),
    ("fernet",                       "Bebidas Alcohólicas"),
    ("vino",                         "Bebidas Alcohólicas"),
    ("snack",                        "Snacks / Aperitivos"),
    ("chip",                         "Snacks / Aperitivos"),
    ("palito",                       "Snacks / Aperitivos"),
    ("candy",                        "Golosinas / Confitería"),
    ("chocolate",                    "Golosinas / Confitería"),
    ("golosina",                     "Golosinas / Confitería"),
    ("caramel",                      "Golosinas / Confitería"),
    ("alfajor",                      "Golosinas / Confitería"),
    ("biscuit",                      "Golosinas / Confitería"),
    ("galletita",                    "Golosinas / Confitería"),
    ("cookie",                       "Golosinas / Confitería"),
    ("cake",                         "Golosinas / Confitería"),
    ("cereal",                       "Cereales / Harinas / Pastas"),
    ("flour",                        "Cereales / Harinas / Pastas"),
    ("pasta",                        "Cereales / Harinas / Pastas"),
    ("rice",                         "Cereales / Harinas / Pastas"),
    ("arroz",                        "Cereales / Harinas / Pastas"),
    ("harina",                       "Cereales / Harinas / Pastas"),
    ("fideo",                        "Cereales / Harinas / Pastas"),
    ("oil",                          "Aceites / Condimentos / Salsas"),
    ("sauce",                        "Aceites / Condimentos / Salsas"),
    ("condiment",                    "Aceites / Condimentos / Salsas"),
    ("vinegar",                      "Aceites / Condimentos / Salsas"),
    ("mayonnaise",                   "Aceites / Condimentos / Salsas"),
    ("ketchup",                      "Aceites / Condimentos / Salsas"),
    ("mustard",                      "Aceites / Condimentos / Salsas"),
    ("aceite",                       "Aceites / Condimentos / Salsas"),
    ("salsa",                        "Aceites / Condimentos / Salsas"),
    ("spice",                        "Aceites / Condimentos / Salsas"),
    ("seasoning",                    "Aceites / Condimentos / Salsas"),
    ("canned",                       "Enlatados / Conservas"),
    ("conserva",                     "Enlatados / Conservas"),
    ("preserve",                     "Enlatados / Conservas"),
    ("tomato",                       "Enlatados / Conservas"),
    ("legume",                       "Enlatados / Conservas"),
    ("bean",                         "Enlatados / Conservas"),
    ("legumbre",                     "Enlatados / Conservas"),
    ("meat",                         "Carnes"),
    ("beef",                         "Carnes"),
    ("chicken",                      "Carnes"),
    ("pork",                         "Carnes"),
    ("poultry",                      "Carnes"),
    ("carne",                        "Carnes"),
    ("ham",                          "Fiambres (x peso)"),
    ("sausage",                      "Fiambres (x peso)"),
    ("cold-cut",                     "Fiambres (x peso)"),
    ("delicatessen",                 "Fiambres (x peso)"),
    ("jamón",                        "Fiambres (x peso)"),
    ("salame",                       "Fiambres (x peso)"),
    ("cheese",                       "Fiambres (x peso)"),
    ("queso",                        "Fiambres (x peso)"),
    ("dairy",                        "Lácteos"),
    ("milk",                         "Lácteos"),
    ("yogurt",                       "Lácteos"),
    ("butter",                       "Lácteos"),
    ("cream",                        "Lácteos"),
    ("lacteo",                       "Lácteos"),
    ("leche",                        "Lácteos"),
    ("bread",                        "Pan / Panadería (x peso)"),
    ("bakery",                       "Pan / Panadería (x peso)"),
    ("pan",                          "Pan / Panadería (x peso)"),
    ("panaderia",                    "Pan / Panadería (x peso)"),
    ("infusion",                     "Infusiones"),
    ("tea",                          "Infusiones"),
    ("coffee",                       "Infusiones"),
    ("yerba",                        "Infusiones"),
    ("mate",                         "Infusiones"),
    ("herbal",                       "Infusiones"),
    ("juice",                        "Bebidas"),
    ("water",                        "Bebidas"),
    ("soda",                         "Bebidas"),
    ("beverage",                     "Bebidas"),
    ("drink",                        "Bebidas"),
    ("bebida",                       "Bebidas"),
    ("gaseosa",                      "Bebidas"),
    ("agua",                         "Bebidas"),
    ("jugo",                         "Bebidas"),
    ("cleaning",                     "Limpieza del Hogar"),
    ("detergent",                    "Limpieza del Hogar"),
    ("hygiene",                      "Higiene Personal"),
    ("shampoo",                      "Higiene Personal"),
    ("soap",                         "Higiene Personal"),
    ("toothpaste",                   "Higiene Personal"),
    ("deodorant",                    "Higiene Personal"),
    ("paper",                        "Papel / Descartables"),
    ("tissue",                       "Papel / Descartables"),
    ("diet",                         "Dietética / Naturales"),
    ("organic",                      "Dietética / Naturales"),
    ("natural",                      "Dietética / Naturales"),
    ("fruit",                        "Verduras / Frutas (x peso)"),
    ("vegetable",                    "Verduras / Frutas (x peso)"),
    ("fruta",                        "Verduras / Frutas (x peso)"),
    ("verdura",                      "Verduras / Frutas (x peso)"),
    ("sugar",                        "No Perecederos"),
    ("salt",                         "No Perecederos"),
    ("azúcar",                       "No Perecederos"),
    ("sal",                          "No Perecederos"),
]


def _map_category(categories_tags: list) -> str:
    """
    Convierte la lista de tags de OFF al nombre de categoría del sistema.
    Devuelve 'Sin Clasificar' si ningún tag coincide.
    """
    if not categories_tags:
        return "Sin Clasificar"
    # Unir todos los tags en un solo string en minúsculas para búsqueda simple
    tags_str = " ".join(t.lower() for t in categories_tags)
    for fragment, cat_name in _CAT_MAP:
        if fragment in tags_str:
            return cat_name
    return "Sin Clasificar"


# ─── Conexión DB ──────────────────────────────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    """Abre conexión a almacen.db con row_factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _ensure_category(cursor: sqlite3.Cursor, nombre: str) -> str:
    """
    Garantiza que la categoría existe en la tabla categorias.
    Si no existe la crea. Devuelve el nombre normalizado.
    La columna `categoria` en productos es TEXT (nombre, no ID).
    """
    row = cursor.execute(
        "SELECT nombre FROM categorias WHERE nombre = ?", (nombre,)
    ).fetchone()
    if not row:
        cursor.execute(
            "INSERT INTO categorias (nombre, activa) VALUES (?, 1)", (nombre,)
        )
        logger.debug("Nueva categoría creada: %s", nombre)
    return nombre


def _next_codigo_interno(cursor: sqlite3.Cursor) -> str:
    """
    Genera el siguiente código PRD-XXXX sincronizado con lo que ya existe
    en la tabla para evitar colisiones UNIQUE.
    """
    row = cursor.execute(
        "SELECT codigo_interno FROM productos "
        "WHERE codigo_interno LIKE 'PRD-%' "
        "ORDER BY CAST(SUBSTR(codigo_interno, 5) AS INTEGER) DESC "
        "LIMIT 1"
    ).fetchone()
    if row:
        try:
            n = int(row["codigo_interno"].split("-")[1]) + 1
        except (IndexError, ValueError):
            n = 1
    else:
        n = 1
    return f"PRD-{n:04d}"


# ─── Fetcher HTTP ─────────────────────────────────────────────────────────────

def _fetch_page(page: int, page_size: int = PAGE_SIZE,
                timeout: int = API_TIMEOUT) -> dict | None:
    """
    Descarga una página de resultados de la API de OpenFoodFacts.
    Filtra por Argentina. Devuelve el dict JSON o None si falla.
    """
    params = urllib.parse.urlencode({
        "action":         "process",
        "json":           "1",
        "countries_tags": "argentina",
        "page_size":      page_size,
        "page":           page,
        "fields":         "code,product_name,product_name_es,brands,categories_tags",
        "sort_by":        "unique_scans_n",   # primero los más escaneados
    })
    url = f"{API_BASE}?{params}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT}
    )
    ctx = _ssl_context()
    for attempt in range(1, API_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                raw = resp.read()
            return json.loads(raw)
        except urllib.error.URLError as exc:
            logger.warning("Red (intento %d/%d) pag %d: %s", attempt, API_RETRIES, page, exc)
        except json.JSONDecodeError as exc:
            logger.warning("JSON invalido pag %d: %s", page, exc)
            return None
        except Exception as exc:
            logger.warning("Error (intento %d/%d) pag %d: %s", attempt, API_RETRIES, page, exc)
        if attempt < API_RETRIES:
            time.sleep(2 * attempt)
    return None


# ─── Prefijos EAN de Argentina ────────────────────────────────────────────────
# AFIP/GS1 Argentina asignó los prefijos 779 y 780
_AR_PREFIXES = ("779", "780")

# Longitud mínima/máxima de barcode aceptado
_BC_MIN_LEN = 8
_BC_MAX_LEN = 14

# Caracteres "útiles" mínimos en la descripción
_NAME_MIN_CHARS = 3   # al menos 3 letras/números reales

import re as _re

def _is_garbage_name(name: str, barcode: str) -> bool:
    """
    Devuelve True si la descripción es basura y debe descartarse.
    Casos detectados:
      1. El nombre ES el código de barras (igual o contenido como único token)
      2. Solo caracteres especiales / guiones / puntos / espacios
      3. Demasiado corto (menos de _NAME_MIN_CHARS letras reales)
      4. Más del 60% son caracteres no alfanuméricos
    """
    # Caso 1: el nombre es literalmente el barcode
    if name.strip() == barcode.strip():
        return True
    # Caso 1b: el nombre contiene solo el barcode (con espacios alrededor)
    if _re.fullmatch(r"[\s]*" + _re.escape(barcode) + r"[\s]*", name):
        return True

    # Extraer solo letras y números
    alphanums = _re.sub(r"[^a-zA-Z0-9áéíóúüñÁÉÍÓÚÜÑ]", "", name)

    # Caso 2 y 3: sin suficientes caracteres alfanuméricos reales
    if len(alphanums) < _NAME_MIN_CHARS:
        return True

    # Caso 4: más del 60% son caracteres especiales
    ratio_special = 1 - (len(alphanums) / max(len(name), 1))
    if ratio_special > 0.60:
        return True

    return False


def _filter_product(raw: dict) -> dict | None:
    """
    Valida que el producto tenga los campos obligatorios y pase los filtros
    de calidad. Devuelve un dict limpio o None si debe descartarse.

    Filtros aplicados
    -----------------
    · Barcode numérico de longitud 8-14
    · Barcode con prefijo argentino 779 o 780
    · product_name no vacío
    · brands no vacío
    · Descripción no es basura (no es el barcode, no son solo símbolos)
    """
    barcode = str(raw.get("code", "")).strip()

    # ── Validar barcode ──────────────────────────────────────────────────────
    if not barcode:
        return None
    if not barcode.isdigit():
        return None
    if not (_BC_MIN_LEN <= len(barcode) <= _BC_MAX_LEN):
        return None
    # Solo prefijos argentinos
    if not barcode.startswith(_AR_PREFIXES):
        return None

    # ── Validar nombre ───────────────────────────────────────────────────────
    name = (
        raw.get("product_name_es", "")  # preferir español
        or raw.get("product_name", "")
        or ""
    ).strip()
    if not name:
        return None

    # Descartar nombres basura
    if _is_garbage_name(name, barcode):
        return None

    # ── Validar marca ────────────────────────────────────────────────────────
    brands_raw = raw.get("brands", "") or ""
    brand = brands_raw.split(",")[0].strip()
    if not brand:
        return None

    category_tags = raw.get("categories_tags", []) or []
    category = _map_category(category_tags)

    return {
        "barcode":  barcode,
        "name":     name,
        "brand":    brand,
        "category": category,
    }


# ─── Blacklist helper ────────────────────────────────────────────────────────

def _load_blacklist(cursor: sqlite3.Cursor) -> set:
    """
    Carga todos los barcodes bloqueados desde la tabla barcode_blacklist.
    Retorna un set vacío si la tabla no existe todavía (DBs antiguas).
    """
    try:
        rows = cursor.execute("SELECT barcode FROM barcode_blacklist").fetchall()
        return {r["barcode"] for r in rows}
    except Exception:
        return set()


# ─── Función principal: importación inicial ───────────────────────────────────

def import_products(limit: int = 350, timeout: int = API_TIMEOUT) -> dict:
    """
    Importa productos desde OpenFoodFacts hasta insertar `limit` productos
    válidos nuevos, o hasta que la API no tenga más páginas.

    Parámetros
    ----------
    limit   : mínimo de productos nuevos a insertar (default 350)
    timeout : segundos de espera por request HTTP (default 15)

    Devuelve
    --------
    dict con claves: inserted, skipped, pages_fetched, errors
    """
    logger.info("Iniciando importación — objetivo: %d productos", limit)

    stats = {
        "inserted":     0,
        "skipped":      0,   # ya existían (mismo barcode)
        "pages_fetched": 0,
        "errors":       0,
    }

    conn = _get_conn()
    try:
        cursor = conn.cursor()
        page = 1

        # Cargar blacklist una sola vez para evitar consultas repetidas
        blacklist = _load_blacklist(cursor)
        logger.info("Lista negra cargada: %d barcodes bloqueados", len(blacklist))

        while stats["inserted"] < limit:
            logger.info(
                "Página %d — insertados hasta ahora: %d/%d",
                page, stats["inserted"], limit
            )
            data = _fetch_page(page, timeout=timeout)
            stats["pages_fetched"] += 1

            if not data:
                stats["errors"] += 1
                logger.warning("Sin datos en página %d, se detiene.", page)
                break

            products_raw = data.get("products", [])
            if not products_raw:
                logger.info("Página %d vacía — no hay más resultados.", page)
                break

            for raw in products_raw:
                p = _filter_product(raw)
                if not p:
                    continue

                # ── ¿Está en la lista negra? ─────────────────────────────────
                if p["barcode"] in blacklist:
                    stats["skipped"] += 1
                    continue

                # ── ¿Ya existe en la DB? ─────────────────────────────────────
                existing = cursor.execute(
                    "SELECT id FROM productos WHERE codigo_barras = ?",
                    (p["barcode"],)
                ).fetchone()

                if existing:
                    stats["skipped"] += 1
                    continue

                # ── Garantizar categoría ─────────────────────────────────────
                cat_name = _ensure_category(cursor, p["category"])

                # ── Generar código interno ───────────────────────────────────
                codigo = _next_codigo_interno(cursor)

                # ── Insertar ─────────────────────────────────────────────────
                try:
                    cursor.execute(
                        """
                        INSERT INTO productos
                            (codigo_interno, codigo_barras, descripcion, marca,
                             categoria, unidad, por_peso, costo, precio_venta,
                             iva, activo)
                        VALUES (?, ?, ?, ?, ?, 'Unidad', 0, 0, 0, '21%', 1)
                        """,
                        (codigo, p["barcode"], p["name"], p["brand"], cat_name)
                    )
                    # Crear fila en stock para que aparezca en la vista de Stock
                    new_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT OR IGNORE INTO stock "                        "(producto_id, stock_actual, stock_minimo, stock_maximo) "                        "VALUES (?, 0, 5, 50)",
                        (new_id,)
                    )
                    stats["inserted"] += 1
                except sqlite3.IntegrityError:
                    # UNIQUE violation (codigo_interno) — reintentar con +1
                    # (edge case: carrera entre dos inserciones en la misma sesión)
                    stats["skipped"] += 1
                    continue

                # Salir del loop si ya alcanzamos el límite
                if stats["inserted"] >= limit:
                    break

            page += 1
            time.sleep(DELAY_S)

        conn.commit()
        logger.info(
            "Importación completa — insertados: %d | ya existían: %d | "
            "páginas: %d | errores: %d",
            stats["inserted"], stats["skipped"],
            stats["pages_fetched"], stats["errors"]
        )

    except Exception as exc:
        conn.rollback()
        logger.error("Error fatal durante la importación: %s", exc, exc_info=True)
        raise
    finally:
        conn.close()

    return stats


# ─── Función de actualización ─────────────────────────────────────────────────

def update_products(max_pages: int | None = None,
                    timeout: int = API_TIMEOUT) -> dict:
    """
    Agrega productos nuevos y actualiza nombre/marca de los existentes.

    Reglas estrictas
    ----------------
    · Si el barcode YA existe → actualizar SOLO descripcion y marca.
    · NUNCA tocar: costo, precio_venta, stock, categoria.
    · Si el barcode NO existe → insertar como producto nuevo.

    Parámetros
    ----------
    max_pages : None → iterar todas las páginas disponibles
                int  → detenerse después de esa cantidad de páginas
    timeout   : segundos de espera por request HTTP

    Devuelve
    --------
    dict con claves: inserted, updated, skipped, pages_fetched, errors
    """
    mode = f"máximo {max_pages} páginas" if max_pages else "todas las páginas"
    logger.info("Iniciando actualización — modo: %s", mode)

    stats = {
        "inserted":     0,
        "updated":      0,   # nombre o marca cambió
        "skipped":      0,   # sin cambios
        "pages_fetched": 0,
        "errors":       0,
    }

    conn = _get_conn()
    try:
        cursor = conn.cursor()
        page = 1

        # Cargar blacklist una sola vez
        blacklist = _load_blacklist(cursor)
        logger.info("Lista negra cargada: %d barcodes bloqueados", len(blacklist))

        while True:
            if max_pages is not None and page > max_pages:
                logger.info("Límite de %d páginas alcanzado.", max_pages)
                break

            logger.info("Actualizando — página %d", page)
            data = _fetch_page(page, timeout=timeout)
            stats["pages_fetched"] += 1

            if not data:
                stats["errors"] += 1
                logger.warning("Sin datos en página %d, se detiene.", page)
                break

            products_raw = data.get("products", [])
            if not products_raw:
                logger.info("Página %d vacía — fin de resultados.", page)
                break

            for raw in products_raw:
                p = _filter_product(raw)
                if not p:
                    continue

                # ── ¿Está en la lista negra? ─────────────────────────────────
                if p["barcode"] in blacklist:
                    stats["skipped"] += 1
                    continue

                existing = cursor.execute(
                    """
                    SELECT id, descripcion, marca
                    FROM productos
                    WHERE codigo_barras = ?
                    """,
                    (p["barcode"],)
                ).fetchone()

                if existing:
                    # ── Actualizar solo nombre y marca si cambiaron ──────────
                    name_changed  = existing["descripcion"] != p["name"]
                    brand_changed = existing["marca"]       != p["brand"]

                    if name_changed or brand_changed:
                        cursor.execute(
                            """
                            UPDATE productos
                            SET descripcion = ?, marca = ?
                            WHERE id = ?
                            """,
                            (p["name"], p["brand"], existing["id"])
                        )
                        stats["updated"] += 1
                    else:
                        stats["skipped"] += 1
                else:
                    # ── Producto nuevo: insertar ─────────────────────────────
                    cat_name = _ensure_category(cursor, p["category"])
                    codigo   = _next_codigo_interno(cursor)

                    try:
                        cursor.execute(
                            """
                            INSERT INTO productos
                                (codigo_interno, codigo_barras, descripcion, marca,
                                 categoria, unidad, por_peso, costo, precio_venta,
                                 iva, activo)
                            VALUES (?, ?, ?, ?, ?, 'Unidad', 0, 0, 0, '21%', 1)
                            """,
                            (codigo, p["barcode"], p["name"], p["brand"], cat_name)
                        )
                        stats["inserted"] += 1
                    except sqlite3.IntegrityError:
                        stats["skipped"] += 1

            page += 1
            time.sleep(DELAY_S)

        conn.commit()
        logger.info(
            "Actualización completa — nuevos: %d | actualizados: %d | "
            "sin cambios: %d | páginas: %d | errores: %d",
            stats["inserted"], stats["updated"], stats["skipped"],
            stats["pages_fetched"], stats["errors"]
        )

    except Exception as exc:
        conn.rollback()
        logger.error("Error fatal durante la actualización: %s", exc, exc_info=True)
        raise
    finally:
        conn.close()

    return stats


# ─── Utilidades auxiliares ────────────────────────────────────────────────────

def check_connectivity(timeout: int = 5) -> bool:
    """Verifica si hay conexión a internet."""
    # Usa HTTP (no HTTPS) para evitar problemas de certificados SSL
    # en ejecutables PyInstaller donde certifi puede no estar disponible
    try:
        req = urllib.request.Request(
            "http://www.openfoodfacts.org",
            headers={"User-Agent": USER_AGENT}
        )
        urllib.request.urlopen(req, timeout=timeout)
        return True
    except Exception:
        pass
    # Fallback: intenta con Google DNS como segunda verificación
    try:
        import socket
        socket.create_connection(("8.8.8.8", 53), timeout=timeout)
        return True
    except Exception:
        return False


def get_stats() -> dict:
    """
    Retorna estadisticas actuales de la DB relacionadas con la importacion.
    Llama init_db() primero para garantizar que las tablas existen.
    """
    try:
        import database as _db
        _db.init_db()
    except Exception:
        pass

    conn = _get_conn()
    try:
        cur = conn.cursor()
        total    = cur.execute("SELECT COUNT(*) FROM productos WHERE activo=1").fetchone()[0]
        con_bc   = cur.execute(
            "SELECT COUNT(*) FROM productos WHERE activo=1 AND codigo_barras != ''"
        ).fetchone()[0]
        con_marca = cur.execute(
            "SELECT COUNT(*) FROM productos WHERE activo=1 AND marca != ''"
        ).fetchone()[0]
        sin_precio = cur.execute(
            "SELECT COUNT(*) FROM productos WHERE activo=1 AND precio_venta = 0"
        ).fetchone()[0]
        return {
            "total_productos":     total,
            "con_codigo_barras":   con_bc,
            "con_marca":           con_marca,
            "sin_precio_asignado": sin_precio,
        }
    finally:
        conn.close()


# ─── Ejecución directa (sin Flask) ───────────────────────────────────────────
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "import"

    if cmd == "import":
        lim = int(sys.argv[2]) if len(sys.argv) > 2 else 350
        result = import_products(limit=lim)
        print(f"\nResultado: {result}")

    elif cmd == "update":
        pages = int(sys.argv[2]) if len(sys.argv) > 2 else None
        result = update_products(max_pages=pages)
        print(f"\nResultado: {result}")

    elif cmd == "stats":
        print(get_stats())

    else:
        print("Uso: python openfood_importer.py [import|update|stats] [limite|paginas]")
