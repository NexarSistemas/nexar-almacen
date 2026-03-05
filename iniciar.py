#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║   SISTEMA DE GESTIÓN PARA ALMACENES  —  v1.5.0                      ║
║   Creado por Rolando Navarta · Desarrollado con Claude.ai · 2026     ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import subprocess
import threading
import time
import webbrowser
import socket
import signal
import importlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

IS_WIN = sys.platform == 'win32'
IS_MAC = sys.platform == 'darwin'

def verde(t):    return f'\033[92m{t}\033[0m'   if not IS_WIN else t
def rojo(t):     return f'\033[91m{t}\033[0m'   if not IS_WIN else t
def bold(t):     return f'\033[1m{t}\033[0m'    if not IS_WIN else t
def amarillo(t): return f'\033[93m{t}\033[0m'   if not IS_WIN else t
def cyan(t):     return f'\033[96m{t}\033[0m'   if not IS_WIN else t

PORT_FILE = os.path.join(BASE_DIR, '.port')

# ── Colores Windows (habilitar ANSI en CMD/PowerShell) ───────────────────────
if IS_WIN:
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(
            ctypes.windll.kernel32.GetStdHandle(-11), 7)
        # Ahora sí funcionan los colores
        def verde(t):    return f'\033[92m{t}\033[0m'
        def rojo(t):     return f'\033[91m{t}\033[0m'
        def bold(t):     return f'\033[1m{t}\033[0m'
        def amarillo(t): return f'\033[93m{t}\033[0m'
        def cyan(t):     return f'\033[96m{t}\033[0m'
    except Exception:
        pass


# ── Verificar módulo sin importarlo ──────────────────────────────────────────
import importlib.util as _imp_util  # necesario en Python 3.10+

def has_module(name):
    try:
        return _imp_util.find_spec(name) is not None
    except Exception:
        try:
            __import__(name)
            return True
        except ImportError:
            return False


# ── Instalar dependencias OBLIGATORIAS (bloqueante, breve) ───────────────────
def install_required():
    """Solo flask, openpyxl, reportlab. Rápidos y necesarios."""
    needed = [p for p in ('flask', 'openpyxl', 'reportlab') if not has_module(p)]
    if not needed:
        return
    print(amarillo(f'  Instalando dependencias: {", ".join(needed)} ...'))
    for flags in [['--break-system-packages', '-q'], ['-q']]:
        try:
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install'] + flags + needed,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=120
            )
            print(verde('  ✓ Dependencias instaladas'))
            return
        except Exception:
            continue
    print(rojo(f'  ✗ No se pudieron instalar. Corré manualmente:'))
    print(rojo(f'    pip install {" ".join(needed)}'))
    sys.exit(1)


# ── Intentar instalar pywebview en BACKGROUND (nunca bloquea el inicio) ──────
def try_install_webview_background():
    """
    Intenta instalar pywebview en un hilo separado.
    El sistema inicia igual aunque no esté disponible.
    """
    if has_module('webview'):
        return

    def _install():
        try:
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', 'pywebview', '-q',
                 '--break-system-packages'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=60
            )
        except Exception:
            pass  # No es crítico

    threading.Thread(target=_install, daemon=True).start()


# ── Puerto aleatorio libre ────────────────────────────────────────────────────
def get_free_port(start=5100, end=5999):
    import random
    ports = list(range(start, end))
    random.shuffle(ports)
    for p in ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('127.0.0.1', p))
                return p
        except OSError:
            continue
    return 5000


def save_port(port):
    try:
        with open(PORT_FILE, 'w') as f:
            f.write(str(port))
    except Exception:
        pass


# ── Invalidar sesiones (fuerza re-login) ─────────────────────────────────────
def invalidate_sessions():
    try:
        import database as db
        from datetime import datetime
        db.set_config({'sessions_invalidated_at': datetime.now().isoformat()})
    except Exception:
        pass


# ── Ventana nativa con pywebview ─────────────────────────────────────────────
def try_native_window(url):
    if not has_module('webview'):
        return False
    try:
        import webview

        def run():
            webview.create_window(
                'Almacén Gestión',
                url,
                width=1280, height=800,
                resizable=True, min_size=(900, 600),
                confirm_close=True,
            )
            webview.start()
            # El usuario cerró la ventana → apagar
            invalidate_sessions()
            os.kill(os.getpid(), signal.SIGTERM)

        threading.Thread(target=run, daemon=False).start()
        return True
    except Exception:
        return False


