# ════════════════════════════════════════════════════════════
# build/nexar_almacen.spec — Configuración de PyInstaller
# ════════════════════════════════════════════════════════════

import os

PROJ = os.path.abspath(os.path.join(SPECPATH, '..'))

block_cipher = None

# ─────────────────────────────────────────────────────────────
# Validación de archivos críticos
# ─────────────────────────────────────────────────────────────
version_file = os.path.join(PROJ, 'VERSION')

if not os.path.exists(version_file):
    raise FileNotFoundError("❌ ERROR: Falta el archivo VERSION en la raíz del proyecto")

# ─────────────────────────────────────────────────────────────
# Archivos a incluir
# ─────────────────────────────────────────────────────────────
datas = [
    (os.path.join(PROJ, 'templates'),         'templates'),
    (os.path.join(PROJ, 'static'),            'static'),
    (os.path.join(PROJ, 'services'),          'services'),

    # 🔐 VERSIONADO (clave para tu pipeline)
    (version_file, '.'),

    # 📄 Metadata
    (os.path.join(PROJ, 'CHANGELOG.md'),      '.'),
    (os.path.join(PROJ, 'productos_seed.py'), '.'),
]

# ─────────────────────────────────────────────────────────────
# Clave pública (build dinámico)
# ─────────────────────────────────────────────────────────────
keys_path = os.path.join(PROJ, 'keys')

if os.path.isdir(keys_path):
    datas.append((keys_path, 'keys'))
else:
    public_key_txt = os.getenv('PUBLIC_KEY', '').strip()

    if public_key_txt:
        tmp_key_dir = os.path.join(PROJ, 'build_tmp_keys')
        os.makedirs(tmp_key_dir, exist_ok=True)

        tmp_key_file = os.path.join(tmp_key_dir, 'public_key.asc')

        with open(tmp_key_file, 'w', encoding='utf-8') as f:
            f.write(public_key_txt + ('\n' if not public_key_txt.endswith('\n') else ''))

        datas.append((tmp_key_file, 'keys'))

# ─────────────────────────────────────────────────────────────
# Análisis
# ─────────────────────────────────────────────────────────────
a = Analysis(
    scripts=[os.path.join(PROJ, 'iniciar.py')],
    pathex=[PROJ],
    binaries=[],
    datas=datas,

    hiddenimports=[
        # Flask
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

        # Proyecto
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

        # pywebview
        'webview',
        'webview.util',
        'webview.window',
        'webview.event',
        'webview.screen',
        'webview.guilib',
        'webview.platforms',
        'webview.platforms.winforms',
        'webview.platforms.edgechromium',

        # pythonnet
        'clr',
        'clr._extra_clr_loader',

        # stdlib
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

# ─────────────────────────────────────────────────────────────
# Empaquetado Python
# ─────────────────────────────────────────────────────────────
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

# ─────────────────────────────────────────────────────────────
# Ejecutable final
# ─────────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],

    name='NexarAlmacen',

    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,

    console=False,

    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,

    icon=os.path.join(PROJ, 'static', 'icons', 'nexar_almacen_ico.ico'),
)