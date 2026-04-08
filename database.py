import sqlite3
import os
import hashlib as _hashlib
import hmac as _hmac
from werkzeug.security import generate_password_hash, check_password_hash
import time as _time
from datetime import datetime, date, timedelta
from calendar import month_name
import base64 as _b64
import hashlib as _hl

def _get_telemetry_path() -> str:
    """Ruta del archivo externo de control de demo."""
    if os.name == 'nt':
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
        folder = os.path.join(base, 'nexaralmacen')
    else:
        base = os.environ.get('XDG_DATA_HOME',
                              os.path.join(os.path.expanduser('~'), '.local', 'share'))
        folder = os.path.join(base, 'nexaralmacen')
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, 'telemetry.bin')


def _encode_date(date_str: str, machine_id: str) -> str:
    """
    Codifica la fecha junto con el machine_id para que el contenido
    no sea legible ni obvio.
    Formato interno: base64( sha256(machine_id)[:8] + ":" + date_str )
    """
    salt   = _hl.sha256(machine_id.encode()).hexdigest()[:8]
    raw    = f"{salt}:{date_str}"
    return _b64.b64encode(raw.encode()).decode()


def _decode_date(encoded: str, machine_id: str) -> str | None:
    """
    Decodifica y verifica que el contenido corresponda a este machine_id.
    Retorna la fecha ISO o None si es inválido/de otra máquina.
    """
    try:
        raw  = _b64.b64decode(encoded.strip()).decode()
        salt = _hl.sha256(machine_id.encode()).hexdigest()[:8]
        if not raw.startswith(f"{salt}:"):
            return None  # archivo de otra máquina o corrupto
        return raw.split(":", 1)[1]
    except Exception:
        return None


def _read_telemetry(machine_id: str) -> str | None:
    """
    Lee la fecha de instalación del archivo externo.
    Retorna fecha ISO string o None si no existe o es inválido.
    """
    path = _get_telemetry_path()
    try:
        with open(path, 'r') as f:
            encoded = f.read().strip()
        return _decode_date(encoded, machine_id)
    except Exception:
        return None


def _write_telemetry(date_str: str, machine_id: str) -> bool:
    """
    Escribe la fecha de instalación en el archivo externo.
    Retorna True si tuvo éxito.
    """
    path = _get_telemetry_path()
    try:
        encoded = _encode_date(date_str, machine_id)
        with open(path, 'w') as f:
            f.write(encoded)
        return True
    except Exception:
        return False


# Ruta de la base de datos:
# 1. Variable de entorno ALMACEN_DB_PATH (instaladores .deb y Windows)
# 2. En Windows sin env var: %APPDATA%\nexaralmacen\almacen.db  (evita readonly en Program Files)
# 3. Fallback: junto al script (portable/Linux)
def _resolve_db_path():
    env = os.environ.get('ALMACEN_DB_PATH', '')
    if env:
        return env
    if os.name == 'nt':  # Windows
        appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
        data_dir = os.path.join(appdata, 'nexaralmacen')
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, 'almacen.db')
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'almacen.db')

DB_PATH = _resolve_db_path()

TIER_LIMITS = {
    "DEMO": {
        "productos_off": None,   # ilimitado durante 30 días
        "clientes":      None,
        "proveedores":   None,
    },
    "BASICA": {
        "productos_off": 200,    # máx 200 productos importados desde OFF
        "clientes":      100,    # máx 100 clientes en CC
        "proveedores":   50,     # máx 50 proveedores
    },
    "PRO": {
        "productos_off": None,   # ilimitado
        "clientes":      None,
        "proveedores":   None,
    },
}

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def q(sql, params=(), fetchall=True, fetchone=False, commit=False):
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute(sql, params)
        if commit:
            conn.commit()
            return c.lastrowid
        if fetchone:
            return c.fetchone()
        if fetchall:
            return c.fetchall()
    finally:
        conn.close()

def qm(statements):
    """Execute multiple statements in one transaction"""
    conn = get_conn()
    try:
        c = conn.cursor()
        for sql, params in statements:
            c.execute(sql, params)
        conn.commit()
        return c.lastrowid
    finally:
        conn.close()

# ─── INIT ────────────────────────────────────────────────────────────────────
_db_initialized = False

def _seed_changelog(c):
    """Inserta el historial de versiones inicial si no existe."""
    existing = c.execute("SELECT COUNT(*) FROM changelog").fetchone()[0]
    if existing > 0:
        return
    entries = [
        ('1.0.0','2026-01-01','Nueva función',
         'Lanzamiento inicial del sistema',
         'Primera versión de Nexar Almacen con módulos de Ventas, Stock, Caja y Gastos.'),
        ('1.1.0','2026-01-15','Nueva función',
         'Cuentas Corrientes',
         'Se agregaron módulos de CC Clientes y CC Proveedores con alertas de vencimiento.'),
        ('1.2.0','2026-02-01','Nueva función',
         'Estadísticas, Análisis y Usuarios',
         'Dashboard con gráficos, módulo de análisis de rentabilidad y gestión de múltiples usuarios con roles.'),
        ('1.2.1','2026-02-24','Corrección',
         'Mejoras de estabilidad y respaldos',
         'Sidebar con scroll, check_deps robusto, módulo de respaldos automáticos y botón de apagado del sistema.'),
        ('1.3.0','2026-02-27','Nueva función',
         'OpenFoodFacts, demo por tiempo y versionado',
         'Integración con API OpenFoodFacts para importar 360+ productos reales. Demo por 30 días. Sistema de versionado semántico con changelog. Instaladores profesionales multiplataforma.'),
        ('1.4.0','2026-02-27','Nueva función',
         'Filtros de calidad + Lista negra + Mejoras de stock',
         'Filtro de barcodes argentinos 779/780. Detección de descripciones basura. Lista negra de barcodes gestionable. Proveedor habitual seleccionable en stock. Alias /punto_venta.'),
        ('1.5.0','2026-03-02','Nueva función',
         'Puerto aleatorio + Cierre de sesión + Actualizaciones + Ventana nativa',
         'Puerto aleatorio para evitar conflictos. Cierre de sesión automático al apagar. Sistema de actualización sin reinstalar. Ventana independiente tipo app nativa. Botón apagar en login.'),
        ('1.5.1','2026-03-05','Corrección',
         'Fix login loop al reiniciar',
         'Corregido bug donde login_date usaba solo fecha YYYY-MM-DD causando loop infinito al comparar con sessions_invalidated_at datetime completo. Ahora ambos usan datetime ISO completo.'),
        ('1.5.2','2026-03-07','Mejoras',
         'Integración de favicon y organización de estáticos',
         'Ruta dedicada /favicon.ico en Flask. Iconos movidos a static/icons/. Mejora en organización de archivos estáticos.'),
        ('1.5.3','2026-03-07','Corrección',
         'Fix loop de login al apagar el sistema',
         'Corregido bug en rutas /apagar y /apagar_rapido: usaban date.today() en lugar de datetime.now() para sessions_invalidated_at, causando loop de login al reiniciar. Fallbacks de versión actualizados.'),
        ('1.5.4','2026-03-15','Mejora de seguridad',
         'Sistema de licencias RSA',
         'Reemplaza validación HMAC por firma digital RSA de 2048 bits. Token Base64. Soporte MONO y MULTI (1, 3 o 10 PCs). Proceso de transferencia de licencia entre PCs.'),
        ('1.5.5','2026-03-18','Corrección',
         'Fix ticket abría navegador externo pidiendo login',
         'El botón Ver Ticket en Punto de Venta y el link de ticket en Historial tenían target="_blank", abriéndose en el navegador del sistema sin sesión activa. Ahora abren dentro de la misma ventana de la app.'),
        ('1.6.0','2026-03-19','Nueva función',
         'Sistema de tiers: Plan Básico y Plan Pro',
         'Plan Básico pago único U$D 30 con límites (200 productos OFF, 100 clientes, 50 proveedores). '
         'Plan Pro mensual U$D 6 ilimitado con estadísticas históricas, análisis, actualizaciones y soporte. '
         'Anti-reinstall con telemetry.bin codificado. Pantalla de licencia renovada con comparativa de planes.'),
        ('1.7.0','2026-03-28','Mejoras y correcciones',
         'Pipeline CI/CD inteligente y corrección de enlaces',
         'Automatización de releases basada en CHANGELOG, firma GPG de binarios, creación automática de tags y releases. '
         'Enlaces a proveedores en stock.html corregidos para apuntar a /cc_proveedores.'),

    ]
    for ver, fecha, tipo, titulo, desc in entries:
        c.execute(
            "INSERT INTO changelog (version,fecha,tipo,titulo,descripcion) VALUES (?,?,?,?,?)",
            (ver, fecha, tipo, titulo, desc)
        )


