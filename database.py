import sqlite3
import os
import hashlib as _hashlib
import hmac as _hmac
import time as _time
from datetime import datetime, date, timedelta
from calendar import month_name

# Ruta de la base de datos:
# 1. Variable de entorno ALMACEN_DB_PATH (instaladores .deb y Windows)
# 2. En Windows sin env var: %APPDATA%\AlmacenGestion\almacen.db  (evita readonly en Program Files)
# 3. Fallback: junto al script (portable/Linux)
def _resolve_db_path():
    env = os.environ.get('ALMACEN_DB_PATH', '')
    if env:
        return env
    if os.name == 'nt':  # Windows
        appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
        data_dir = os.path.join(appdata, 'AlmacenGestion')
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, 'almacen.db')
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'almacen.db')

DB_PATH = _resolve_db_path()

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
         'Primera versión del Sistema de Gestión para Almacenes con módulos de Ventas, Stock, Caja y Gastos.'),
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

    # Fix install date: set once, never overwrite
    inst = c.execute("SELECT valor FROM config WHERE clave='demo_install_date'").fetchone()
    if not inst or not inst['valor']:
        today = date.today().isoformat()
        c.execute("INSERT OR REPLACE INTO config VALUES ('demo_install_date',?)", (today,))

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
    _seed_demo_data()

