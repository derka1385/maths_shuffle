#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════
#  compile_figures.sh
#  Compile PSTricks figures to PNG for the Maths Bac website.
#
#  Requires MacTeX (or BasicTeX + extra packages).
#  Install MacTeX: https://tug.org/mactex/  (~4.5 GB)
#  Or BasicTeX:    https://tug.org/mactex/morepackages.html (~100 MB)
#    then run: sudo tlmgr install pst-all pst-func pst-3dplot pst-eucl dvipng
#
#  Usage:  bash compile_figures.sh
# ════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIGURES_DIR="$SCRIPT_DIR/figures"
WORK_DIR="$(mktemp -d)"
trap "rm -rf $WORK_DIR" EXIT

# ── Check dependencies ────────────────────────────────────────
for cmd in latex dvipng; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "❌  '$cmd' not found."
        echo ""
        echo "Please install MacTeX from https://tug.org/mactex/"
        echo "  or BasicTeX + packages:"
        echo "    sudo tlmgr install pst-all pst-func pst-3dplot pst-eucl dvipng"
        exit 1
    fi
done

echo "✅  latex and dvipng found."
echo "📁  Figures directory: $FIGURES_DIR"
echo ""

# ── Compile each .tex file ────────────────────────────────────
total=0
success=0
skip=0

for tex_file in "$FIGURES_DIR"/*.tex; do
    [ -f "$tex_file" ] || continue
    base=$(basename "$tex_file" .tex)
    png_out="$FIGURES_DIR/${base}.png"
    total=$((total + 1))

    # Skip if PNG already up to date
    if [ -f "$png_out" ] && [ "$png_out" -nt "$tex_file" ]; then
        skip=$((skip + 1))
        continue
    fi

    echo -n "  Compiling $base … "

    # Copy .tex to temp dir and compile there (keeps figures/ clean)
    cp "$tex_file" "$WORK_DIR/${base}.tex"
    cd "$WORK_DIR"

    if latex -halt-on-error -interaction=nonstopmode "${base}.tex" \
             > "${base}.log" 2>&1; then
        # Convert DVI → PNG, 150 DPI, tight crop, transparent background
        if dvipng -D 150 -T tight -bg Transparent \
                  -o "$png_out" "${base}.dvi" \
                  >> "${base}.log" 2>&1; then
            echo "✓"
            success=$((success + 1))
        else
            echo "⚠ dvipng failed (see ${base}.log)"
        fi
    else
        echo "⚠ latex failed (see figures/${base}.log)"
        # Copy log back so user can inspect
        cp "${base}.log" "$FIGURES_DIR/${base}.log" 2>/dev/null || true
    fi

    cd "$SCRIPT_DIR"
done

echo ""
echo "════════════════════════════════════════"
echo "  Total .tex files : $total"
echo "  Already compiled : $skip"
echo "  Newly compiled   : $success"
echo "  PNG files ready  : $(ls "$FIGURES_DIR"/*.png 2>/dev/null | wc -l | tr -d ' ')"
echo "════════════════════════════════════════"
echo ""
echo "Reload the website – figures will appear automatically."