def init_db():
    global _db_initialized
    if _db_initialized:
        return
    _db_initialized = True
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS config (
            clave TEXT PRIMARY KEY,
            valor TEXT
        );

        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            rol TEXT DEFAULT 'usuario',
            nombre_completo TEXT DEFAULT '',
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            activa INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_interno TEXT UNIQUE NOT NULL,
            codigo_barras TEXT DEFAULT '',
            descripcion TEXT NOT NULL,
            marca TEXT DEFAULT '',
            categoria TEXT DEFAULT '',
            unidad TEXT DEFAULT 'Unidad',
            por_peso INTEGER DEFAULT 0,
            costo REAL DEFAULT 0,
            precio_venta REAL DEFAULT 0,
            iva TEXT DEFAULT '21%',
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS changelog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL,
            fecha TEXT NOT NULL,
            tipo TEXT DEFAULT 'Actualización',
            titulo TEXT NOT NULL,
            descripcion TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS barcode_blacklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE NOT NULL,
            nombre_producto TEXT DEFAULT '',
            motivo TEXT DEFAULT '',
            fecha TEXT DEFAULT CURRENT_DATE
        );

        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER UNIQUE REFERENCES productos(id) ON DELETE CASCADE,
            stock_actual REAL DEFAULT 0,
            stock_minimo REAL DEFAULT 5,
            stock_maximo REAL DEFAULT 50,
            ultimo_ingreso TEXT DEFAULT '',
            proveedor_habitual TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            nombre TEXT NOT NULL,
            dni_cuit TEXT DEFAULT '',
            telefono TEXT DEFAULT '',
            email TEXT DEFAULT '',
            limite_credito REAL DEFAULT 0,
            activo INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            nombre TEXT NOT NULL,
            cuit TEXT DEFAULT '',
            telefono TEXT DEFAULT '',
            email TEXT DEFAULT '',
            dias_credito INTEGER DEFAULT 30,
            activo INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_ticket INTEGER,
            fecha TEXT,
            hora TEXT,
            cliente_id INTEGER DEFAULT 0,
            cliente_nombre TEXT DEFAULT 'Mostrador',
            medio_pago TEXT DEFAULT 'Efectivo',
            subtotal REAL DEFAULT 0,
            descuento_adicional REAL DEFAULT 0,
            total REAL DEFAULT 0,
            vendedor TEXT DEFAULT '',
            temporada TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS ventas_detalle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER REFERENCES ventas(id) ON DELETE CASCADE,
            producto_id INTEGER DEFAULT 0,
            codigo_interno TEXT DEFAULT '',
            descripcion TEXT DEFAULT '',
            categoria TEXT DEFAULT '',
            unidad TEXT DEFAULT '',
            cantidad REAL DEFAULT 1,
            precio_unitario REAL DEFAULT 0,
            descuento REAL DEFAULT 0,
            subtotal REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            numero_remito TEXT DEFAULT '',
            proveedor_id INTEGER DEFAULT 0,
            proveedor_nombre TEXT DEFAULT '',
            producto_id INTEGER DEFAULT 0,
            codigo_interno TEXT DEFAULT '',
            descripcion TEXT DEFAULT '',
            cantidad REAL DEFAULT 1,
            costo_unitario REAL DEFAULT 0,
            total REAL DEFAULT 0,
            observaciones TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS caja_historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT UNIQUE,
            saldo_apertura REAL DEFAULT 0,
            ventas_efectivo REAL DEFAULT 0,
            ventas_debito REAL DEFAULT 0,
            ventas_credito REAL DEFAULT 0,
            ventas_qr REAL DEFAULT 0,
            ventas_cta_cte REAL DEFAULT 0,
            ventas_transferencia REAL DEFAULT 0,
            total_ventas REAL DEFAULT 0,
            gastos_dia REAL DEFAULT 0,
            saldo_cierre_esperado REAL DEFAULT 0,
            saldo_cierre_real REAL DEFAULT 0,
            diferencia REAL DEFAULT 0,
            cerrada INTEGER DEFAULT 0,
            responsable_apertura TEXT DEFAULT '',
            responsable_cierre TEXT DEFAULT '',
            hora_apertura TEXT DEFAULT '',
            hora_cierre TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            tipo TEXT DEFAULT 'Gasto',
            categoria TEXT DEFAULT '',
            descripcion TEXT DEFAULT '',
            monto REAL DEFAULT 0,
            iva_incluido INTEGER DEFAULT 1,
            medio_pago TEXT DEFAULT 'Efectivo',
            proveedor TEXT DEFAULT '',
            necesario TEXT DEFAULT 'SI (necesario)',
            comprobante TEXT DEFAULT '',
            observaciones TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS cc_clientes_mov (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER REFERENCES clientes(id),
            fecha TEXT,
            tipo TEXT DEFAULT 'Venta',
            numero_comprobante TEXT DEFAULT '',
            debe REAL DEFAULT 0,
            haber REAL DEFAULT 0,
            vencimiento TEXT DEFAULT '',
            observaciones TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS facturas_proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id INTEGER REFERENCES proveedores(id),
            numero_factura TEXT DEFAULT '',
            fecha TEXT,
            fecha_vencimiento TEXT,
            importe REAL DEFAULT 0,
            pagado REAL DEFAULT 0,
            observaciones TEXT DEFAULT ''
        );
    """)

    # Default config
    defaults = [
        ('nombre_negocio', 'Mi Almacén'),
        ('direccion', ''),
        ('telefono', ''),
        ('cuit', ''),
        ('responsable', ''),
        ('margen_minimo', '0.20'),
        ('margen_objetivo', '0.35'),
        ('dias_alerta_proveedor', '30'),
        ('dias_alerta_cliente', '15'),
        ('siguiente_ticket', '1001'),
        ('siguiente_codigo', '1'),
        ('demo_mode', '1'),           # 1=demo, 0=full
        ('demo_dias', '30'),           # días de demo desde instalación
        ('demo_install_date', ''),     # fecha ISO de instalación (se fija solo 1 vez)
        ('backup_intervalo_h', '24'),  # 0 = desactivado
        ('backup_keep', '10'),         # cuántos respaldos conservar
        ('backup_dir', ''),            # vacío = carpeta respaldo/ del sistema
        ('backup_ultimo', ''),
    ]
    for k, v in defaults:
        c.execute("INSERT OR IGNORE INTO config VALUES (?,?)", (k, v))

    # Generate machine_id if not exists
    mid = c.execute("SELECT valor FROM config WHERE clave='machine_id'").fetchone()
    if not mid:
        import uuid
        machine_id = str(uuid.uuid4()).replace('-','').upper()[:16]
        c.execute("INSERT INTO config VALUES ('machine_id',?)", (machine_id,))

    # ── Fix install date con anti-reinstall ──────────────────────────────────
    # 1. Obtener machine_id (ya fue generado arriba en este mismo init_db)
    _mid_row = c.execute("SELECT valor FROM config WHERE clave='machine_id'").fetchone()
    _mid     = _mid_row['valor'] if _mid_row else 'UNKNOWN'

    # 2. Leer fecha del archivo externo (telemetry.bin)
    _telem_date = _read_telemetry(_mid)

    # 3. Leer fecha de la DB
    inst = c.execute("SELECT valor FROM config WHERE clave='demo_install_date'").fetchone()
    _db_date = inst['valor'] if inst and inst['valor'] else None

    if _telem_date:
        # El archivo externo existe y es válido — es la fuente de verdad
        # Si la DB fue borrada y recreada, restaurar la fecha original
        if _db_date != _telem_date:
            c.execute(
                "INSERT OR REPLACE INTO config VALUES ('demo_install_date',?)",
                (_telem_date,)
            )
    elif _db_date:
        # La DB tiene fecha pero el archivo no existe (primera vez post-update)
        # Crear el archivo externo con la fecha que ya tiene la DB
        _write_telemetry(_db_date, _mid)
    else:
        # Ni DB ni archivo — primera instalación real
        _today = date.today().isoformat()
        c.execute(
            "INSERT OR REPLACE INTO config VALUES ('demo_install_date',?)",
            (_today,)
        )
        _write_telemetry(_today, _mid)

    # ── DB MIGRATIONS ──────────────────────────────────────────────────────────
    # v1.5.4: agregar claves de licencia RSA si no existen (para instalaciones previas)
    for _k, _v in [
        ('license_type',         'DEMO'),
        ('license_max_machines', '1'),
        ('license_key',          ''),
        ('license_activated_at', ''),
        ('license_tier',         'DEMO'),    # DEMO / BASICA / PRO
        ('license_expires_at',   ''),        # fecha ISO vencimiento Pro, vacío = no vence

    ]:
        c.execute("INSERT OR IGNORE INTO config VALUES (?,?)", (_k, _v))

    # ── DB MIGRATIONS ──────────────────────────────────────────────────────────
    # Add 'marca' column if not present (migration from <1.3.0)
    cols = [row[1] for row in c.execute("PRAGMA table_info(productos)").fetchall()]
    if 'marca' not in cols:
        c.execute("ALTER TABLE productos ADD COLUMN marca TEXT DEFAULT ''")

    # Add changelog table if not exists
    c.execute("""
        CREATE TABLE IF NOT EXISTS changelog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL,
            fecha TEXT NOT NULL,
            tipo TEXT DEFAULT 'Actualización',
            titulo TEXT NOT NULL,
            descripcion TEXT DEFAULT ''
        )
    """)

    # Seed changelog with known versions
    _seed_changelog(c)

    # Default users (admin + vendedor)
    import hashlib
    def _hash(pw): return hashlib.sha256(pw.encode()).hexdigest()
    default_users = [
        ('admin',    _hash('admin123'),    'admin',   'Administrador'),
        ('vendedor', _hash('vendedor123'), 'usuario', 'Vendedor'),
    ]
    for uname, phash, rol, nombre in default_users:
        c.execute("INSERT OR IGNORE INTO usuarios (username,password_hash,rol,nombre_completo) VALUES (?,?,?,?)",
                  (uname, phash, rol, nombre))

    # Categories
    cats = [
        'Lácteos','No Perecederos','Bebidas','Infusiones',
        'Limpieza del Hogar','Higiene Personal','Verduras / Frutas (x peso)',
        'Fiambres (x peso)','Pan / Panadería (x peso)','Carnes','Congelados',
        'Golosinas / Confitería','Enlatados / Conservas',
        'Cereales / Harinas / Pastas','Aceites / Condimentos / Salsas',
        'Papel / Descartables','Ferretería / Bazar','Tabaco / Cigarrillos',
        'Mascotas','Bebidas Alcohólicas','Snacks / Aperitivos',
        'Dietética / Naturales','Otros',
    ]
    for cat in cats:
        c.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES (?)", (cat,))

    # Reparar productos importados sin fila de stock
    # (puede ocurrir si fueron importados por openfood_importer antes de este fix)
    c.execute("""
        INSERT OR IGNORE INTO stock (producto_id, stock_actual, stock_minimo, stock_maximo)
        SELECT id, 0, 5, 50 FROM productos
        WHERE activo=1
        AND id NOT IN (SELECT producto_id FROM stock)
    """)

    conn.commit()
    conn.close()
    # _seed_demo_data() eliminado: la app se distribuye sin datos de ejemplo.
    # Los productos se importan desde Productos -> Importar Productos.

def _seed_demo_data():
    """Deshabilitado: la app se distribuye sin datos de ejemplo.
    Usar Productos -> Importar Productos para cargar el dataset local
    (361 productos reales) o importar desde OpenFoodFacts.
    """
    return

# ─── CONFIG ──────────────────────────────────────────────────────────────────
def get_config():
    rows = q("SELECT clave, valor FROM config")
    return {r['clave']: r['valor'] for r in rows}

def set_config(data: dict):
    conn = get_conn()
    c = conn.cursor()
    for k, v in data.items():
        c.execute("INSERT OR REPLACE INTO config VALUES (?,?)", (k, v))
    conn.commit()
    conn.close()

def next_codigo():
    """Generate next unique product code, syncing with actual DB if needed"""
    conn = get_conn()
    c = conn.cursor()
    # Get max existing code number
    row = c.execute("SELECT MAX(CAST(SUBSTR(codigo_interno,5) AS INTEGER)) as mx FROM productos WHERE codigo_interno LIKE 'PRD-%'").fetchone()
    max_n = (row['mx'] or 0) + 1
    # Also check config
    cfg_n = int(c.execute("SELECT valor FROM config WHERE clave='siguiente_codigo'").fetchone()['valor'] or 1)
    n = max(max_n, cfg_n)
    new_code = f"PRD-{n:04d}"
    c.execute("INSERT OR REPLACE INTO config VALUES ('siguiente_codigo', ?)", (str(n + 1),))
    conn.commit()
    conn.close()
    return new_code

def next_ticket():
    cfg = get_config()
    n = int(cfg.get('siguiente_ticket', 1001))
    set_config({'siguiente_ticket': str(n + 1)})
    return n

# ─── CATEGORÍAS ──────────────────────────────────────────────────────────────
def get_categorias():
    return [r['nombre'] for r in q("SELECT nombre FROM categorias WHERE activa=1 ORDER BY nombre")]

def add_categoria(nombre):
    q("INSERT OR IGNORE INTO categorias (nombre) VALUES (?)", (nombre,), fetchall=False, commit=True)

# ─── PRODUCTOS ───────────────────────────────────────────────────────────────
def get_productos(activo_only=True, search=''):
    sql = "SELECT * FROM productos"
    conds = []
    params = []
    if activo_only:
        conds.append("activo=1")
    if search:
        conds.append("(codigo_interno LIKE ? OR codigo_barras LIKE ? OR descripcion LIKE ? OR categoria LIKE ?)")
        params += [f'%{search}%'] * 4
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    sql += " ORDER BY descripcion"
    return q(sql, params)

def get_producto(pid):
    return q("SELECT * FROM productos WHERE id=?", (pid,), fetchone=True)

def get_producto_by_codigo(codigo):
    """Search by internal code or barcode"""
    r = q("SELECT * FROM productos WHERE codigo_interno=? AND activo=1", (codigo,), fetchone=True)
    if not r:
        r = q("SELECT * FROM productos WHERE codigo_barras=? AND activo=1", (codigo,), fetchone=True)
    return r

def add_producto(data):
    codigo = next_codigo()
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO productos
        (codigo_interno,codigo_barras,descripcion,marca,categoria,unidad,por_peso,costo,precio_venta,iva,activo)
        VALUES (?,?,?,?,?,?,?,?,?,?,1)""",
        (codigo, data.get('codigo_barras',''), data['descripcion'], data.get('marca',''),
         data.get('categoria',''), data.get('unidad','Unidad'), int(data.get('por_peso',0)),
         float(data.get('costo',0)), float(data.get('precio_venta',0)), data.get('iva','21%')))
    pid = c.lastrowid
    c.execute("INSERT INTO stock (producto_id,stock_actual,stock_minimo,stock_maximo) VALUES (?,?,?,?)",
              (pid, float(data.get('stock_actual',0)), float(data.get('stock_minimo',5)), float(data.get('stock_maximo',50))))
    conn.commit()
    conn.close()
    return pid