# ── Abrir navegador cuando Flask esté listo ──────────────────────────────────
def open_browser_when_ready(url, port):
    def _try():
        for _ in range(30):
            time.sleep(0.4)
            try:
                with socket.create_connection(('127.0.0.1', port), timeout=0.5):
                    webbrowser.open(url)
                    return
            except Exception:
                continue
    threading.Thread(target=_try, daemon=True).start()


# ── Cerrar ventana del terminal (sin matar sesión del SO) ────────────────────
def close_terminal():
    time.sleep(1.0)
    try:
        if IS_WIN:
            import ctypes
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
        elif IS_MAC:
            subprocess.Popen(
                ['osascript', '-e',
                 'tell application "Terminal" to close front window'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            # Linux: xdotool si está disponible
            try:
                wid = subprocess.check_output(
                    ['xdotool', 'getactivewindow'],
                    stderr=subprocess.DEVNULL).decode().strip()
                subprocess.run(['xdotool', 'windowclose', wid],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
    except Exception:
        pass


# ── Señal de salida ───────────────────────────────────────────────────────────
def on_exit(signum=None, frame=None):
    print('\n' + amarillo('  Cerrando sistema...'))
    invalidate_sessions()
    print(verde('  ✓ Sistema cerrado\n'))
    os._exit(0)

signal.signal(signal.SIGTERM, on_exit)


# ── Banner ────────────────────────────────────────────────────────────────────
def print_banner(url):
    print()
    print(verde('╔' + '═' * 54 + '╗'))
    print(verde('║') + bold('  🛒  SISTEMA DE GESTIÓN PARA ALMACENES  v1.5.0  ') + '   ' + verde('║'))
    print(verde('╠' + '═' * 54 + '╣'))
    print(verde('║') + f'  URL:    {url}'.ljust(54) + verde('║'))
    print(verde('║') + '  Login:  admin  /  admin123'.ljust(54) + verde('║'))
    print(verde('║') + '  Ctrl+C para cerrar'.ljust(54) + verde('║'))
    print(verde('╚' + '═' * 54 + '╝'))
    print()


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print(bold('\n  Iniciando Sistema de Gestión para Almacenes...\n'))

    # 1. Dependencias obligatorias (solo si faltan, normalmente instantáneo)
    print('  Verificando dependencias...', end=' ', flush=True)
    install_required()
    print(verde('OK'))

    # 2. Intentar pywebview en background (nunca bloquea)
    try_install_webview_background()

    # 3. Base de datos
    print('  Iniciando base de datos...', end=' ', flush=True)
    try:
        import database as db
        db.init_db()
        print(verde('OK'))
    except Exception as e:
        print(rojo(f'ERROR: {e}'))
        sys.exit(1)

    # 4. Puerto libre
    print('  Buscando puerto libre...', end=' ', flush=True)
    PORT = get_free_port()
    save_port(PORT)
    HOST = '127.0.0.1'
    URL  = f'http://{HOST}:{PORT}'
    print(verde(f'OK (puerto {PORT})'))

    # 5. Importar Flask app
    print('  Cargando aplicación...', end=' ', flush=True)
    try:
        from app import app as flask_app
        print(verde('OK'))
    except Exception as e:
        print(rojo(f'ERROR: {e}'))
        sys.exit(1)

    # 6. Mostrar banner
    print_banner(URL)

    # 7. Arrancar Flask en hilo daemon
    flask_thread = threading.Thread(
        target=lambda: flask_app.run(
            debug=False, host=HOST, port=PORT, use_reloader=False),
        daemon=True
    )
    flask_thread.start()

    # Breve espera para que Flask esté escuchando
    for _ in range(15):
        time.sleep(0.3)
        try:
            with socket.create_connection((HOST, PORT), timeout=0.3):
                break
        except Exception:
            continue

    # 8. Abrir UI
    native = try_native_window(URL)
    if native:
        print(cyan('  → Ventana independiente abierta (modo app nativa)'))
    else:
        print(cyan(f'  → Abriendo en navegador: {URL}'))
        open_browser_when_ready(URL, PORT)

    # 9. Mantener proceso vivo
    try:
        while flask_thread.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        print('\n' + amarillo('  Cerrando sistema...'))
        invalidate_sessions()
        close_terminal()
        print(verde('  ✓ Sistema cerrado correctamente\n'))


if __name__ == '__main__':
    main()
