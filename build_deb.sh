#!/bin/bash
# ============================================================
# build_deb.sh — Genera el paquete .deb para Nexar Almacen
# Uso: bash build_deb.sh
# Requiere: dpkg-deb, python3
# ============================================================

set -e

VERSION="1.7.1"
PACKAGE="nexar-almacen"
ARCH="all"
MAINTAINER="Nexar Sistemas <nexarsistemas@outlook.com.ar>"
DESCRIPTION="Nexar Almacen — v${VERSION}"

# Directorio de trabajo
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build_deb"
PKG_DIR="${BUILD_DIR}/${PACKAGE}_${VERSION}"
INSTALL_DIR="${PKG_DIR}/opt/nexar-almacen"
DEBIAN_DIR="${PKG_DIR}/DEBIAN"

echo "=================================================="
echo "  Nexar Almacen — Builder .deb v${VERSION}"
echo "=================================================="

# Limpiar build anterior
rm -rf "${BUILD_DIR}"
mkdir -p "${INSTALL_DIR}"
mkdir -p "${DEBIAN_DIR}"
mkdir -p "${PKG_DIR}/usr/local/bin"
mkdir -p "${PKG_DIR}/usr/share/applications"
mkdir -p "${PKG_DIR}/usr/share/pixmaps"

echo "→ Copiando archivos del sistema..."

# Archivos principales
cp "${SCRIPT_DIR}/iniciar.py"          "${INSTALL_DIR}/"
cp "${SCRIPT_DIR}/app.py"              "${INSTALL_DIR}/"
cp "${SCRIPT_DIR}/database.py"         "${INSTALL_DIR}/"
cp "${SCRIPT_DIR}/openfoodfacts.py"    "${INSTALL_DIR}/"
cp "${SCRIPT_DIR}/productos_seed.py"   "${INSTALL_DIR}/"
cp "${SCRIPT_DIR}/license_verifier.py" "${INSTALL_DIR}/"
cp "${SCRIPT_DIR}/VERSION"             "${INSTALL_DIR}/"
cp "${SCRIPT_DIR}/CHANGELOG.md"        "${INSTALL_DIR}/"
cp "${SCRIPT_DIR}/README.md"           "${INSTALL_DIR}/"
cp "${SCRIPT_DIR}/LICENSE"             "${INSTALL_DIR}/"

# Carpetas
cp -r "${SCRIPT_DIR}/templates"   "${INSTALL_DIR}/"
cp -r "${SCRIPT_DIR}/static"      "${INSTALL_DIR}/"
cp -r "${SCRIPT_DIR}/services"    "${INSTALL_DIR}/"

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

# Icono
if [ -f "${SCRIPT_DIR}/static/icons/nexar_almacen_ico.png" ]; then
    cp "${SCRIPT_DIR}/static/icons/nexar_almacen_ico.png" \
       "${PKG_DIR}/usr/share/pixmaps/nexar-almacen.png"
fi

echo "→ Creando lanzador..."

cat > "${PKG_DIR}/usr/local/bin/almacen" << 'EOF'
#!/bin/bash
export ALMACEN_DB_PATH="${HOME}/.local/share/nexaralmacen/almacen.db"
mkdir -p "${HOME}/.local/share/nexaralmacen"
cd /opt/nexar-almacen
exec python3 iniciar.py "$@" || xdg-open http://127.0.0.1:5601
EOF
chmod +x "${PKG_DIR}/usr/local/bin/almacen"

echo "→ Creando entrada de menú..."

cat > "${PKG_DIR}/usr/share/applications/nexar-almacen.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Nexar Almacen
Comment=Control completo de ventas, stock, caja y más
Exec=/usr/local/bin/almacen
Icon=nexar-almacen
Terminal=false
Categories=Office;Finance;
EOF

echo "→ Calculando tamaño..."
INSTALLED_SIZE=$(du -sk "${INSTALL_DIR}" | cut -f1)

echo "→ Generando metadata..."

cat > "${DEBIAN_DIR}/control" << EOF
Package: ${PACKAGE}
Version: ${VERSION}
Architecture: ${ARCH}
Maintainer: ${MAINTAINER}
Installed-Size: ${INSTALLED_SIZE}
Depends: python3 (>= 3.8), python3-pip, python3-gi, gir1.2-gtk-3.0
Recommends: libwebkit2gtk-4.0-37
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

echo "Instalando dependencias de Nexar Almacen..."

python3 -m pip install --quiet --break-system-packages --ignore-installed \
    flask openpyxl reportlab pywebview python-dotenv
pip3 install --quiet \
    flask openpyxl reportlab pywebview python-dotenv 2>/dev/null || \
echo "Nota: algunas dependencias pueden instalarse al primer inicio."

chmod +x /usr/local/bin/almacen
chmod -R a+rX /opt/nexar-almacen

echo ""
echo "============================================"
echo " Nexar Almacen instalado correctamente"
echo "============================================"
echo " Ejecutar: almacen"
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
exit 0
EOF
chmod +x "${DEBIAN_DIR}/postrm"

echo "→ Construyendo .deb..."

DEB_FILE="${BUILD_DIR}/${PACKAGE}_${VERSION}_${ARCH}.deb"
dpkg-deb --build --root-owner-group "${PKG_DIR}" "${DEB_FILE}"

echo ""
echo "✅ Paquete generado:"
echo "${DEB_FILE}"