def update_producto(pid, data):
    q("""UPDATE productos SET codigo_barras=?,descripcion=?,marca=?,categoria=?,unidad=?,por_peso=?,
        costo=?,precio_venta=?,iva=?,activo=? WHERE id=?""",
        (data.get('codigo_barras',''), data['descripcion'], data.get('marca',''),
         data.get('categoria',''), data.get('unidad','Unidad'), int(data.get('por_peso',0)),
         float(data.get('costo',0)), float(data.get('precio_venta',0)), data.get('iva','21%'),
         int(data.get('activo',1)), pid),
        fetchall=False, commit=True)

def delete_producto(pid):
    q("UPDATE productos SET activo=0 WHERE id=?", (pid,), fetchall=False, commit=True)

# ─── STOCK ───────────────────────────────────────────────────────────────────
def get_stock_full(search='', alerta_only=False):
    sql = """SELECT p.id, p.codigo_interno, p.descripcion, p.categoria, p.unidad,
                    p.costo, p.precio_venta,
                    s.stock_actual, s.stock_minimo, s.stock_maximo,
                    s.ultimo_ingreso, s.proveedor_habitual,
                    CASE
                        WHEN s.stock_actual <= 0 THEN 'SIN STOCK'
                        WHEN s.stock_actual <= s.stock_minimo THEN 'CRITICO'
                        WHEN s.stock_actual <= s.stock_minimo * 1.5 THEN 'BAJO'
                        WHEN s.stock_actual >= s.stock_maximo THEN 'EXCESO'
                        ELSE 'NORMAL'
                    END as estado,
                    s.stock_actual * p.costo as valor_stock
             FROM productos p
             JOIN stock s ON s.producto_id = p.id
             WHERE p.activo=1"""
    params = []
    if search:
        sql += " AND (p.descripcion LIKE ? OR p.categoria LIKE ? OR p.codigo_interno LIKE ?)"
        params += [f'%{search}%'] * 3
    if alerta_only:
        sql += " AND s.stock_actual <= s.stock_minimo * 1.5"
    sql += " ORDER BY p.descripcion"
    return q(sql, params)

def update_stock_item(pid, stock_actual=None, stock_minimo=None, stock_maximo=None, proveedor=None):
    updates = []
    params = []
    if stock_actual is not None:
        updates.append("stock_actual=?"); params.append(stock_actual)
    if stock_minimo is not None:
        updates.append("stock_minimo=?"); params.append(stock_minimo)
    if stock_maximo is not None:
        updates.append("stock_maximo=?"); params.append(stock_maximo)
    if proveedor is not None:
        updates.append("proveedor_habitual=?"); params.append(proveedor)
    if updates:
        params.append(pid)
        q(f"UPDATE stock SET {','.join(updates)} WHERE producto_id=?", params, fetchall=False, commit=True)

def get_alertas_count():
    r = q("""SELECT
        COALESCE(SUM(CASE WHEN s.stock_actual<=0 THEN 1 ELSE 0 END),0) as sin_stock,
        COALESCE(SUM(CASE WHEN s.stock_actual>0 AND s.stock_actual<=s.stock_minimo THEN 1 ELSE 0 END),0) as critico,
        COALESCE(SUM(CASE WHEN s.stock_actual>s.stock_minimo AND s.stock_actual<=s.stock_minimo*1.5 THEN 1 ELSE 0 END),0) as bajo
        FROM stock s JOIN productos p ON p.id=s.producto_id WHERE p.activo=1""", fetchone=True)
    if r:
        return {'sin_stock': r['sin_stock'] or 0, 'critico': r['critico'] or 0, 'bajo': r['bajo'] or 0}
    return {'sin_stock':0,'critico':0,'bajo':0}

# ─── CLIENTES ────────────────────────────────────────────────────────────────
def get_clientes(activo_only=True, search=''):
    sql = "SELECT * FROM clientes"
    conds = []
    params = []
    if activo_only:
        conds.append("activo=1")
    if search:
        conds.append("(nombre LIKE ? OR codigo LIKE ? OR dni_cuit LIKE ?)")
        params += [f'%{search}%'] * 3
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    sql += " ORDER BY nombre"
    return q(sql, params)

