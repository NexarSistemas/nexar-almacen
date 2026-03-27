# ════════════════════════════════════════════════════════════
# build/nexar_stock.spec — Configuración de PyInstaller
#
# Genera un único .exe que incluye todo lo necesario para
# ejecutar Nexar Stock sin instalar Python.
#
# Para compilar manualmente desde la raíz del proyecto:
#   pyinstaller build/nexar_stock.spec --distpath dist --noconfirm
# ════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════
# build/nexar_stock.spec — Configuración de PyInstaller
# ════════════════════════════════════════════════════════════

import os

PROJ = os.path.abspath(os.path.join(SPECPATH, '..'))

block_cipher = None

a = Analysis(
    scripts=[os.path.join(PROJ, 'iniciar.py')],
    pathex=[PROJ],
    binaries=[],

    datas=[
        (os.path.join(PROJ, 'templates'),          'templates'),
        (os.path.join(PROJ, 'static'),             'static'),
        (os.path.join(PROJ, 'services'),           'services'),
        (os.path.join(PROJ, 'keys'),               'keys'),
        (os.path.join(PROJ, 'VERSION'),            '.'),
        (os.path.join(PROJ, 'CHANGELOG.md'),       '.'),
        (os.path.join(PROJ, 'productos_seed.py'),  '.'),
    ],

    hiddenimports=[
        # Flask y dependencias internas
        'flask',
        'flask.helpers',
        'flask.templating',
        'jinja2',
        'jinja2.ext',
        'werkzeug',
        'werkzeug.serving',
        'werkzeug.routing',
        'werkzeug.exceptions',
        'click',
        # Módulos del proyecto
        'app',
        'database',
        'openfoodfacts',
        'license_verifier',
        'productos_seed',
        'services',
        'services.openfood_importer',
        # Exportaciones
        'openpyxl',
        'reportlab',
        'reportlab.lib.pagesizes',
        'reportlab.platypus',
        'reportlab.lib.styles',
        # ─── CAMBIO: pywebview y pythonnet para ventana nativa ───────────
        # pywebview abre la app en una ventana independiente (sin navegador)
        # pythonnet le da acceso a las APIs de Windows/.NET
        'webview',
        'webview.util',
        'webview.window',
        'webview.event',
        'webview.screen',
        'webview.guilib',
        'webview.platforms',
        'webview.platforms.winforms',
        'webview.platforms.edgechromium',
        'clr',
        'clr._extra_clr_loader',
        # ─────────────────────────────────────────────────────────────────
        # Estándar Python
        'sqlite3',
        'json',
        'hashlib',
        'hmac',
        'uuid',
        'socket',
        'threading',
        'signal',
        'webbrowser',
        'importlib',
        'importlib.util',
        'calendar',
        'zipfile',
    ],

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],

    excludes=[
        # ─── CAMBIO: pywebview ya NO está aquí — se movió a hiddenimports ──
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'scipy',
        'cryptography',
        'pytest',
        'docutils',
        'pydoc',
    ],

    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],

    name='NexarStock',

    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,

    # ─── CAMBIO: console=False para que no aparezca la ventana negra ─────
    # El usuario ve directamente la ventana nativa de pywebview
    # Si necesitás ver errores durante el desarrollo, cambialo a True
    console=False,
    # ──────────────────────────────────────────────────────────────────────

    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,

    icon=os.path.join(PROJ, 'static', 'icons', 'nexar_stock_ico.ico'),
)