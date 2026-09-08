#!/usr/bin/env bash
# Build the distributable archive for the Odoo App Store.
#
# The store expects a zip whose ROOT ENTRY is a folder named exactly the
# technical name, i.e. pdf_invoice_studio/. Anything else fails to install.
#
# Internal documents are excluded deliberately: blueprint.md and docs/ contain
# competitive analysis and pricing strategy that must not reach buyers.
set -euo pipefail

MODULE="pdf_invoice_studio"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT="$(dirname "$HERE")"
OUT="$HERE/dist"

VERSION="$(python3 -c "import ast,sys; print(ast.literal_eval(open('$HERE/__manifest__.py').read())['version'])")"
ARCHIVE="$OUT/${MODULE}-${VERSION}.zip"

rm -rf "$OUT"
mkdir -p "$OUT"

# Strip build artefacts before packaging.
find "$HERE" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$HERE" -name '*.pyc' -delete 2>/dev/null || true
find "$HERE" -name '.DS_Store' -delete 2>/dev/null || true

cd "$PARENT"
zip -r -q "$ARCHIVE" "$MODULE" \
    -x "$MODULE/dist/*" \
    -x "$MODULE/build.sh" \
    -x "$MODULE/blueprint.md" \
    -x "$MODULE/docs/*" \
    -x "$MODULE/.git/*" \
    -x "*__pycache__*" \
    -x "*.pyc" \
    -x "*.DS_Store"

echo "built: $ARCHIVE"
echo "size:  $(du -h "$ARCHIVE" | cut -f1)"
echo
echo "contents:"
unzip -l "$ARCHIVE" | tail -n +4 | head -40
