#!/bin/bash
# ============================================================
# build_deb.sh — Genera el paquete .deb para Nexar Almacen
# Uso: bash build_deb.sh
# Requiere:
#   - dist/NexarAlmacen    (binario compilado por PyInstaller)
#   - dpkg-deb, fakeroot
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VERSION="$(tr -d '[:space:]' < "${SCRIPT_DIR}/VERSION")"
PACKAGE="nexar-almacen"
ARCH="amd64"
MAINTAINER="Nexar Sistemas <nexarsistemas@outlook.com.ar>"
DESCRIPTION="Nexar Almacen — v${VERSION}"

BUILD_DIR="${SCRIPT_DIR}/build_deb"
PKG_DIR="${BUILD_DIR}/${PACKAGE}_${VERSION}"
INSTALL_DIR="${PKG_DIR}/opt/nexar-almacen"
DEBIAN_DIR="${PKG_DIR}/DEBIAN"
APP_BIN="${SCRIPT_DIR}/dist/NexarAlmacen"

echo "=================================================="
echo "  Nexar Almacen — Builder .deb v${VERSION}"
echo "=================================================="

# Verificar que el binario exista
if [ ! -f "${APP_BIN}" ]; then
  echo "No se encontro ${APP_BIN}"
  echo "Compila primero con PyInstaller:"
  echo "  pyinstaller build/nexar_almacen.spec --distpath dist --workpath build/work --noconfirm"
  exit 1
fi

# Limpiar build anterior
rm -rf "${BUILD_DIR}"
mkdir -p "${INSTALL_DIR}"
mkdir -p "${DEBIAN_DIR}"
mkdir -p "${PKG_DIR}/usr/local/bin"
mkdir -p "${PKG_DIR}/usr/share/applications"
mkdir -p "${PKG_DIR}/usr/share/pixmaps"
mkdir -p "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps"

echo "→ Copiando binario y recursos..."

# Binario compilado (OneFile)
cp "${APP_BIN}" "${INSTALL_DIR}/NexarAlmacen"
chmod +x "${INSTALL_DIR}/NexarAlmacen"

# Recursos del proyecto
cp -r "${SCRIPT_DIR}/templates"   "${INSTALL_DIR}/"
cp -r "${SCRIPT_DIR}/static"      "${INSTALL_DIR}/"
cp    "${SCRIPT_DIR}/VERSION"     "${INSTALL_DIR}/"
cp    "${SCRIPT_DIR}/CHANGELOG.md" "${INSTALL_DIR}/"

# Archivos opcionales de referencia
[ -f "${SCRIPT_DIR}/README.md" ] && cp "${SCRIPT_DIR}/README.md" "${INSTALL_DIR}/"
[ -f "${SCRIPT_DIR}/LICENSE"   ] && cp "${SCRIPT_DIR}/LICENSE"   "${INSTALL_DIR}/"
[ -f "${SCRIPT_DIR}/.env"      ] && cp "${SCRIPT_DIR}/.env"      "${INSTALL_DIR}/"

# Clave pública
if [ -d "${SCRIPT_DIR}/keys" ]; then
    cp -r "${SCRIPT_DIR}/keys" "${INSTALL_DIR}/"
elif [ -n "${PUBLIC_KEY:-}" ]; then
    mkdir -p "${INSTALL_DIR}/keys"
    printf '%s\n' "$PUBLIC_KEY" > "${INSTALL_DIR}/keys/public_key.asc"
fi

# Limpieza
find "${INSTALL_DIR}" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "${INSTALL_DIR}" -name "*.pyc" -delete 2>/dev/null || true
find "${INSTALL_DIR}" -name "*.db"  -delete 2>/dev/null || true
find "${INSTALL_DIR}" -name ".port" -delete 2>/dev/null || true

# Icono: se instalan los dos nombres para conservar compatibilidad con
# versiones anteriores y con el cache del menu de aplicaciones de GNOME.
if [ -f "${SCRIPT_DIR}/static/icons/nexar_almacen_ico.png" ]; then
    cp "${SCRIPT_DIR}/static/icons/nexar_almacen_ico.png" \
       "${PKG_DIR}/usr/share/pixmaps/nexar-almacen.png"
    cp "${SCRIPT_DIR}/static/icons/nexar_almacen_ico.png" \
       "${PKG_DIR}/usr/share/pixmaps/nexar_almacen.png"
    cp "${SCRIPT_DIR}/static/icons/nexar_almacen_ico.png" \
       "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps/nexar-almacen.png"
    cp "${SCRIPT_DIR}/static/icons/nexar_almacen_ico.png" \
       "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps/nexar_almacen.png"
