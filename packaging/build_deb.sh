#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
VERSION="$(python -c 'from privacyguard import __version__; print(__version__)')"
ARCH="$(dpkg --print-architecture)"
STAGE_DIR="$ROOT_DIR/build/deb-stage"

mkdir -p "$DIST_DIR"
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR/usr/local/lib/privacyguard"
mkdir -p "$STAGE_DIR/usr/local/bin"
mkdir -p "$STAGE_DIR/usr/share/applications"
mkdir -p "$STAGE_DIR/usr/share/icons/hicolor/scalable/apps"

if ! command -v fpm >/dev/null 2>&1; then
  echo "fpm is required to build .deb packages" >&2
  exit 1
fi

pushd "$ROOT_DIR" >/dev/null
python -m pip install . --target "$STAGE_DIR/usr/local/lib/privacyguard"

cat > "$STAGE_DIR/usr/local/bin/privacyguard" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="/usr/local/lib/privacyguard:${PYTHONPATH:-}"
exec python3 -m privacyguard.main "$@"
EOF
chmod +x "$STAGE_DIR/usr/local/bin/privacyguard"

cp "$ROOT_DIR/packaging/privacyguard.desktop" "$STAGE_DIR/usr/share/applications/privacyguard.desktop"
if [[ -f "$ROOT_DIR/packaging/privacyguard.svg" ]]; then
  cp "$ROOT_DIR/packaging/privacyguard.svg" "$STAGE_DIR/usr/share/icons/hicolor/scalable/apps/privacyguard.svg"
fi

fpm \
  -s dir \
  -t deb \
  -C "$STAGE_DIR" \
  --name privacyguard \
  --version "$VERSION" \
  --architecture "$ARCH" \
  --description "Local-first text redaction desktop tool" \
  --url "https://github.com/USERNAME/privacyguard" \
  --license "MIT" \
  --depends "python3 (>= 3.11)" \
  --after-install "$ROOT_DIR/packaging/postinst.sh" \
  --package "$DIST_DIR/privacyguard_${VERSION}_${ARCH}.deb" \
  .

popd >/dev/null

echo "Built .deb package(s) in $DIST_DIR"