def get_cliente(cid):
    return q("SELECT * FROM clientes WHERE id=?", (cid,), fetchone=True)

def add_cliente(data):
    conn = get_conn()
    c = conn.cursor()
    n = c.execute("SELECT COUNT(*)+1 as n FROM clientes").fetchone()['n']
    codigo = f"CLI-{n:03d}"
    c.execute("""INSERT INTO clientes (codigo,nombre,dni_cuit,telefono,email,limite_credito)
        VALUES (?,?,?,?,?,?)""",
        (codigo, data['nombre'], data.get('dni_cuit',''), data.get('telefono',''),
         data.get('email',''), float(data.get('limite_credito',0))))
    conn.commit()
    conn.close()

def update_cliente(cid, data):
    q("""UPDATE clientes SET nombre=?,dni_cuit=?,telefono=?,email=?,limite_credito=?,activo=? WHERE id=?""",
      (data['nombre'], data.get('dni_cuit',''), data.get('telefono',''), data.get('email',''),
       float(data.get('limite_credito',0)), int(data.get('activo',1)), cid),
      fetchall=False, commit=True)

def get_saldo_cliente(cid):
    r = q("SELECT COALESCE(SUM(debe),0)-COALESCE(SUM(haber),0) as saldo FROM cc_clientes_mov WHERE cliente_id=?",
          (cid,), fetchone=True)
    return r['saldo'] if r else 0

# ─── PROVEEDORES ─────────────────────────────────────────────────────────────
def get_proveedores(activo_only=True, search=''):
    sql = "SELECT * FROM proveedores"
    conds = []
    params = []
    if activo_only:
        conds.append("activo=1")
    if search:
        conds.append("(nombre LIKE ? OR codigo LIKE ?)")
        params += [f'%{search}%'] * 2
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    sql += " ORDER BY nombre"
    return q(sql, params)

def get_proveedor(pid):
    return q("SELECT * FROM proveedores WHERE id=?", (pid,), fetchone=True)

def add_proveedor(data):
    conn = get_conn()
    c = conn.cursor()
    n = c.execute("SELECT COUNT(*)+1 as n FROM proveedores").fetchone()['n']
    codigo = f"PROV-{n:03d}"
    c.execute("""INSERT INTO proveedores (codigo,nombre,cuit,telefono,email,dias_credito)
        VALUES (?,?,?,?,?,?)""",
        (codigo, data['nombre'], data.get('cuit',''), data.get('telefono',''),
         data.get('email',''), int(data.get('dias_credito',30))))
    conn.commit()
    conn.close()

def update_proveedor(pid, data):
    q("""UPDATE proveedores SET nombre=?,cuit=?,telefono=?,email=?,dias_credito=?,activo=? WHERE id=?""",
      (data['nombre'], data.get('cuit',''), data.get('telefono',''), data.get('email',''),
       int(data.get('dias_credito',30)), int(data.get('activo',1)), pid),
      fetchall=False, commit=True)

# ─── VENTAS ──────────────────────────────────────────────────────────────────
def get_ventas(search='', fecha_desde='', fecha_hasta='', limit=200):
    sql = """SELECT v.*, COUNT(d.id) as items
             FROM ventas v LEFT JOIN ventas_detalle d ON d.venta_id=v.id
             WHERE 1=1"""
    params = []
    if search:
        sql += " AND (v.cliente_nombre LIKE ? OR v.medio_pago LIKE ? OR CAST(v.numero_ticket AS TEXT) LIKE ?)"
        params += [f'%{search}%'] * 3
    if fecha_desde:
        sql += " AND v.fecha >= ?"; params.append(fecha_desde)
    if fecha_hasta:
        sql += " AND v.fecha <= ?"; params.append(fecha_hasta)
    sql += " GROUP BY v.id ORDER BY v.fecha DESC, v.id DESC LIMIT ?"
    params.append(limit)
    return q(sql, params)

def get_venta_detalle(vid):
    return q("SELECT * FROM ventas_detalle WHERE venta_id=? ORDER BY id", (vid,))

def crear_venta(items, cliente_nombre, medio_pago, descuento_adicional, vendedor, cliente_id=0):
    """
    items: list of dicts with producto_id, codigo_interno, descripcion, categoria,
           unidad, cantidad, precio_unitario, descuento
    """
    today = date.today()
    season = _get_season(today.month)
    ticket = next_ticket()
    subtotal = sum(i['cantidad'] * i['precio_unitario'] * (1 - i['descuento']) for i in items)
    total = subtotal * (1 - descuento_adicional)

    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO ventas (numero_ticket,fecha,hora,cliente_id,cliente_nombre,medio_pago,
                subtotal,descuento_adicional,total,vendedor,temporada)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (ticket, today.isoformat(), datetime.now().strftime('%H:%M'),
         cliente_id, cliente_nombre, medio_pago, subtotal, descuento_adicional, total, vendedor, season))
    vid = c.lastrowid

    for item in items:
        item_subtotal = item['cantidad'] * item['precio_unitario'] * (1 - item['descuento'])
        c.execute("""INSERT INTO ventas_detalle
            (venta_id,producto_id,codigo_interno,descripcion,categoria,unidad,cantidad,precio_unitario,descuento,subtotal)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (vid, item['producto_id'], item['codigo_interno'], item['descripcion'],
             item['categoria'], item['unidad'], item['cantidad'], item['precio_unitario'],
             item['descuento'], item_subtotal))
        # Update stock
        c.execute("UPDATE stock SET stock_actual=stock_actual-? WHERE producto_id=?",
                  (item['cantidad'], item['producto_id']))

    # Update caja
    field_map = {
        'Efectivo': 'ventas_efectivo',
        'Débito': 'ventas_debito',
        'Crédito': 'ventas_credito',
        'QR / Billetera Virtual': 'ventas_qr',
        'Cuenta Corriente': 'ventas_cta_cte',
        'Transferencia': 'ventas_transferencia',
    }
    field = field_map.get(medio_pago, 'ventas_efectivo')
    fecha_str = today.isoformat()
    c.execute(f"""INSERT INTO caja_historial (fecha,{field},total_ventas)
        VALUES (?,?,?) ON CONFLICT(fecha) DO UPDATE SET
        {field}={field}+excluded.{field},
        total_ventas=total_ventas+excluded.total_ventas""",
        (fecha_str, total, total))

    # If cuenta corriente, register movement
    if medio_pago == 'Cuenta Corriente' and cliente_id:
        venc = (today + timedelta(days=15)).isoformat()
        c.execute("""INSERT INTO cc_clientes_mov (cliente_id,fecha,tipo,numero_comprobante,debe,vencimiento)
            VALUES (?,?,?,?,?,?)""",
            (cliente_id, today.isoformat(), 'Venta', str(ticket), total, venc))

    conn.commit()
    conn.close()
    return vid, ticket

def _get_season(month):
    if month in [12, 1, 2, 3]: return 'Verano'
    if month in [4, 5]: return 'Otoño'
    if month in [6, 7, 8]: return 'Invierno'
    return 'Primavera'

# ─── COMPRAS ─────────────────────────────────────────────────────────────────
def get_compras(search='', limit=200):
    sql = """SELECT c.*, p.nombre as proveedor_obj FROM compras c
             LEFT JOIN proveedores p ON p.id=c.proveedor_id WHERE 1=1"""
    params = []
    if search:
        sql += " AND (c.descripcion LIKE ? OR c.proveedor_nombre LIKE ? OR c.numero_remito LIKE ?)"
        params += [f'%{search}%'] * 3
    sql += " ORDER BY c.fecha DESC, c.id DESC LIMIT ?"
    params.append(limit)
    return q(sql, params)

def registrar_compra(data):
    conn = get_conn()
    c = conn.cursor()
    total = float(data.get('cantidad',1)) * float(data.get('costo_unitario',0))
    c.execute("""INSERT INTO compras
        (fecha,numero_remito,proveedor_id,proveedor_nombre,producto_id,codigo_interno,descripcion,
         cantidad,costo_unitario,total,observaciones)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (data.get('fecha', date.today().isoformat()), data.get('numero_remito',''),
         int(data.get('proveedor_id',0)), data.get('proveedor_nombre',''),
         int(data.get('producto_id',0)), data.get('codigo_interno',''),
         data.get('descripcion',''), float(data.get('cantidad',1)),
         float(data.get('costo_unitario',0)), total, data.get('observaciones','')))

    # Update stock and cost
    pid = int(data.get('producto_id',0))
    if pid:
        c.execute("UPDATE stock SET stock_actual=stock_actual+?, ultimo_ingreso=? WHERE producto_id=?",
                  (float(data.get('cantidad',1)), data.get('fecha', date.today().isoformat()), pid))
        # Update cost if provided
        nuevo_costo = float(data.get('costo_unitario',0))
        if nuevo_costo > 0:
            c.execute("UPDATE productos SET costo=? WHERE id=?", (nuevo_costo, pid))

    conn.commit()
    conn.close()

# ─── CAJA ────────────────────────────────────────────────────────────────────
def get_caja_hoy():
    today = date.today().isoformat()
    row = q("SELECT * FROM caja_historial WHERE fecha=?", (today,), fetchone=True)
    if not row:
        return None
    return dict(row)

