#!/bin/bash
# ============================================================
# build_deb.sh — Genera el paquete .deb para Nexar Almacen
# ============================================================

set -e

# ─────────────────────────────────────────────────────────────
# Obtener versión desde archivo VERSION (fuente única)
# ─────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VERSION_FILE="${SCRIPT_DIR}/VERSION"

if [ ! -f "$VERSION_FILE" ]; then
    echo "❌ ERROR: No existe el archivo VERSION"
    exit 1
fi

VERSION="$(cat "$VERSION_FILE" | tr -d ' \n\r')"

if [ -z "$VERSION" ]; then
    echo "❌ ERROR: VERSION está vacío"
    exit 1
fi

# ─────────────────────────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────────────────────────
PACKAGE="nexar-almacen"
ARCH="all"
MAINTAINER="Nexar Sistemas <nexarsistemas@outlook.com.ar>"
DESCRIPTION="Nexar Almacen — v${VERSION}"

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
exec python3 iniciar.py "$@"
EOF

chmod +x "${PKG_DIR}/usr/local/bin/almacen"

echo "→ Creando .desktop..."

cat > "${PKG_DIR}/usr/share/applications/nexar-almacen.desktop" << EOF
[Desktop Entry]
Version=${VERSION}
Type=Application
Name=Nexar Almacen
Comment=Control completo de ventas y stock
Exec=/usr/local/bin/almacen
Icon=nexar-almacen
Terminal=false
Categories=Office;Finance;
EOF

echo "→ Calculando tamaño..."
INSTALLED_SIZE=$(du -sk "${INSTALL_DIR}" | cut -f1)

echo "→ Generando control..."

cat > "${DEBIAN_DIR}/control" << EOF
Package: ${PACKAGE}
Version: ${VERSION}
Architecture: ${ARCH}
Maintainer: ${MAINTAINER}
Installed-Size: ${INSTALLED_SIZE}
Depends: python3 (>= 3.8), python3-pip
Section: misc
Priority: optional
Description: ${DESCRIPTION}
EOF

echo "→ Construyendo .deb..."

DEB_FILE="${BUILD_DIR}/${PACKAGE}_${VERSION}_${ARCH}.deb"
dpkg-deb --build --root-owner-group "${PKG_DIR}" "${DEB_FILE}"

echo ""
echo "✅ Paquete generado:"
echo "${DEB_FILE}"