#!/bin/bash
set -e

# =========================
# CONFIG
# =========================
APP_NAME="nexar-stock"
ENTRY_POINT="app.py"
ARCH="amd64"

# =========================
# VERSION (desde archivo)
# =========================
VERSION_FILE="$PROJECT_ROOT/version"

if [ ! -f "$VERSION_FILE" ]; then
  echo "❌ Error: no existe archivo version en $VERSION_FILE"
  exit 1
fi

VERSION_BASE=$(cat "$VERSION_FILE" | tr -d ' \n')

# opcional: agregar hash (recomendado para builds internos)
GIT_HASH=$(git rev-parse --short HEAD)

VERSION="${VERSION_BASE}+${GIT_HASH}"

# =========================
# PATHS (FIX robusto)
# =========================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

BUILD_ROOT="$PROJECT_ROOT/build_linux"
DIST_DIR="$PROJECT_ROOT/dist"
DEB_DIR="$BUILD_ROOT/deb"

PKG_NAME="${APP_NAME}_${VERSION}"
PKG_DIR="$DEB_DIR/$PKG_NAME"

ICON_SRC="$SCRIPT_DIR/assets/nexar-stock.png"

echo "======================================"
echo "   NEXAR STOCK - LINUX BUILD"
echo "======================================"
echo "Version: $VERSION"
echo "Root: $PROJECT_ROOT"

# =========================
# LIMPIEZA
# =========================
echo "Limpiando..."
rm -rf "$PROJECT_ROOT/build" "$DIST_DIR" "$PROJECT_ROOT/__pycache__" "$PROJECT_ROOT"/*.spec "$BUILD_ROOT"

# =========================
# BUILD PORTABLE
# =========================
echo "Generando portable..."

cd "$PROJECT_ROOT"

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
# ICONO (FIX)
# =========================
if [ -f "$ICON_SRC" ]; then
  cp "$ICON_SRC" "$PKG_DIR/usr/share/pixmaps/$APP_NAME.png"
  echo "✔ Icono agregado"
else
  echo "❌ Icono no encontrado: $ICON_SRC"
  exit 1
fi

# =========================
# DESKTOP ENTRY
# =========================
cat <<EOF > "$PKG_DIR/usr/share/applications/$APP_NAME.desktop"
[Desktop Entry]
Name=Nexar Stock
Exec=/usr/local/bin/$APP_NAME
Icon=$APP_NAME
Type=Application
Categories=Office;
Terminal=false
StartupNotify=true
EOF

chmod 644 "$PKG_DIR/usr/share/applications/$APP_NAME.desktop"

# =========================
# CONTROL FILE (FIX VERSION)
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
# POSTINST
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
mkdir -p "$PROJECT_ROOT/release"

cp "$DIST_DIR/$APP_NAME" "$PROJECT_ROOT/release/${APP_NAME}-linux-portable-${VERSION}"
cp "$FINAL_DEB" "$PROJECT_ROOT/release/${APP_NAME}-linux-installer-${VERSION}.deb"

echo "======================================"
echo "✔ BUILD COMPLETO"
echo "======================================"
echo "Portable: release/${APP_NAME}-linux-portable-${VERSION}"
echo "DEB:      release/${APP_NAME}-linux-installer-${VERSION}.deb"