def _seed_demo_data():
    """Insert demo products and sample data if DB is empty"""
    # Use config flag to avoid re-seeding if user deleted demo data
    cfg = get_config()
    if cfg.get('demo_seeded') == '1':
        return
    if q("SELECT COUNT(*) as n FROM productos", fetchone=True)['n'] > 0:
        # Products exist, just mark as seeded
        set_config({'demo_seeded': '1'})
        return

    productos = [
        ('PRD-0001','7790580001001','Leche entera 1L','Lácteos','Litro',0,450,700,'21%'),
        ('PRD-0002','7790580001002','Yogur entero 200g','Lácteos','Unidad',0,180,300,'21%'),
        ('PRD-0003','7790895901003','Aceite girasol 900ml','Aceites / Condimentos / Salsas','Unidad',0,800,1200,'21%'),
        ('PRD-0004','7791234000004','Arroz 000 1Kg','Cereales / Harinas / Pastas','Unidad',0,320,500,'10.5%'),
        ('PRD-0005','7790895905005','Fideos spaghetti 500g','Cereales / Harinas / Pastas','Unidad',0,250,400,'10.5%'),
        ('PRD-0006','7792222000006','Coca Cola 1.5L','Bebidas','Unidad',0,600,950,'21%'),
        ('PRD-0007','7792222000007','Agua mineral 1.5L','Bebidas','Unidad',0,250,400,'21%'),
        ('PRD-0008','7791234000008','Mate La Jerba 500g','Infusiones','Unidad',0,800,1250,'10.5%'),
        ('PRD-0009','7790895900009','Azúcar 1Kg','No Perecederos','Unidad',0,380,600,'10.5%'),
        ('PRD-0010','7790580000010','Harina 000 1Kg','Cereales / Harinas / Pastas','Unidad',0,300,480,'10.5%'),
        ('PRD-0011','','Jamón cocido','Fiambres (x peso)','Kg',1,3800,6500,'21%'),
        ('PRD-0012','','Queso cremoso','Fiambres (x peso)','Kg',1,4200,7000,'21%'),
        ('PRD-0013','','Pan francés','Pan / Panadería (x peso)','Kg',1,600,1000,'0%'),
        ('PRD-0014','','Tomate','Verduras / Frutas (x peso)','Kg',1,400,800,'0%'),
        ('PRD-0015','7794000000015','Jabón en polvo 1Kg','Limpieza del Hogar','Unidad',0,900,1450,'21%'),
        ('PRD-0016','7794000000016','Lavandina 1L','Limpieza del Hogar','Unidad',0,350,600,'21%'),
        ('PRD-0017','7794111000017','Champú 400ml','Higiene Personal','Unidad',0,700,1100,'21%'),
        ('PRD-0018','7793000000018','Papel higiénico x4','Papel / Descartables','Pack',0,550,900,'21%'),
        ('PRD-0019','7791234000019','Café molido 250g','Infusiones','Unidad',0,650,1050,'10.5%'),
        ('PRD-0020','7790895900020','Sal fina 500g','No Perecederos','Unidad',0,120,200,'10.5%'),
        ('PRD-0021','7792000000021','Gaseosa Pepsi 2.25L','Bebidas','Unidad',0,580,920,'21%'),
        ('PRD-0022','7791000000022','Galletitas 150g','Golosinas / Confitería','Unidad',0,200,350,'10.5%'),
        ('PRD-0023','7792500000023','Cerveza 1L','Bebidas Alcohólicas','Unidad',0,900,1500,'21%'),
        ('PRD-0024','','Manzana verde','Verduras / Frutas (x peso)','Kg',1,350,700,'0%'),
        ('PRD-0025','7793500000025','Detergente 500ml','Limpieza del Hogar','Unidad',0,280,450,'21%'),
    ]

    conn = get_conn()
    c = conn.cursor()

    stock_vals = [
        (10,5,30),(8,5,20),(25,10,60),(30,10,80),(20,10,60),
        (15,10,50),(20,10,60),(12,5,30),(40,15,100),(35,15,100),
        (2,1,5),(3,1,5),(5,2,15),(8,3,20),(6,3,20),
        (12,5,30),(4,3,15),(10,5,30),(8,4,20),(50,20,120),
        (12,8,40),(20,10,50),(8,5,25),(6,2,15),(15,8,40),
    ]

    for i, p in enumerate(productos):
        c.execute("""INSERT INTO productos
            (codigo_interno,codigo_barras,descripcion,categoria,unidad,por_peso,costo,precio_venta,iva)
            VALUES (?,?,?,?,?,?,?,?,?)""", p)
        pid = c.lastrowid
        st = stock_vals[i]
        c.execute("INSERT INTO stock (producto_id,stock_actual,stock_minimo,stock_maximo) VALUES (?,?,?,?)",
                  (pid, st[0], st[1], st[2]))

    # Demo clients
    clients = [
        ('CLI-001','García, María','DNI 25.000.001','11-1111-1111','','30000'),
        ('CLI-002','López, Juan Carlos','DNI 30.500.002','11-2222-2222','','50000'),
        ('CLI-003','Fernández, Ana','DNI 28.300.003','11-3333-3333','','20000'),
        ('CLI-004','Martínez, Pedro','DNI 22.100.005','11-4444-4444','','35000'),
    ]
    for cl in clients:
        c.execute("INSERT INTO clientes (codigo,nombre,dni_cuit,telefono,email,limite_credito) VALUES (?,?,?,?,?,?)", cl)

    # Demo suppliers
    provs = [
        ('PROV-001','Lácteos del Sur SRL','30-70111222-3','011-4001-0001','ventas@lacteos.com',30),
        ('PROV-002','Distribuidora Norte SA','30-70333444-5','011-4002-0002','pedidos@norte.com',15),
        ('PROV-003','Bebidas & Más','30-70555666-7','011-4003-0003','comercial@bymas.com',30),
        ('PROV-004','Limpieza Total','30-70777888-9','011-4004-0004','limpiezatotal@email.com',7),
        ('PROV-005','Todo en Harinas','30-70900100-1','011-4005-0005','',15),
    ]
    for p in provs:
        c.execute("INSERT INTO proveedores (codigo,nombre,cuit,telefono,email,dias_credito) VALUES (?,?,?,?,?,?)", p)

    conn.commit()

    # Demo sales for last 90 days
    import random
    random.seed(42)
    seasons = {1:'Verano',2:'Verano',3:'Verano',4:'Otoño',5:'Otoño',
               6:'Invierno',7:'Invierno',8:'Invierno',9:'Primavera',
               10:'Primavera',11:'Primavera',12:'Verano'}
    medios = ['Efectivo','Efectivo','Efectivo','Débito','QR / Billetera Virtual','Transferencia']
    prods_list = c.execute("SELECT id, codigo_interno, descripcion, categoria, unidad, precio_venta FROM productos WHERE por_peso=0").fetchall()
    ticket_num = 1001

    today = date.today()
    for day_offset in range(90, 0, -1):
        sale_date = today - timedelta(days=day_offset)
        date_str = sale_date.isoformat()
        season = seasons[sale_date.month]
        daily = random.randint(4, 12)
        for _ in range(daily):
            prod = random.choice(prods_list)
            qty = random.randint(1, 3)
            dto = random.choice([0.0, 0.0, 0.0, 0.05, 0.10])
            price = prod['precio_venta']
            subtot = round(qty * price * (1 - dto), 2)
            medio = random.choice(medios)
            c.execute("""INSERT INTO ventas (numero_ticket,fecha,hora,cliente_nombre,medio_pago,subtotal,total,temporada)
                VALUES (?,?,?,?,?,?,?,?)""",
                (ticket_num, date_str, '10:00', 'Mostrador', medio, subtot, subtot, season))
            vid = c.lastrowid
            c.execute("""INSERT INTO ventas_detalle
                (venta_id,producto_id,codigo_interno,descripcion,categoria,unidad,cantidad,precio_unitario,descuento,subtotal)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (vid, prod['id'], prod['codigo_interno'], prod['descripcion'],
                 prod['categoria'], prod['unidad'], qty, price, dto, subtot))
            ticket_num += 1

    # Demo expenses
    today_str = today.isoformat()
    exp_data = [
        (today_str, 'Gasto', 'Alquiler', 'Alquiler local', 80000, 'Transferencia', 'Propietario', 'SI (necesario)'),
        ((today - timedelta(days=30)).isoformat(), 'Gasto', 'Alquiler', 'Alquiler local', 80000, 'Transferencia', 'Propietario', 'SI (necesario)'),
        ((today - timedelta(days=5)).isoformat(), 'Gasto', 'Servicios', 'Factura luz', 12000, 'Efectivo', 'EDESUR', 'SI (necesario)'),
        ((today - timedelta(days=10)).isoformat(), 'Gasto', 'Internet/Teléfono', 'Internet fibra', 6500, 'Débito', 'Telecom', 'SI (necesario)'),
        ((today - timedelta(days=15)).isoformat(), 'Gasto', 'Publicidad', 'Redes sociales', 3000, 'QR / Billetera Virtual', 'Meta Ads', 'NO (prescindible)'),
        ((today - timedelta(days=20)).isoformat(), 'Gasto', 'Mantenimiento', 'Reparación heladera', 15000, 'Efectivo', 'Técnico', 'SI (necesario)'),
        ((today - timedelta(days=3)).isoformat(), 'Gasto', 'Impuestos/Tasas', 'Ingresos brutos', 18000, 'Transferencia', 'AFIP', 'SI (necesario)'),
    ]
    for e in exp_data:
        c.execute("""INSERT INTO gastos (fecha,tipo,categoria,descripcion,monto,medio_pago,proveedor,necesario)
            VALUES (?,?,?,?,?,?,?,?)""", e)

    # Demo supplier invoices
    inv_data = [
        (1, 'FAC-0001', (today - timedelta(days=5)).isoformat(), (today + timedelta(days=25)).isoformat(), 45000, 0),
        (2, 'FAC-0002', (today - timedelta(days=10)).isoformat(), (today + timedelta(days=5)).isoformat(), 32000, 0),
        (3, 'FAC-0003', (today - timedelta(days=2)).isoformat(), (today + timedelta(days=28)).isoformat(), 67000, 0),
        (4, 'FAC-0004', (today - timedelta(days=8)).isoformat(), (today - timedelta(days=1)).isoformat(), 15000, 0),
    ]
    for inv in inv_data:
        c.execute("""INSERT INTO facturas_proveedores (proveedor_id,numero_factura,fecha,fecha_vencimiento,importe,pagado)
            VALUES (?,?,?,?,?,?)""", inv)

    conn.commit()
    conn.close()
    print("[DB] Demo data seeded successfully")
    set_config({'demo_seeded': '1'})

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

def _hash_pw(pw: str) -> str:
    return _hashlib.sha256(pw.encode()).hexdigest()

def get_usuario(username: str):
    return q("SELECT * FROM usuarios WHERE username=? AND activo=1", (username,), fetchone=True)

def verificar_password(username: str, password: str):
    u = get_usuario(username)
    if not u: return None
    if u['password_hash'] == _hash_pw(password):
        return dict(u)
    return None

def get_usuarios():
    return q("SELECT id,username,rol,nombre_completo,activo FROM usuarios ORDER BY rol,username")

def crear_usuario(username, password, rol, nombre):
    try:
        q("INSERT INTO usuarios (username,password_hash,rol,nombre_completo) VALUES (?,?,?,?)",
          (username.strip(), _hash_pw(password), rol, nombre.strip()),
          fetchall=False, commit=True)
        return True
    except Exception:
        return False

def cambiar_password(uid, nueva):
    q("UPDATE usuarios SET password_hash=? WHERE id=?", (_hash_pw(nueva), uid), fetchall=False, commit=True)

def toggle_usuario(uid):
    q("UPDATE usuarios SET activo=CASE WHEN activo=1 THEN 0 ELSE 1 END WHERE id=?", (uid,), fetchall=False, commit=True)

def delete_usuario(uid):
    q("DELETE FROM usuarios WHERE id=? AND rol!='admin'", (uid,), fetchall=False, commit=True)

def editar_usuario(uid, nombre, rol):
    q("UPDATE usuarios SET nombre_completo=?, rol=? WHERE id=?", (nombre, rol, uid), fetchall=False, commit=True)

# ─── DEMO / LICENCIA ─────────────────────────────────────────────────────────
_LICENSE_SECRET = b'ALMACEN_NAVARTA_2026_SECRET_KEY'

def get_machine_id() -> str:
    r = q("SELECT valor FROM config WHERE clave='machine_id'", fetchone=True)
    return r['valor'] if r else 'UNKNOWN'

def is_demo_mode() -> bool:
    cfg = get_config()
    return cfg.get('demo_mode', '1') == '1'

def get_demo_status() -> dict:
    """Returns demo status based on 30-day install date (not quantity limits)."""
    cfg = get_config()
    demo = cfg.get('demo_mode', '1') == '1'

    if not demo:
        return {'demo': False, 'dias_restantes': 0, 'vencido': False,
                'aviso_proximo': False, 'install_date': '', 'dias_usados': 0}

    install_str = cfg.get('demo_install_date', '')
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
        # Legacy compatibility keys (kept so templates don't crash)
        'ventas_bloqueado':    vencido,
        'productos_bloqueado': vencido,
        'ventas':           0,
        'ventas_limit':     0,
        'ventas_pct':       min(100, int(dias_usados / dias_demo * 100)),
    }

def generar_codigo_activacion(machine_id: str) -> str:
    """Generate activation code for a machine_id. Used by the generator app."""
    raw = _hmac.new(_LICENSE_SECRET, machine_id.encode(), _hashlib.sha256).hexdigest().upper()
    # Format as XXXX-XXXX-XXXX-XXXX
    return f"{raw[0:4]}-{raw[4:8]}-{raw[8:12]}-{raw[12:16]}"

def validar_codigo_activacion(codigo: str) -> bool:
    """Validate activation code against this machine's ID."""
    mid = get_machine_id()
    expected = generar_codigo_activacion(mid)
    # normalize input
    codigo_norm = codigo.strip().upper().replace(' ', '')
    if '-' not in codigo_norm:
        codigo_norm = f"{codigo_norm[0:4]}-{codigo_norm[4:8]}-{codigo_norm[8:12]}-{codigo_norm[12:16]}"
    return _hmac.compare_digest(expected, codigo_norm)

def activar_licencia(codigo: str) -> bool:
    if validar_codigo_activacion(codigo):
        set_config({'demo_mode': '0'})
        return True
    return False

# ─── CHANGELOG ───────────────────────────────────────────────────────────────
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