def abrir_caja(saldo_apertura, responsable):
    today = date.today().isoformat()
    hora = datetime.now().strftime('%H:%M')
    q("""INSERT OR IGNORE INTO caja_historial (fecha,saldo_apertura,responsable_apertura,hora_apertura,cerrada)
        VALUES (?,?,?,?,0)""",
      (today, saldo_apertura, responsable, hora), fetchall=False, commit=True)

def cerrar_caja(saldo_real, responsable):
    today = date.today().isoformat()
    hora = datetime.now().strftime('%H:%M')
    row = get_caja_hoy()
    if not row:
        return
    total_ventas = (row['ventas_efectivo'] + row['ventas_debito'] + row['ventas_credito'] +
                    row['ventas_qr'] + row['ventas_cta_cte'] + row['ventas_transferencia'])
    esperado = row['saldo_apertura'] + row.get('ventas_efectivo',0) - row.get('gastos_dia',0)
    diferencia = saldo_real - esperado
    q("""UPDATE caja_historial SET total_ventas=?,saldo_cierre_esperado=?,saldo_cierre_real=?,
        diferencia=?,cerrada=1,responsable_cierre=?,hora_cierre=? WHERE fecha=?""",
      (total_ventas, esperado, saldo_real, diferencia, responsable, hora, today),
      fetchall=False, commit=True)

def get_caja_historial(limit=60):
    return q("SELECT * FROM caja_historial ORDER BY fecha DESC LIMIT ?", (limit,))

def add_gasto_caja(monto):
    today = date.today().isoformat()
    q("""INSERT INTO caja_historial (fecha,gastos_dia) VALUES (?,?)
        ON CONFLICT(fecha) DO UPDATE SET gastos_dia=gastos_dia+excluded.gastos_dia""",
      (today, monto), fetchall=False, commit=True)

# ─── GASTOS ──────────────────────────────────────────────────────────────────
def get_gastos(search='', limit=500):
    sql = "SELECT * FROM gastos WHERE 1=1"
    params = []
    if search:
        sql += " AND (descripcion LIKE ? OR categoria LIKE ? OR proveedor LIKE ?)"
        params += [f'%{search}%'] * 3
    sql += " ORDER BY fecha DESC LIMIT ?"
    params.append(limit)
    return q(sql, params)

