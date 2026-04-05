#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
BUILD_DIR="$ROOT_DIR/build"
APPDIR="$BUILD_DIR/AppDir"
APP_NAME="PrivacyGuard"
ARCH="$(uname -m)"

mkdir -p "$DIST_DIR" "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/scalable/apps"

pushd "$ROOT_DIR" >/dev/null
python -m pip install --upgrade pyinstaller
pyinstaller --noconfirm --clean --name privacyguard privacyguard/main.py
popd >/dev/null

# Copy binary
cp "$ROOT_DIR/dist/privacyguard/privacyguard" "$APPDIR/usr/bin/privacyguard"

# Copy desktop file to both locations (root required for appimagetool)
cp "$ROOT_DIR/packaging/privacyguard.desktop" "$APPDIR/usr/share/applications/privacyguard.desktop"
cp "$ROOT_DIR/packaging/privacyguard.desktop" "$APPDIR/privacyguard.desktop"

# Copy icon files
if [[ -f "$ROOT_DIR/packaging/privacyguard.svg" ]]; then
  cp "$ROOT_DIR/packaging/privacyguard.svg" "$APPDIR/usr/share/icons/hicolor/scalable/apps/privacyguard.svg"
  cp "$ROOT_DIR/packaging/privacyguard.svg" "$APPDIR/privacyguard.svg"
  cp "$ROOT_DIR/packaging/privacyguard.svg" "$APPDIR/.DirIcon"
fi

cat > "$APPDIR/AppRun" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/privacyguard" "$@"
EOF
chmod +x "$APPDIR/AppRun"

if command -v appimagetool >/dev/null 2>&1; then
  appimagetool "$APPDIR" "$DIST_DIR/${APP_NAME}-${ARCH}.AppImage"
else
  echo "appimagetool not found. Install it to build AppImage." >&2
  exit 1
fi

echo "Built $DIST_DIR/${APP_NAME}-${ARCH}.AppImage"
