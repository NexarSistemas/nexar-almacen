#!/bin/bash
set -e

# =========================
# CONFIG
# =========================
APP_NAME="nexar-stock"
ENTRY_POINT="app.py"
ARCH="amd64"

# Version desde entorno o fallback
VERSION=${VERSION:-"dev-$(git rev-parse --short HEAD)"}

BUILD_ROOT="build_linux"
DIST_DIR="dist"
DEB_DIR="$BUILD_ROOT/deb"
PKG_NAME="${APP_NAME}_${VERSION}"
PKG_DIR="$DEB_DIR/$PKG_NAME"

ICON_SRC="build/linux/assets/nexar-stock.png"

echo "======================================"
echo "   NEXAR STOCK - LINUX BUILD"
echo "======================================"
echo "Version: $VERSION"

# =========================
# LIMPIEZA
# =========================
echo "Limpiando..."
rm -rf build dist __pycache__ *.spec "$BUILD_ROOT"

# =========================
# BUILD PORTABLE (PyInstaller)
# =========================
echo "Generando portable..."

pyinstaller \
  --onefile \
  --name "$APP_NAME" \
  --add-data "templates:templates" \
  --add-data "static:static" \
  "$ENTRY_POINT"

if [ ! -f "$DIST_DIR/$APP_NAME" ]; then
  echo "❌ Error: no se generó el binario"
  exit 1
fi

echo "✔ Portable listo: $DIST_DIR/$APP_NAME"

# =========================
# ESTRUCTURA DEB
# =========================
echo "Creando estructura .deb..."

mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/local/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/pixmaps"

# =========================
# BINARIO
# =========================
cp "$DIST_DIR/$APP_NAME" "$PKG_DIR/usr/local/bin/$APP_NAME"
chmod +x "$PKG_DIR/usr/local/bin/$APP_NAME"

# =========================
# ICONO
# =========================
if [ -f "$ICON_SRC" ]; then
  cp "$ICON_SRC" "$PKG_DIR/usr/share/pixmaps/$APP_NAME.png"
  echo "✔ Icono agregado"
else
  echo "⚠️ Icono no encontrado: $ICON_SRC"
fi

# =========================
# DESKTOP ENTRY
# =========================
cat <<EOF > "$PKG_DIR/usr/share/applications/$APP_NAME.desktop"
[Desktop Entry]
Name=Nexar Stock
Exec=$APP_NAME
Icon=$APP_NAME
Type=Application
Categories=Office;
Terminal=false
StartupNotify=true
EOF

chmod 644 "$PKG_DIR/usr/share/applications/$APP_NAME.desktop"

# =========================
# CONTROL FILE
# =========================
cat <<EOF > "$PKG_DIR/DEBIAN/control"
Package: $APP_NAME
Version: $VERSION
Section: office
Priority: optional
Architecture: $ARCH
Maintainer: Rolo
Depends: libc6
Description: Nexar Stock - Sistema de gestión de inventario profesional
EOF

chmod 644 "$PKG_DIR/DEBIAN/control"

# =========================
# POSTINST (opcional PRO)
# =========================
cat <<EOF > "$PKG_DIR/DEBIAN/postinst"
#!/bin/bash
set -e
update-desktop-database || true
echo "Nexar Stock instalado correctamente"
EOF

chmod 755 "$PKG_DIR/DEBIAN/postinst"

# =========================
# BUILD DEB
# =========================
echo "Construyendo .deb..."

dpkg-deb --build "$PKG_DIR"

FINAL_DEB="${APP_NAME}-${VERSION}.deb"
mv "${PKG_DIR}.deb" "$FINAL_DEB"

# =========================
# OUTPUT FINAL
# =========================
mkdir -p release

cp "$DIST_DIR/$APP_NAME" "release/${APP_NAME}-linux-portable-${VERSION}"
cp "$FINAL_DEB" "release/${APP_NAME}-linux-installer-${VERSION}.deb"

echo "======================================"
echo "✔ BUILD COMPLETO"
echo "======================================"
echo "Portable: release/${APP_NAME}-linux-portable-${VERSION}"
echo "DEB:      release/${APP_NAME}-linux-installer-${VERSION}.deb"