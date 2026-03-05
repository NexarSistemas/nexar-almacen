"""
openfoodfacts.py — Módulo de integración con OpenFoodFacts API.
Permite importar productos reales con código de barras, nombre y marca.
Si no hay conexión a internet, usa el dataset local (productos_seed.py).
"""
import json
import os
import time
import sys
import urllib.request
import urllib.parse

# ─── MAPEO DE CATEGORÍAS OpenFoodFacts → Sistema ─────────────────────────────
CAT_MAP = {
    'beverages': 'Bebidas', 'drinks': 'Bebidas', 'sodas': 'Bebidas',
    'waters': 'Bebidas', 'juices': 'Bebidas', 'beers': 'Bebidas',
    'wines': 'Bebidas', 'spirits': 'Bebidas', 'coffees': 'Yerba y Té',
    'teas': 'Yerba y Té', 'instant-coffees': 'Yerba y Té',
    'dairies': 'Lácteos', 'milks': 'Lácteos', 'cheeses': 'Fiambres y Quesos',
    'yogurts': 'Lácteos', 'butters': 'Lácteos', 'creams': 'Lácteos',
    'breads': 'Panadería', 'biscuits': 'Panadería', 'cereals': 'Panadería',
    'pastas': 'Almacén', 'rices': 'Almacén', 'legumes': 'Almacén',
    'sugars': 'Almacén', 'flours': 'Almacén', 'oils': 'Almacén',
    'sauces': 'Almacén', 'condiments': 'Almacén', 'spices': 'Almacén',
    'canned-foods': 'Almacén', 'jams': 'Almacén',
    'chips': 'Golosinas y Snacks', 'snacks': 'Golosinas y Snacks',
    'chocolates': 'Golosinas y Snacks', 'candies': 'Golosinas y Snacks',
    'cleaning': 'Limpieza', 'hygiene': 'Higiene', 'cosmetics': 'Higiene',
    'frozen': 'Congelados', 'meats': 'Fiambres y Quesos',
    'pet-foods': 'Mascotas', 'tobacco': 'Cigarrillos',
    'baby-foods': 'Higiene',
}

def _map_category(tags):
    """Mapea las categorías de OFF al sistema local."""
    if not tags:
        return 'Almacén'
    for tag in tags:
        tag_clean = tag.replace('en:', '').replace('es:', '').replace('-', ' ').lower()
        for key, cat in CAT_MAP.items():
            if key.replace('-', ' ') in tag_clean:
                return cat
    return 'Almacén'

def _fetch_json(url, timeout=10):
    """Realiza un GET HTTP y devuelve el JSON parseado. None si falla."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'AlmacenGestion/1.3.0'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception:
        return None

def buscar_por_barcode(barcode: str) -> dict | None:
    """Busca un producto por código de barras en OpenFoodFacts.
    Devuelve dict con: barcode, name, brand, category | None si no existe."""
    url = f'https://world.openfoodfacts.org/api/v2/product/{barcode}.json'
    data = _fetch_json(url)
    if not data or data.get('status') != 1:
        return None
    prod = data.get('product', {})
    name = (prod.get('product_name_es') or prod.get('product_name') or '').strip()
    brand = (prod.get('brands') or '').split(',')[0].strip()
    tags = prod.get('categories_tags', [])
    return {
        'barcode': barcode,
        'name': name or prod.get('abbreviated_product_name', ''),
        'brand': brand,
        'category': _map_category(tags),
    } if name else None

def importar_desde_openfoodfacts(pais='ar', paginas=10, por_pagina=50,
                                  callback=None) -> list:
    """
    Importa productos de OpenFoodFacts para Argentina.
    pais: código ISO de país ('ar' = Argentina)
    paginas: cuántas páginas de resultados obtener
    por_pagina: productos por página (max 50)
    callback: función(mensaje, progreso%) para actualizar progreso
    Devuelve lista de dicts: barcode, name, brand, category
    """
    productos = []
    categorias_buscar = [
        'bebidas', 'lacteos', 'panificados', 'fideos', 'arroz',
        'aceites', 'limpieza', 'galletitas', 'golosinas', 'yerba',
    ]

    if callback:
        callback("Conectando con OpenFoodFacts...", 0)

    for idx_cat, cat in enumerate(categorias_buscar):
        for page in range(1, paginas + 1):
            url = (
                f'https://world.openfoodfacts.org/cgi/search.pl'
                f'?search_terms={urllib.parse.quote(cat)}'
                f'&search_simple=1&action=process&json=1'
                f'&country=argentina'
                f'&page={page}&page_size={por_pagina}'
                f'&fields=code,product_name,product_name_es,brands,categories_tags'
            )
            data = _fetch_json(url)
            if not data:
                break
            for p in data.get('products', []):
                barcode = p.get('code', '').strip()
                name = (p.get('product_name_es') or p.get('product_name') or '').strip()
                brand = (p.get('brands') or '').split(',')[0].strip()
                tags = p.get('categories_tags', [])
                if barcode and name and len(barcode) >= 8:
                    productos.append({
                        'barcode': barcode,
                        'name': name,
                        'brand': brand,
                        'category': _map_category(tags),
                    })
            prog = int(((idx_cat * paginas + page) / (len(categorias_buscar) * paginas)) * 100)
            if callback:
                callback(f"Descargando {cat}... pág {page}", prog)
            time.sleep(0.3)  # Respetar rate limit de OFF

    return productos

def importar_desde_seed() -> list:
    """Usa el dataset local embebido (sin internet)."""
    from productos_seed import PRODUCTOS_SEED
    return [
        {'barcode': p[0], 'name': p[1], 'brand': p[2], 'category': p[3],
         'unit': p[4], 'por_peso': p[5]}
        for p in PRODUCTOS_SEED
    ]

def tiene_internet(timeout=3) -> bool:
    """Verifica si hay conexión a internet."""
    try:
        urllib.request.urlopen('https://world.openfoodfacts.org', timeout=timeout)
        return True
    except Exception:
        return False