def add_gasto(data):
    monto = float(data.get('monto', 0))
    q("""INSERT INTO gastos (fecha,tipo,categoria,descripcion,monto,iva_incluido,medio_pago,proveedor,necesario,comprobante,observaciones)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
      (data.get('fecha', date.today().isoformat()), data.get('tipo','Gasto'),
       data.get('categoria',''), data.get('descripcion',''), monto,
       int(data.get('iva_incluido',1)), data.get('medio_pago','Efectivo'),
       data.get('proveedor',''), data.get('necesario','SI (necesario)'),
       data.get('comprobante',''), data.get('observaciones','')),
      fetchall=False, commit=True)
    if data.get('tipo','Gasto') == 'Gasto':
        add_gasto_caja(monto)

def update_gasto(gid, data):
    q("""UPDATE gastos SET fecha=?,tipo=?,categoria=?,descripcion=?,monto=?,iva_incluido=?,
        medio_pago=?,proveedor=?,necesario=?,comprobante=?,observaciones=? WHERE id=?""",
      (data.get('fecha'), data.get('tipo','Gasto'), data.get('categoria',''),
       data.get('descripcion',''), float(data.get('monto',0)), int(data.get('iva_incluido',1)),
       data.get('medio_pago','Efectivo'), data.get('proveedor',''),
       data.get('necesario','SI (necesario)'), data.get('comprobante',''),
       data.get('observaciones',''), gid),
      fetchall=False, commit=True)

def delete_gasto(gid):
    q("DELETE FROM gastos WHERE id=?", (gid,), fetchall=False, commit=True)

# ─── CC CLIENTES ─────────────────────────────────────────────────────────────
def get_cc_movimientos(cliente_id):
    return q("SELECT * FROM cc_clientes_mov WHERE cliente_id=? ORDER BY fecha DESC, id DESC", (cliente_id,))

def add_cc_mov(cliente_id, data):
    q("""INSERT INTO cc_clientes_mov (cliente_id,fecha,tipo,numero_comprobante,debe,haber,vencimiento,observaciones)
        VALUES (?,?,?,?,?,?,?,?)""",
      (cliente_id, data.get('fecha', date.today().isoformat()), data.get('tipo','Venta'),
       data.get('numero_comprobante',''), float(data.get('debe',0)), float(data.get('haber',0)),
       data.get('vencimiento',''), data.get('observaciones','')),
      fetchall=False, commit=True)

def get_cc_clientes_resumen():
    rows = q("""SELECT cl.*, 
        COALESCE(SUM(m.debe),0)-COALESCE(SUM(m.haber),0) as saldo_actual,
        MAX(m.vencimiento) as proximo_vto
        FROM clientes cl
        LEFT JOIN cc_clientes_mov m ON m.cliente_id=cl.id
        WHERE cl.activo=1
        GROUP BY cl.id ORDER BY cl.nombre""")
    return rows

# ─── CC PROVEEDORES ──────────────────────────────────────────────────────────
def get_facturas_proveedores(search=''):
    sql = """SELECT fp.*, p.nombre as proveedor_nombre_obj,
             fp.importe - fp.pagado as saldo,
             CASE
                WHEN fp.fecha_vencimiento < date('now') AND fp.importe > fp.pagado THEN 'VENCIDA'
                WHEN fp.fecha_vencimiento <= date('now','+30 days') AND fp.importe > fp.pagado THEN 'POR VENCER'
                WHEN fp.importe <= fp.pagado THEN 'PAGADA'
                ELSE 'VIGENTE'
             END as estado
             FROM facturas_proveedores fp
             JOIN proveedores p ON p.id=fp.proveedor_id
             WHERE 1=1"""
    params = []
    if search:
        sql += " AND (p.nombre LIKE ? OR fp.numero_factura LIKE ?)"
        params += [f'%{search}%'] * 2
    sql += " ORDER BY fp.fecha_vencimiento ASC"
    return q(sql, params)

def add_factura_proveedor(data):
    q("""INSERT INTO facturas_proveedores (proveedor_id,numero_factura,fecha,fecha_vencimiento,importe,pagado,observaciones)
        VALUES (?,?,?,?,?,?,?)""",
      (int(data['proveedor_id']), data.get('numero_factura',''),
       data.get('fecha', date.today().isoformat()), data['fecha_vencimiento'],
       float(data['importe']), float(data.get('pagado',0)), data.get('observaciones','')),
      fetchall=False, commit=True)

def pagar_factura(fid, monto):
    q("UPDATE facturas_proveedores SET pagado=pagado+? WHERE id=?", (monto, fid), fetchall=False, commit=True)

# ─── ESTADÍSTICAS ────────────────────────────────────────────────────────────
def get_ventas_por_mes(year=None):
    if not year:
        year = date.today().year
    rows = q("""SELECT strftime('%m',fecha) as mes,
                ROUND(SUM(total),2) as total,
                COUNT(DISTINCT id) as tickets
                FROM ventas WHERE strftime('%Y',fecha)=? GROUP BY mes ORDER BY mes""",
             (str(year),))
    result = {}
    for r in rows:
        result[int(r['mes'])] = {'total': r['total'], 'tickets': r['tickets']}
    return result

def get_ventas_por_semana(weeks=8):
    rows = []
    today = date.today()
    for i in range(weeks-1, -1, -1):
        start = today - timedelta(days=today.weekday()) - timedelta(weeks=i)
        end = start + timedelta(days=6)
        r = q("SELECT ROUND(SUM(total),2) as total, COUNT(id) as tickets FROM ventas WHERE fecha>=? AND fecha<=?",
              (start.isoformat(), end.isoformat()), fetchone=True)
        rows.append({
            'label': f'{start.strftime("%d/%m")}-{end.strftime("%d/%m")}',
            'total': r['total'] or 0,
            'tickets': r['tickets'] or 0,
        })
    return rows

def get_top_productos(limit=10, fecha_desde='', fecha_hasta=''):
    sql = """SELECT d.descripcion, d.categoria,
                ROUND(SUM(d.cantidad),2) as total_unidades,
                ROUND(SUM(d.subtotal),2) as total_pesos,
                COUNT(DISTINCT d.venta_id) as num_ventas
             FROM ventas_detalle d
             JOIN ventas v ON v.id=d.venta_id
             WHERE 1=1"""
    params = []
    if fecha_desde:
        sql += " AND v.fecha>=?"; params.append(fecha_desde)
    if fecha_hasta:
        sql += " AND v.fecha<=?"; params.append(fecha_hasta)
    sql += f" GROUP BY d.descripcion ORDER BY total_pesos DESC LIMIT ?"
    params.append(limit)
    return q(sql, params)

def get_bottom_productos(limit=10):
    sql = """SELECT d.descripcion, d.categoria,
                ROUND(SUM(d.cantidad),2) as total_unidades,
                ROUND(SUM(d.subtotal),2) as total_pesos
             FROM ventas_detalle d
             JOIN ventas v ON v.id=d.venta_id
             WHERE v.fecha >= date('now','-90 days')
             GROUP BY d.descripcion ORDER BY total_pesos ASC LIMIT ?"""
    return q(sql, (limit,))

def get_ventas_por_medio_pago(year=None, month=None):
    if not year: year = date.today().year
    if not month: month = date.today().month
    return q("""SELECT medio_pago, ROUND(SUM(total),2) as total, COUNT(id) as ops
                FROM ventas WHERE strftime('%Y',fecha)=? AND strftime('%m',fecha)=?
                GROUP BY medio_pago ORDER BY total DESC""",
             (str(year), f'{month:02d}'))

def get_ventas_por_temporada():
    return q("""SELECT temporada, ROUND(SUM(total),2) as total, COUNT(id) as tickets
                FROM ventas WHERE temporada!=''
                GROUP BY temporada ORDER BY total DESC""")

def get_ventas_por_categoria(fecha_desde='', fecha_hasta=''):
    sql = """SELECT d.categoria, ROUND(SUM(d.subtotal),2) as total,
                ROUND(SUM(d.cantidad),2) as unidades
             FROM ventas_detalle d JOIN ventas v ON v.id=d.venta_id WHERE 1=1"""
    params = []
    if fecha_desde:
        sql += " AND v.fecha>=?"; params.append(fecha_desde)
    if fecha_hasta:
        sql += " AND v.fecha<=?"; params.append(fecha_hasta)
    sql += " GROUP BY d.categoria ORDER BY total DESC"
    return q(sql, params)

def get_rentabilidad_mes(year=None, month=None):
    if not year: year = date.today().year
    if not month: month = date.today().month
    ym = f"{year}-{month:02d}"
    ventas_r = q("SELECT ROUND(SUM(total),2) as v FROM ventas WHERE strftime('%Y-%m',fecha)=?", (ym,), fetchone=True)
    gastos_r = q("SELECT ROUND(SUM(monto),2) as g FROM gastos WHERE tipo='Gasto' AND strftime('%Y-%m',fecha)=?", (ym,), fetchone=True)
    gastos_prescrind = q("SELECT ROUND(SUM(monto),2) as g FROM gastos WHERE tipo='Gasto' AND necesario='NO (prescindible)' AND strftime('%Y-%m',fecha)=?", (ym,), fetchone=True)
    ventas = ventas_r['v'] or 0
    gastos = gastos_r['g'] or 0
    prescind = gastos_prescrind['g'] or 0
    return {
        'ventas': ventas,
        'gastos': gastos,
        'utilidad': ventas - gastos,
        'rentabilidad': (ventas - gastos) / ventas * 100 if ventas else 0,
        'gastos_prescindibles': prescind,
        'mes': month,
        'anio': year,
    }

def get_dashboard_kpis():
    today = date.today().isoformat()
    month = date.today().strftime('%Y-%m')
    r_hoy = q("SELECT ROUND(SUM(total),2) as v, COUNT(id) as t FROM ventas WHERE fecha=?", (today,), fetchone=True)
    r_mes = q("SELECT ROUND(SUM(total),2) as v FROM ventas WHERE strftime('%Y-%m',fecha)=?", (month,), fetchone=True)
    gastos_mes = q("SELECT ROUND(SUM(monto),2) as g FROM gastos WHERE tipo='Gasto' AND strftime('%Y-%m',fecha)=?", (month,), fetchone=True)
    alertas = get_alertas_count()
    fact_venc = q("""SELECT COUNT(*) as n FROM facturas_proveedores
        WHERE fecha_vencimiento <= date('now','+30 days') AND importe > pagado""", fetchone=True)
    return {
        'ventas_hoy': r_hoy['v'] or 0,
        'tickets_hoy': r_hoy['t'] or 0,
        'ventas_mes': r_mes['v'] or 0,
        'gastos_mes': gastos_mes['g'] or 0,
        'sin_stock': alertas['sin_stock'],
        'stock_critico': alertas['critico'],
        'facturas_por_vencer': fact_venc['n'] or 0,
    }

# ─── EXPORTS ─────────────────────────────────────────────────────────────────
def get_catalogo_export():
    """Full product catalog with stock for export"""
    return q("""
        SELECT p.codigo_interno, p.codigo_barras, p.descripcion, p.categoria,
               p.unidad, p.por_peso, p.costo, p.precio_venta, p.iva,
               CASE WHEN p.costo>0 THEN ROUND((p.precio_venta-p.costo)/p.costo*100,2) ELSE 0 END as margen_pct,
               COALESCE(s.stock_actual,0) as stock_actual,
               COALESCE(s.stock_minimo,0) as stock_minimo,
               COALESCE(s.stock_maximo,0) as stock_maximo,
               COALESCE(s.proveedor_habitual,'') as proveedor_habitual,
               CASE
                   WHEN COALESCE(s.stock_actual,0)<=0 THEN 'SIN STOCK'
                   WHEN COALESCE(s.stock_actual,0)<=COALESCE(s.stock_minimo,0) THEN 'CRITICO'
                   WHEN COALESCE(s.stock_actual,0)<=COALESCE(s.stock_minimo,0)*1.5 THEN 'BAJO'
                   WHEN COALESCE(s.stock_actual,0)>=COALESCE(s.stock_maximo,50) THEN 'EXCESO'
                   ELSE 'NORMAL'
               END as estado_stock,
               COALESCE(s.stock_actual,0)*p.costo as valor_stock
        FROM productos p
        LEFT JOIN stock s ON s.producto_id=p.id
        WHERE p.activo=1
        ORDER BY p.categoria, p.descripcion
    """)

# ─── CATEGORÍAS CRUD ─────────────────────────────────────────────────────────
def update_categoria(old_nombre, new_nombre):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE categorias SET nombre=? WHERE nombre=?", (new_nombre, old_nombre))
    c.execute("UPDATE productos SET categoria=? WHERE categoria=?", (new_nombre, old_nombre))
    conn.commit()
    conn.close()

def delete_categoria(nombre):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM categorias WHERE nombre=?", (nombre,))
    conn.commit()
    conn.close()

def get_categoria_by_nombre(nombre):
    return q("SELECT * FROM categorias WHERE nombre=?", (nombre,), fetchone=True)

# ─── CLIENTES CRUD ───────────────────────────────────────────────────────────
def delete_cliente(cid):
    q("UPDATE clientes SET activo=0 WHERE id=?", (cid,), fetchall=False, commit=True)

def update_cliente(cid, data):
    q("""UPDATE clientes SET nombre=?,dni_cuit=?,telefono=?,email=?,limite_credito=?
         WHERE id=?""",
      (data.get('nombre',''), data.get('dni_cuit',''), data.get('telefono',''),
       data.get('email',''), float(data.get('limite_credito',0) or 0), cid),
      fetchall=False, commit=True)

def get_clientes_con_saldo():
    return q("""
        SELECT cl.*,
            COALESCE(SUM(m.debe),0)-COALESCE(SUM(m.haber),0) as saldo_actual,
            MAX(CASE WHEN m.debe>0 THEN m.vencimiento ELSE NULL END) as proximo_vto
        FROM clientes cl
        LEFT JOIN cc_clientes_mov m ON m.cliente_id=cl.id
        WHERE cl.activo=1
        GROUP BY cl.id ORDER BY cl.nombre
    """)

# ─── PROVEEDORES CRUD ────────────────────────────────────────────────────────
def delete_proveedor(pid):
    q("UPDATE proveedores SET activo=0 WHERE id=?", (pid,), fetchall=False, commit=True)

def update_proveedor(pid, data):
    q("""UPDATE proveedores SET nombre=?,cuit=?,telefono=?,email=?,dias_credito=?
         WHERE id=?""",
      (data.get('nombre',''), data.get('cuit',''), data.get('telefono',''),
       data.get('email',''), int(data.get('dias_credito',30) or 30), pid),
      fetchall=False, commit=True)

# ─── BÚSQUEDA INSTANTÁNEA POS ────────────────────────────────────────────────
def buscar_productos_pos(term, limit=10):
    """Search products for POS instant search"""
    if not term or len(term.strip()) < 2:
        return []
    t = f'%{term.strip()}%'
    return q("""
        SELECT p.id, p.codigo_interno, p.codigo_barras, p.descripcion,
               p.categoria, p.unidad, p.por_peso, p.precio_venta,
               COALESCE(s.stock_actual, 0) as stock_actual
        FROM productos p
        LEFT JOIN stock s ON s.producto_id=p.id
        WHERE p.activo=1
          AND (p.descripcion LIKE ? OR p.codigo_interno LIKE ? OR p.codigo_barras LIKE ? OR p.categoria LIKE ?)
        ORDER BY p.descripcion
        LIMIT ?
    """, (t, t, t, t, limit))

# ─── FACTURA PROVEEDOR DELETE ─────────────────────────────────────────────────
def delete_factura_proveedor(fid):
    q("DELETE FROM facturas_proveedores WHERE id=?", (fid,), fetchall=False, commit=True)

# ─── CC MOV DELETE ───────────────────────────────────────────────────────────
def delete_cc_mov(mid):
    q("DELETE FROM cc_clientes_mov WHERE id=?", (mid,), fetchall=False, commit=True)

# ─── AUTH ────────────────────────────────────────────────────────────────────

def get_usuario(username: str):
    return q("SELECT * FROM usuarios WHERE username=? AND activo=1", (username,), fetchone=True)

def verificar_password(username: str, password: str):
    u = get_usuario(username)
    if not u: return None
    if check_password_hash(u['password_hash'], password):
        return dict(u)
    return None

def get_usuarios():
    return q("SELECT id,username,rol,nombre_completo,activo FROM usuarios ORDER BY rol,username")

def crear_usuario(username, password, rol, nombre):
    try:
        q("INSERT INTO usuarios (username,password_hash,rol,nombre_completo) VALUES (?,?,?,?)",
          (username.strip(), generate_password_hash(password), rol, nombre.strip()),
          fetchall=False, commit=True)
        return True
    except Exception:
        return False

def cambiar_password(uid, nueva):
    q("UPDATE usuarios SET password_hash=? WHERE id=?", (generate_password_hash(nueva), uid), fetchall=False, commit=True)

def toggle_usuario(uid):
    q("UPDATE usuarios SET activo=CASE WHEN activo=1 THEN 0 ELSE 1 END WHERE id=?", (uid,), fetchall=False, commit=True)

def delete_usuario(uid):
    q("DELETE FROM usuarios WHERE id=? AND rol!='admin'", (uid,), fetchall=False, commit=True)

def editar_usuario(uid, nombre, rol):
    q("UPDATE usuarios SET nombre_completo=?, rol=? WHERE id=?", (nombre, rol, uid), fetchall=False, commit=True)

# ─── DEMO / LICENCIA RSA ─────────────────────────────────────────────────────
#
# Validación por firma digital RSA.
# La clave PRIVADA vive solo en el generador (licencias_fh).
# Aquí solo está la clave PÚBLICA: sirve para verificar, no para firmar.
# Sin la privada es imposible generar un token válido.

import base64 as _base64

# ─── DEMO / LICENCIA RSA ─────────────────────────────────────────────────────
# Verificacion RSA usando SOLO stdlib Python (base64, hashlib).
# Sin cryptography, sin rsa, sin pyasn1.
# Funciona en cualquier exe PyInstaller sin instalar nada extra.

import base64 as _base64
import hashlib as _hashlib_rsa

# Cargar clave pública desde variable de entorno PUBLIC_KEY, o fallback a keys/public_key.asc
public_key_str = (os.getenv("PUBLIC_KEY") or "").strip()
if not public_key_str:
    # Soporte compatibilidad con builds .deb/instalación local
    possible_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys', 'public_key.asc'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public_key.asc'),
    ]
    for p in possible_paths:
        if os.path.isfile(p):
            with open(p, 'r', encoding='utf-8') as f:
                public_key_str = f.read().strip()
            break

if not public_key_str:
    raise RuntimeError(
        '❌ Clave pública no encontrada. Definí PUBLIC_KEY o colocá keys/public_key.asc.'
    )
_ALMACEN_PUBLIC_KEY_PEM = public_key_str.encode('utf-8')

# SHA256 DigestInfo header (RFC 3447 / PKCS1v15)
_SHA256_HEADER = bytes([
    0x30,0x31,0x30,0x0d,0x06,0x09,0x60,0x86,0x48,0x01,
    0x65,0x03,0x04,0x02,0x01,0x05,0x00,0x04,0x20
])


def _parse_asn1_len(data, pos):
    b = data[pos]; pos += 1
    if b < 0x80:
        return b, pos
    n = b & 0x7f
    return int.from_bytes(data[pos:pos+n], 'big'), pos + n


def _parse_asn1_int(data, pos):
    assert data[pos] == 0x02; pos += 1
    length, pos = _parse_asn1_len(data, pos)
    return int.from_bytes(data[pos:pos+length], 'big'), pos + length


def _load_pubkey():
    """Extrae (n, e) de la clave publica PEM usando solo stdlib."""
    lines = _ALMACEN_PUBLIC_KEY_PEM.strip().split(b'\n')
    der = _base64.b64decode(b''.join(l for l in lines if not l.startswith(b'-----')))
    pos = 0
    assert der[pos] == 0x30; pos += 1
    _, pos = _parse_asn1_len(der, pos)
    assert der[pos] == 0x30; pos += 1
    alg_len, pos = _parse_asn1_len(der, pos)
    pos += alg_len
    assert der[pos] == 0x03; pos += 1
    _, pos = _parse_asn1_len(der, pos)
    pos += 1
    assert der[pos] == 0x30; pos += 1
    _, pos = _parse_asn1_len(der, pos)
    n, pos = _parse_asn1_int(der, pos)
    e, _   = _parse_asn1_int(der, pos)
    return n, e


def _rsa_verify(message: bytes, signature: bytes) -> bool:
    """Verifica firma PKCS1v15 SHA256 usando solo aritmetica entera."""
    try:
        n, e = _load_pubkey()
        k = (n.bit_length() + 7) // 8
        if len(signature) != k:
            return False
        m = pow(int.from_bytes(signature, 'big'), e, n).to_bytes(k, 'big')
        if m[0] != 0x00 or m[1] != 0x01:
            return False
        sep = m.find(b'\x00', 2)
        if sep < 0 or any(b != 0xFF for b in m[2:sep]):
            return False
        return m[sep+1:] == _SHA256_HEADER + _hashlib_rsa.sha256(message).digest()
    except Exception:
        return False


def get_machine_id() -> str:
    r = q("SELECT valor FROM config WHERE clave='machine_id'", fetchone=True)
    return r['valor'] if r else 'UNKNOWN'


def is_demo_mode() -> bool:
    cfg = get_config()
    return cfg.get('demo_mode', '1') == '1'


def get_demo_status() -> dict:
    cfg  = get_config()
    demo = cfg.get('demo_mode', '1') == '1'
    if not demo:
        return {'demo': False, 'dias_restantes': 0, 'vencido': False,
                'aviso_proximo': False, 'install_date': '', 'dias_usados': 0}
    # Verificar fecha de instalación con anti-reinstall
    machine_id  = get_machine_id()
    telem_date  = _read_telemetry(machine_id)
    install_str = cfg.get('demo_install_date', '')

    if telem_date:
        # El archivo externo es la fuente de verdad
        if telem_date != install_str:
            # La DB fue reseteada — restaurar fecha original
            set_config({'demo_install_date': telem_date})
            install_str = telem_date
    elif install_str:
        # Archivo no existe pero DB tiene fecha — crear archivo
        _write_telemetry(install_str, machine_id)
    # Si ninguno tiene fecha, init_db() ya lo maneja
    dias_demo   = int(cfg.get('demo_dias', '30'))
    try:
        install_dt = date.fromisoformat(install_str)
    except Exception:
        install_dt = date.today()
        set_config({'demo_install_date': install_dt.isoformat()})
    dias_usados    = (date.today() - install_dt).days
    dias_restantes = max(0, dias_demo - dias_usados)
    vencido        = dias_restantes == 0
    aviso_proximo  = not vencido and dias_restantes <= 7
    return {
        'demo':            demo,
        'install_date':    install_str,
        'dias_usados':     dias_usados,
        'dias_restantes':  dias_restantes,
        'dias_demo':       dias_demo,
        'vencido':         vencido,
        'aviso_proximo':   aviso_proximo,
        'ventas_bloqueado':    vencido,
        'productos_bloqueado': vencido,
        'ventas':           0,
        'ventas_limit':     0,
        'ventas_pct':       min(100, int(dias_usados / dias_demo * 100)),
    }


def get_license_info() -> dict:
    cfg = get_config()
    return {
        'type':         cfg.get('license_type', 'DEMO'),
        'tier':         cfg.get('license_tier', 'DEMO'),
        'max_machines': int(cfg.get('license_max_machines', '1')),
        'license_key':  cfg.get('license_key', ''),
        'activated_at': cfg.get('license_activated_at', ''),
        'expires_at':   cfg.get('license_expires_at', ''),
    }


def validar_licencia_rsa(token_b64: str) -> tuple:
    try:
        import json as _json
        try:
            data = _json.loads(_base64.b64decode(token_b64.strip()).decode())
        except Exception:
            return False, "El token no es valido. Verifica que lo hayas copiado completo.", None
        if data.get("product") != "almacen":
            return False, "Este token no es una licencia de Nexar Almacen.", None
        sig_hex = data.get("public_signature", "")
        if not sig_hex:
            return False, "El token no contiene firma digital.", None
        try:
            signature = bytes.fromhex(sig_hex)
        except ValueError:
            return False, "La firma digital del token esta corrupta.", None

        is_multi = "hardware_ids" in data

        # Reconstruir payload exactamente igual que el generador
        # Incluye tier y expires_at en la firma
        if is_multi:
            payload_dict = {
                "expires_at":   data.get("expires_at"),
                "hardware_ids": sorted(data["hardware_ids"]),
                "license_key":  data["license_key"],
                "max_machines": data["max_machines"],
                "product":      "almacen",
                "tier":         data.get("tier", "BASICA"),
                "type":         data["type"],
            }
        else:
            payload_dict = {
                "expires_at":   data.get("expires_at"),
                "hardware_id":  data["hardware_id"],
                "license_key":  data["license_key"],
                "max_machines": data["max_machines"],
                "product":      "almacen",
                "tier":         data.get("tier", "BASICA"),
                "type":         data["type"],
            }

        payload_bytes = _json.dumps(payload_dict, sort_keys=True).encode()
        if not _rsa_verify(payload_bytes, signature):
            return False, "La firma digital es invalida. El token fue alterado o no corresponde a este sistema.", None

        machine_id = get_machine_id()
        if is_multi:
            authorized = machine_id in data.get("hardware_ids", [])
        else:
            authorized = (machine_id == data.get("hardware_id"))

        if not authorized:
            mid = machine_id
            mid_fmt = f"{mid[:4]}-{mid[4:8]}-{mid[8:12]}-{mid[12:16]}"
            return False, f"Esta licencia no esta autorizada para esta computadora.\nTu ID es: {mid_fmt}\nContacta al desarrollador.", None

        return True, "OK", data
    except Exception as ex:
        return False, f"Error al validar la licencia: {ex}", None


def activar_licencia(token_b64: str) -> tuple:
    ok, msg, data = validar_licencia_rsa(token_b64)
    if not ok:
        return False, msg
    from datetime import datetime as _dt
    tier       = data.get("tier", "BASICA")
    expires_at = data.get("expires_at") or ""
    set_config({
        'demo_mode':            '0',
        'license_type':         data.get('type', 'MONO'),
        'license_tier':         tier,
        'license_max_machines': str(data.get('max_machines', 1)),
        'license_key':          data.get('license_key', ''),
        'license_activated_at': _dt.now().isoformat(),
        'license_expires_at':   expires_at,
    })
    return True, "Licencia activada correctamente."


def get_changelog():
    return q("SELECT * FROM changelog ORDER BY id DESC")

def add_changelog_entry(version, tipo, titulo, descripcion=''):
    q("INSERT INTO changelog (version,fecha,tipo,titulo,descripcion) VALUES (?,?,?,?,?)",
      (version, date.today().isoformat(), tipo, titulo, descripcion),
      fetchall=False, commit=True)

# ─── PRODUCTOS: importación masiva ────────────────────────────────────────────
def import_productos_bulk(productos: list) -> dict:
    """
    Importa una lista de dicts con: barcode, name, brand, category.
    Inserta nuevos, actualiza existentes (nombre/marca/categoría).
    Devuelve: {nuevos: int, actualizados: int, sin_cambios: int, errores: int}
    """
    stats = {'nuevos': 0, 'actualizados': 0, 'sin_cambios': 0, 'errores': 0}
    conn = get_conn()
    try:
        c = conn.cursor()
        # Sync counter with max existing PRD to avoid UNIQUE conflicts
        max_row = c.execute(
            "SELECT codigo_interno FROM productos WHERE codigo_interno LIKE 'PRD-%' "
            "ORDER BY CAST(SUBSTR(codigo_interno,5) AS INTEGER) DESC LIMIT 1"
        ).fetchone()
        if max_row:
            try:
                counter = int(max_row['codigo_interno'].split('-')[1]) + 1
            except Exception:
                counter = 1000
        else:
            row = c.execute("SELECT valor FROM config WHERE clave='siguiente_codigo'").fetchone()
            counter = int(row['valor'] if row else 1)

        for p in productos:
            barcode  = str(p.get('barcode', '')).strip()
            name     = str(p.get('name', '')).strip()
            brand    = str(p.get('brand', '')).strip()
            cat      = str(p.get('category', 'Almacén')).strip()
            unit     = str(p.get('unit', 'Unidad')).strip()
            por_peso = int(p.get('por_peso', 0))

            if not name or not barcode:
                stats['errores'] += 1
                continue

            # Check existing by barcode
            existing = c.execute(
                "SELECT id, descripcion, marca, categoria FROM productos WHERE codigo_barras=?",
                (barcode,)
            ).fetchone()

            if existing:
                changed = (existing['descripcion'] != name or
                           existing['marca'] != brand or
                           existing['categoria'] != cat)
                if changed:
                    c.execute(
                        "UPDATE productos SET descripcion=?, marca=?, categoria=? WHERE id=?",
                        (name, brand, cat, existing['id'])
                    )
                    stats['actualizados'] += 1
                else:
                    stats['sin_cambios'] += 1
            else:
                # New product
                codigo_int = f"PRD-{counter:04d}"
                try:
                    c.execute(
                        """INSERT INTO productos
                           (codigo_interno, codigo_barras, descripcion, marca, categoria,
                            unidad, por_peso, costo, precio_venta, activo)
                           VALUES (?,?,?,?,?,?,?,0,0,1)""",
                        (codigo_int, barcode, name, brand, cat, unit, por_peso)
                    )
                    pid = c.lastrowid
                    c.execute(
                        "INSERT OR IGNORE INTO stock (producto_id, stock_actual, stock_minimo, stock_maximo) VALUES (?,0,5,50)",
                        (pid,)
                    )
                    counter += 1
                    stats['nuevos'] += 1
                except Exception:
                    stats['errores'] += 1

        # Update counter
        c.execute("INSERT OR REPLACE INTO config VALUES ('siguiente_codigo',?)", (str(counter),))
        conn.commit()
    finally:
        conn.close()
    return stats


# ─── BLACKLIST ────────────────────────────────────────────────────────────────

def _ensure_blacklist_table():
    """Migración: crea la tabla si no existe en DBs antiguas."""
    q("""CREATE TABLE IF NOT EXISTS barcode_blacklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE NOT NULL,
            nombre_producto TEXT DEFAULT '',
            motivo TEXT DEFAULT '',
            fecha TEXT DEFAULT CURRENT_DATE
        )""")


def get_blacklist():
    """Retorna todos los barcodes bloqueados, ordenados por fecha desc."""
    _ensure_blacklist_table()
    return q("SELECT * FROM barcode_blacklist ORDER BY id DESC")


def add_to_blacklist(barcode: str, nombre_producto: str = '', motivo: str = '') -> bool:
    """
    Agrega un barcode a la lista negra.
    Retorna True si se agregó, False si ya existía.
    """
    _ensure_blacklist_table()
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO barcode_blacklist (barcode, nombre_producto, motivo) VALUES (?,?,?)",
            (barcode.strip(), nombre_producto.strip(), motivo.strip())
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False  # ya existía (UNIQUE)
    finally:
        conn.close()


def remove_from_blacklist(barcode: str) -> bool:
    """Elimina un barcode de la lista negra. Retorna True si existía."""
    _ensure_blacklist_table()
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM barcode_blacklist WHERE barcode=?", (barcode.strip(),))
    deleted = c.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def is_blacklisted(barcode: str) -> bool:
    """Verifica si un barcode está en la lista negra."""
    _ensure_blacklist_table()
    row = q("SELECT id FROM barcode_blacklist WHERE barcode=?",
            (barcode.strip(),), fetchone=True)
    return row is not None


def get_blacklist_set() -> set:
    """Retorna el set completo de barcodes bloqueados (eficiente para bulk checks)."""
    _ensure_blacklist_table()
    rows = q("SELECT barcode FROM barcode_blacklist")
    return {r['barcode'] for r in rows}

def get_tier() -> str:
    """
    Devuelve el tier activo: 'DEMO', 'BASICA' o 'PRO'.
    Si es PRO pero venció, devuelve 'BASICA' (mantiene acceso básico).
    """
    cfg = get_config()
    if cfg.get('demo_mode', '1') == '1':
        return 'DEMO'
    tier = cfg.get('license_tier', 'BASICA')
    if tier == 'PRO':
        expires_at = cfg.get('license_expires_at', '')
        if expires_at:
            try:
                from datetime import date
                if date.today() > date.fromisoformat(expires_at):
                    return 'BASICA'   # Pro vencido → baja a Básica, no a Demo
            except Exception:
                pass
    return tier


def is_pro_expired() -> bool:
    """True si tenía Pro pero venció."""
    cfg = get_config()
    if cfg.get('demo_mode', '1') == '1':
        return False
    if cfg.get('license_tier', 'BASICA') != 'PRO':
        return False
    expires_at = cfg.get('license_expires_at', '')
    if not expires_at:
        return False
    try:
        from datetime import date
        return date.today() > date.fromisoformat(expires_at)
    except Exception:
        return False


def check_tier_limit(recurso: str) -> dict:
    """
    Verifica si se puede crear un nuevo recurso según el tier activo.

    recurso: 'clientes' | 'proveedores' | 'productos_off'

    Retorna:
        {'ok': True}  → puede crear
        {'ok': False, 'actual': N, 'limite': N, 'tier': 'BASICA'}  → bloqueado
    """
    tier = get_tier()
    limite = TIER_LIMITS.get(tier, {}).get(recurso)
    if limite is None:
        return {'ok': True}   # ilimitado en este tier

    # Contar actuales en DB
    conteos = {
        'clientes':      "SELECT COUNT(*) FROM clientes WHERE activo=1",
        'proveedores':   "SELECT COUNT(*) FROM proveedores WHERE activo=1",
        'productos_off': (
            "SELECT COUNT(*) FROM productos "
            "WHERE activo=1 AND codigo_barras != '' "
            "AND (codigo_barras LIKE '779%' OR codigo_barras LIKE '780%')"
        ),
    }
    sql = conteos.get(recurso)
    if not sql:
        return {'ok': True}

    row = q(sql, fetchone=True)
    actual = row[0] if row else 0

    if actual >= limite:
        return {'ok': False, 'actual': actual, 'limite': limite, 'tier': tier}
    return {'ok': True}
