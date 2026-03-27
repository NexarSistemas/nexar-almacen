#!/bin/bash
# ============================================================
# build_deb.sh — Genera el paquete .deb para Nexar Stock
# Uso: bash build_deb.sh
# Requiere: dpkg-deb, python3
# ============================================================

set -e

VERSION="1.6.0"
PACKAGE="nexar-stock"
ARCH="all"
MAINTAINER="Nexar Sistemas <nexarsistemas@outlook.com.ar>"
DESCRIPTION="Nexar Stock — v${VERSION}"

# Directorio de trabajo
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build_deb"
PKG_DIR="${BUILD_DIR}/${PACKAGE}_${VERSION}"
INSTALL_DIR="${PKG_DIR}/opt/nexar-stock"
DEBIAN_DIR="${PKG_DIR}/DEBIAN"

echo "=================================================="
echo "  Nexar Stock — Builder .deb v${VERSION}"
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
cp -r "${SCRIPT_DIR}/keys"        "${INSTALL_DIR}/"

# Eliminar __pycache__ y archivos temporales
find "${INSTALL_DIR}" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "${INSTALL_DIR}" -name "*.pyc" -delete 2>/dev/null || true
find "${INSTALL_DIR}" -name "*.db"  -delete 2>/dev/null || true
find "${INSTALL_DIR}" -name ".port" -delete 2>/dev/null || true

# Icono
if [ -f "${SCRIPT_DIR}/static/icons/nexar_stock_ico.png" ]; then
    cp "${SCRIPT_DIR}/static/icons/nexar_stock_ico.png" \
       "${PKG_DIR}/usr/share/pixmaps/nexar-stock.png"
fi

echo "→ Creando lanzador de terminal..."

# Script ejecutable en /usr/local/bin/almacen
cat > "${PKG_DIR}/usr/local/bin/almacen" << 'EOF'
#!/bin/bash
# Guardar DB en directorio del usuario, no en /opt (que es readonly)
export ALMACEN_DB_PATH="${HOME}/.local/share/nexarstock/almacen.db"
mkdir -p "${HOME}/.local/share/nexarstock"
cd /opt/nexar-stock
exec python3 iniciar.py "$@"
EOF
chmod +x "${PKG_DIR}/usr/local/bin/almacen"

echo "→ Creando entrada de menú de escritorio..."

# Entrada .desktop
cat > "${PKG_DIR}/usr/share/applications/nexar-stock.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Nexar Stock
GenericName=Nexar Stock
Comment=Control completo de ventas, stock, caja y más
Exec=/usr/local/bin/almacen
Icon=nexar-stock
Terminal=false
Categories=Office;Finance;
Keywords=almacen;ventas;stock;caja;gestion;
StartupNotify=true
EOF

echo "→ Calculando tamaño instalado..."
INSTALLED_SIZE=$(du -sk "${INSTALL_DIR}" | cut -f1)

echo "→ Generando metadata del paquete..."

# DEBIAN/control
cat > "${DEBIAN_DIR}/control" << EOF
Package: ${PACKAGE}
Version: ${VERSION}
Architecture: ${ARCH}
Maintainer: ${MAINTAINER}
Installed-Size: ${INSTALLED_SIZE}
Depends: python3 (>= 3.8), python3-pip, python3-gi
Recommends: python3-flask, python3-openpyxl
Section: misc
Priority: optional
Homepage: https://wa.me/5492645858874
Description: ${DESCRIPTION}
 Sistema completo de gestión para pequeños comercios.
 Incluye: Punto de Venta, Stock, Caja, Gastos, Cuentas Corrientes,
 Estadísticas, Importación desde OpenFoodFacts y más.
 Funciona localmente sin servidor externo.
 .
 Planes disponibles: Demo (30 días), Básico (pago único), Pro (mensual).
EOF

# DEBIAN/postinst — se ejecuta después de instalar
cat > "${DEBIAN_DIR}/postinst" << 'EOF'
#!/bin/bash
set -e

echo "Instalando dependencias de Python para Nexar Stock..."

# Instalar Flask, exportaciones y pywebview silenciosamente
# pywebview permite abrir la app en ventana nativa sin navegador externo
pip3 install --quiet --break-system-packages \
    flask openpyxl reportlab pywebview 2>/dev/null || \
pip3 install --quiet \
    flask openpyxl reportlab pywebview 2>/dev/null || \
echo "Nota: las dependencias se instalarán automáticamente al primer inicio."

# Permisos del ejecutable
chmod +x /usr/local/bin/almacen
chmod -R a+rX /opt/nexar-stock

echo ""
echo "================================================="
echo "  Nexar Stock v$(cat /opt/nexar-stock/VERSION) instalado"
echo "================================================="
echo "  Para iniciar: almacen"
echo "  O desde el menú de aplicaciones"
echo "================================================="

exit 0
EOF
chmod +x "${DEBIAN_DIR}/postinst"

# DEBIAN/prerm — se ejecuta antes de desinstalar
cat > "${DEBIAN_DIR}/prerm" << 'EOF'
#!/bin/bash
set -e
echo "Desinstalando Nexar Stock..."
echo "Nota: tus datos (almacen.db) en ~/.local/share/nexarstock/ NO se eliminan."
exit 0
EOF
chmod +x "${DEBIAN_DIR}/prerm"

# DEBIAN/postrm — se ejecuta después de desinstalar
cat > "${DEBIAN_DIR}/postrm" << 'EOF'
#!/bin/bash
set -e
# Limpiar entradas de menú obsoletas si las hay
update-desktop-database /usr/share/applications 2>/dev/null || true
exit 0
EOF
chmod +x "${DEBIAN_DIR}/postrm"

echo "→ Construyendo paquete .deb..."

# Construir el .deb
DEB_FILE="${BUILD_DIR}/${PACKAGE}_${VERSION}_${ARCH}.deb"
dpkg-deb --build --root-owner-group "${PKG_DIR}" "${DEB_FILE}"

echo ""
echo "=================================================="
echo "  ✅ Paquete generado exitosamente:"
echo "  ${DEB_FILE}"
echo ""
echo "  Para instalar:"
echo "  sudo dpkg -i ${DEB_FILE}"
echo ""
echo "  Para desinstalar:"
echo "  sudo apt remove nexar-stock"
echo "=================================================="
