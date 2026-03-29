#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║   NEXAR ALMACEN  —  v1.7.0                                           ║
║   Creado por Nexar Sistemas · Desarrollado con Claude.ai · 2026     ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import sys
# Fix encoding para consola Windows (cp1252 no soporta caracteres Unicode)
# try/except porque en exe sin consola stdout/stderr pueden ser None
if sys.platform == 'win32':
    try:
        if sys.stdout is not None:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if sys.stderr is not None:
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
import os
import subprocess
import threading
import time
import webbrowser
import socket
import signal
import importlib.util

# Cuando corre como .exe PyInstaller los archivos están en sys._MEIPASS
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

IS_WIN   = sys.platform == 'win32'
IS_MAC   = sys.platform == 'darwin'
IS_FROZEN = getattr(sys, 'frozen', False)  # True cuando corre como .exe de PyInstaller

PORT_FILE = os.path.join(BASE_DIR, '.port')

# Garantizar que la DB apunte a AppData en Windows (antes de importar database o app)
if os.name == 'nt' and not os.environ.get('ALMACEN_DB_PATH'):
    _appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    _data_dir = os.path.join(_appdata, 'nexaralmacen')
    os.makedirs(_data_dir, exist_ok=True)
    os.environ['ALMACEN_DB_PATH'] = os.path.join(_data_dir, 'almacen.db')

# ─────────────────────────────────────────────
# Colores consola
# ─────────────────────────────────────────────
def verde(t): return f'\033[92m{t}\033[0m'
def rojo(t): return f'\033[91m{t}\033[0m'
def bold(t): return f'\033[1m{t}\033[0m'
def amarillo(t): return f'\033[93m{t}\033[0m'
def cyan(t): return f'\033[96m{t}\033[0m'

# ─────────────────────────────────────────────
# Verificar módulos
# ─────────────────────────────────────────────
def has_module(name):
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


# ─────────────────────────────────────────────
# Instalar dependencias obligatorias
# ─────────────────────────────────────────────
def install_required():
    # Cuando corre como .exe PyInstaller todo ya está embebido — no hay pip
    if IS_FROZEN:
        return

    needed = [p for p in ('flask','openpyxl','reportlab') if not has_module(p)]

    if not needed:
        return

    print(amarillo(f'  Instalando dependencias: {", ".join(needed)} ...'))

    try:
        subprocess.check_call(
            [sys.executable,'-m','pip','install','-q','--break-system-packages'] + needed
        )
        print(verde('  ✓ Dependencias instaladas'))
    except Exception:
        print(rojo('No se pudieron instalar dependencias'))
        sys.exit(1)


# ─────────────────────────────────────────────
# Instalar pywebview en background
# ─────────────────────────────────────────────
def try_install_webview_background():
    # Cuando corre como .exe PyInstaller no se puede instalar nada
    if IS_FROZEN:
        return

    if has_module("webview"):
        return

    def _install():
        try:
            subprocess.check_call(
                [sys.executable,'-m','pip','install','pywebview','-q','--break-system-packages']
            )
        except Exception:
            pass

    threading.Thread(target=_install, daemon=True).start()


# ─────────────────────────────────────────────
# Puerto libre
# ─────────────────────────────────────────────
def get_free_port(start=5100,end=5999):

    import random

    ports=list(range(start,end))
    random.shuffle(ports)

    for p in ports:
        try:
            with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1",p))
                return p
        except:
            continue

    return 5000


def save_port(port):
    try:
        with open(PORT_FILE,'w') as f:
            f.write(str(port))
    except:
        pass


# ─────────────────────────────────────────────
# Invalidar sesiones
# ─────────────────────────────────────────────
def invalidate_sessions():
    try:
        import database as db
        from datetime import datetime
        db.set_config({'sessions_invalidated_at':datetime.now().isoformat()})
    except:
        pass


# ─────────────────────────────────────────────
# Esperar Flask listo
# ─────────────────────────────────────────────
def wait_for_server(host,port):

    for _ in range(40):
        time.sleep(0.25)

        try:
            with socket.create_connection((host,port),timeout=1):
                return True
        except:
            pass

    return False


# ─────────────────────────────────────────────
# Banner
# ─────────────────────────────────────────────
def _read_version():
    try:
        return open(os.path.join(BASE_DIR,'VERSION')).read().strip()
    except Exception:
        return '1.7.0'


def print_banner(url):
    ver = _read_version()
    titulo = f'  🛒  NEXAR ALMACEN  v{ver}  '
    print()
    print(verde('╔'+'═'*54+'╗'))
    print(verde('║')+bold(titulo.ljust(54))+'   '+verde('║'))
    print(verde('╠'+'═'*54+'╣'))
    print(verde('║')+f'  URL:    {url}'.ljust(54)+verde('║'))
    print(verde('║')+'  Login:  admin  /  admin123'.ljust(54)+verde('║'))
    print(verde('║')+'  Ctrl+C para cerrar'.ljust(54)+verde('║'))
    print(verde('╚'+'═'*54+'╝'))
    print()


# ─────────────────────────────────────────────
# Señal salida
# ─────────────────────────────────────────────
def on_exit(signum=None,frame=None):

    print('\n'+amarillo('  Cerrando sistema...'))
    invalidate_sessions()
    print(verde('  ✓ Sistema cerrado\n'))
    sys.exit(0)

signal.signal(signal.SIGTERM,on_exit)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():

    print(bold('\n  Iniciando Nexar Almacen...\n'))

    print('  Verificando dependencias...',end=' ',flush=True)
    install_required()
    print(verde('OK'))

    try_install_webview_background()

    print('  Iniciando base de datos...',end=' ',flush=True)

    try:
        import database as db
        db.init_db()
        print(verde('OK'))
    except Exception as e:
        print(rojo(e))
        sys.exit(1)

    print('  Buscando puerto libre...',end=' ',flush=True)

    PORT=get_free_port()
    HOST='127.0.0.1'
    URL=f'http://{HOST}:{PORT}'

    save_port(PORT)

    print(verde(f'OK (puerto {PORT})'))

    print('  Cargando aplicación...',end=' ',flush=True)

    try:
        from app import app as flask_app
        print(verde('OK'))
    except Exception as e:
        print(rojo(e))
        sys.exit(1)

    print_banner(URL)

    # ─────────── Flask thread
    def start_flask():

        flask_app.run(
            host=HOST,
            port=PORT,
            debug=False,
            use_reloader=False,
            threaded=True
        )

    flask_thread=threading.Thread(target=start_flask,daemon=True)
    flask_thread.start()

    wait_for_server(HOST,PORT)

    # ─────────── UI
    if has_module("webview"):

        import webview

        print(cyan('  > Ventana independiente abierta (modo app nativa)'))

        webview.create_window(
            "Nexar Almacen",
            URL,
            width=1280,
            height=800,
            min_size=(900,600),
            resizable=True,
            confirm_close=True
        )

        webview.start()

        invalidate_sessions()
        sys.exit(0)

    else:

        print(cyan(f'  → Abriendo en navegador: {URL}'))
        webbrowser.open(URL)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__=="__main__":
    main()
