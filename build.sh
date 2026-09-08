#!/usr/bin/env bash
# Build the distributable archive for the Odoo App Store.
#
# Layout: this script sits at the REPOSITORY root, and the module lives in a
# subdirectory named exactly the technical name. Odoo's Apps platform scans a
# branch for module directories, so the module cannot sit at the repo root -
# the repo is called PDF-Invoice-Studio-Odoo-, which is not a legal Python
# module name.
#
# The archive's root entry is that same folder, pdf_invoice_studio/.
#
# blueprint.md and docs/ are excluded deliberately: they hold competitor
# pricing and pricing strategy that must not reach buyers.
set -euo pipefail

MODULE="pdf_invoice_studio"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$HERE/dist"

VERSION="$(python3 -c "import ast; print(ast.literal_eval(open('$HERE/$MODULE/__manifest__.py').read())['version'])")"
ARCHIVE="$OUT/${MODULE}-${VERSION}.zip"

rm -rf "$OUT"
mkdir -p "$OUT"

find "$HERE/$MODULE" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$HERE/$MODULE" -name '*.pyc' -delete 2>/dev/null || true
find "$HERE/$MODULE" -name '.DS_Store' -delete 2>/dev/null || true

cd "$HERE"
zip -r -q "$ARCHIVE" "$MODULE" \
    -x "*__pycache__*" \
    -x "*.pyc" \
    -x "*.DS_Store"

echo "built: $ARCHIVE"
echo "size:  $(du -h "$ARCHIVE" | cut -f1)"
echo
echo "root entry (must be ${MODULE}/):"
unzip -l "$ARCHIVE" | awk 'NR==4{print "  "$4}'