fi

echo "→ Creando lanzador..."

cat > "${PKG_DIR}/usr/local/bin/almacen" << 'EOF'
#!/bin/bash
unset GSETTINGS_SCHEMA_DIR

if [ -n "${XDG_DATA_DIRS:-}" ]; then
  export XDG_DATA_DIRS="/usr/local/share:/usr/share:${XDG_DATA_DIRS}"
else
  export XDG_DATA_DIRS="/usr/local/share:/usr/share"
fi

export ALMACEN_DB_PATH="${HOME}/.local/share/nexaralmacen/almacen.db"
mkdir -p "${HOME}/.local/share/nexaralmacen"
cd /opt/nexar-almacen
exec ./NexarAlmacen "$@"
EOF
chmod +x "${PKG_DIR}/usr/local/bin/almacen"

echo "→ Creando entrada de menú..."

if [ -f "${SCRIPT_DIR}/build/nexar_almacen.desktop" ]; then
    cp "${SCRIPT_DIR}/build/nexar_almacen.desktop" \
       "${PKG_DIR}/usr/share/applications/nexar-almacen.desktop"
else
    cat > "${PKG_DIR}/usr/share/applications/nexar-almacen.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Nexar Almacen
Comment=Control completo de ventas, stock, caja y más
Exec=/usr/local/bin/almacen
Path=/opt/nexar-almacen
Icon=nexar-almacen
Terminal=false
Categories=Office;Finance;
StartupNotify=true
StartupWMClass=NexarAlmacen
EOF
fi

echo "→ Calculando tamaño..."
INSTALLED_SIZE=$(du -sk "${INSTALL_DIR}" | cut -f1)

echo "→ Generando metadata..."

cat > "${DEBIAN_DIR}/control" << EOF
Package: ${PACKAGE}
Version: ${VERSION}
Architecture: ${ARCH}
Maintainer: ${MAINTAINER}
Installed-Size: ${INSTALLED_SIZE}
Depends: libegl1, libgl1, libxcb-cursor0, libxcb-icccm4, libxcb-image0, libxcb-keysyms1, libxcb-render-util0, libxcb-shape0, libxcb-xinerama0, libxkbcommon-x11-0
Recommends: fonts-liberation
Section: misc
Priority: optional
Homepage: https://wa.me/5492645858874
Description: ${DESCRIPTION}
 Sistema completo de gestión para pequeños comercios.
EOF

# =========================
# POSTINST (FIX DOTENV)
# =========================
cat > "${DEBIAN_DIR}/postinst" << 'EOF'
#!/bin/bash
set -e

chmod +x /usr/local/bin/almacen
chmod +x /opt/nexar-almacen/NexarAlmacen
chmod -R a+rX /opt/nexar-almacen

update-desktop-database /usr/share/applications 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true

echo ""
echo "============================================"
echo " Nexar Almacen instalado correctamente"
echo "============================================"
echo " Ejecutar: almacen"
echo " O buscar Nexar Almacen en el menu de apps"
echo "============================================"

exit 0
EOF
chmod +x "${DEBIAN_DIR}/postinst"

# PRERM
cat > "${DEBIAN_DIR}/prerm" << 'EOF'
#!/bin/bash
set -e
echo "Desinstalando Nexar Almacen..."
exit 0
EOF
chmod +x "${DEBIAN_DIR}/prerm"

# POSTRM
cat > "${DEBIAN_DIR}/postrm" << 'EOF'
#!/bin/bash
set -e
update-desktop-database /usr/share/applications 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
exit 0
EOF
chmod +x "${DEBIAN_DIR}/postrm"

echo "→ Construyendo .deb..."

DEB_FILE="${BUILD_DIR}/${PACKAGE}_${VERSION}_${ARCH}.deb"
dpkg-deb --build --root-owner-group "${PKG_DIR}" "${DEB_FILE}"

echo ""
echo "✅ Paquete generado:"
echo "${DEB_FILE}"
cp "${DEB_FILE}" "${SCRIPT_DIR}/"
