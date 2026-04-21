# ════════════════════════════════════════════════════════════
# build/nexar_almacen.spec — Configuración de PyInstaller
#
# Genera un único .exe que incluye todo lo necesario para
# ejecutar Nexar Almacen sin instalar Python.
#
# Para compilar manualmente desde la raíz del proyecto:
#   pyinstaller build/nexar_almacen.spec --distpath dist --noconfirm
# ════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════
# build/nexar_almacen.spec — Configuración de PyInstaller
# ════════════════════════════════════════════════════════════

import os

PROJ = os.path.abspath(os.path.join(SPECPATH, '..'))

block_cipher = None

datas = [
    (os.path.join(PROJ, 'templates'),         'templates'),
    (os.path.join(PROJ, 'static'),            'static'),
    (os.path.join(PROJ, 'services'),          'services'),
    (os.path.join(PROJ, 'nexar_licencias'),   'nexar_licencias'),
    (os.path.join(PROJ, 'VERSION'),           '.'),
    (os.path.join(PROJ, 'CHANGELOG.md'),      '.'),
    (os.path.join(PROJ, 'productos_seed.py'), '.'),
]

env_path = os.path.join(PROJ, '.env')
if os.path.isfile(env_path):
    datas.append((env_path, '.'))

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


a = Analysis(
    scripts=[os.path.join(PROJ, 'iniciar.py')],
    pathex=[PROJ],
    binaries=[],

    datas=datas,

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
        'services.runtime_config',
        'services.license_storage',
        'services.license_sdk',
        'services.supabase_license_api',
        'services.update_checker',
        'nexar_licencias',
        'nexar_licencias.cache',
        'nexar_licencias.config',
        'nexar_licencias.device',
        'nexar_licencias.plans',
        'nexar_licencias.validator',
        'nexar_licencias.verifier_local',
        'nexar_licencias.verifier_online',
        # Exportaciones
        'requests',
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

    name='NexarAlmacen',

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

    icon=os.path.join(PROJ, 'static', 'icons', 'nexar_almacen_ico.ico'),
)
