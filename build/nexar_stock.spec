# ════════════════════════════════════════════════════════════
# build/nexar_stock.spec — Configuración de PyInstaller
#
# Genera un único .exe que incluye todo lo necesario para
# ejecutar Nexar Stock sin instalar Python.
#
# Para compilar manualmente desde la raíz del proyecto:
#   pyinstaller build/nexar_stock.spec --distpath dist --noconfirm
# ════════════════════════════════════════════════════════════

import os

# SPECPATH = directorio donde está este archivo (build/)
# Subimos un nivel para llegar a la raíz del proyecto
PROJ = os.path.abspath(os.path.join(SPECPATH, '..'))

block_cipher = None

a = Analysis(
    # Punto de entrada: el script que inicia el servidor Flask
    scripts=[os.path.join(PROJ, 'iniciar.py')],

    # Carpeta raíz para que Python encuentre los módulos del proyecto
    pathex=[PROJ],

    binaries=[],

    # Archivos que NO son código Python pero el programa necesita en runtime.
    # El formato es: (origen_en_disco, destino_dentro_del_exe)
    datas=[
        (os.path.join(PROJ, 'templates'),          'templates'),
        (os.path.join(PROJ, 'static'),             'static'),
        (os.path.join(PROJ, 'services'),           'services'),
        (os.path.join(PROJ, 'keys'),               'keys'),
        (os.path.join(PROJ, 'VERSION'),            '.'),
        (os.path.join(PROJ, 'CHANGELOG.md'),       '.'),
        (os.path.join(PROJ, 'productos_seed.py'),  '.'),
    ],

    # Módulos que PyInstaller no detecta automáticamente
    # porque se importan de forma dinámica o están en plugins
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
        # Exportaciones (Excel y PDF)
        'openpyxl',
        'reportlab',
        'reportlab.lib.pagesizes',
        'reportlab.platypus',
        'reportlab.lib.styles',
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

    # Módulos que excluimos para reducir el tamaño del .exe
    excludes=[
        'pywebview',     # se instala aparte si el usuario lo quiere
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'scipy',
        'cryptography',  # no se usa: el RSA está implementado con stdlib
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

    name='NexarStock',      # nombre del archivo .exe generado

    debug=False,            # cambiar a True solo si el .exe falla al abrir
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,               # compresión UPX: reduce el tamaño ~30%
    upx_exclude=[],
    runtime_tmpdir=None,

    # console=True → muestra ventana de terminal con los logs del servidor
    # console=False → ejecuta en segundo plano (sin logs visibles)
    # Recomendamos True durante las primeras versiones para poder ver errores
    console=True,

    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,

    # Ícono del ejecutable — si el archivo no existe el build falla.
    # Verificá que esta ruta sea correcta en tu repositorio.
    icon=os.path.join(PROJ, 'static', 'icons', 'nexar_stock_ico.ico'),
)