#!/usr/bin/env python3
"""
Extract individual icons from DriveNets Drivenets Icons PDF.

Uses two approaches:
1. Page render + crop: Renders each page at high DPI and crops icon cells by grid.
2. SVG export: Exports full-page SVG; individual icon SVGs can be derived by
   cropping the output or parsing path groups (see extracted/*.svg).

Run: python3 extract_icon_svgs.py
"""
import fitz  # PyMuPDF
import re
from pathlib import Path

BRANDING_DIR = Path(__file__).resolve().parent
ICONS_PDF = BRANDING_DIR / "DriveNets _ Drivenets Icons.pdf"
EXTRACTED_DIR = BRANDING_DIR / "extracted"
ICONS_DIR = EXTRACTED_DIR / "icons"
ICONS_DIR.mkdir(parents=True, exist_ok=True)

# Page dimensions (points)
PAGE_W = 595
PAGE_H = 842
# Grid: 5 columns, 5 rows per page (approx)
COLS = 5
ROWS = 5
# Margins and cell size (estimated from PDF layout)
MARGIN_LEFT = 35
MARGIN_TOP = 25
CELL_W = (PAGE_W - 2 * MARGIN_LEFT) / COLS
CELL_H = (PAGE_H - 2 * MARGIN_TOP) / ROWS


def get_icon_labels(doc, page_num):
    """Extract icon names from page text blocks (skip 'SVG • NxN' lines)."""
    page = doc[page_num]
    blocks = page.get_text("dict").get("blocks", [])
    labels = []
    for b in blocks:
        for line in b.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if text and "SVG" not in text and not re.match(r"^\d+x\d+$", text):
                    # Clean: "Multi-\nlayer_Switch" -> "Multi-layer_Switch"
                    text = text.replace("\n", "").replace("_icon2", "").replace("_icon_2", "")
                    if text and text not in labels:
                        labels.append(text)
    return labels


def crop_icons_from_page(doc, page_num, dpi=300):
    """Render each icon cell and save as PNG."""
    page = doc[page_num]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    labels = get_icon_labels(doc, page_num)
    cropped = []
    idx = 0
    for row in range(ROWS):
        for col in range(COLS):
            x0 = MARGIN_LEFT + col * CELL_W
            y0 = MARGIN_TOP + row * CELL_H
            x1 = MARGIN_LEFT + (col + 1) * CELL_W
            y1 = MARGIN_TOP + (row + 1) * CELL_H
            clip = fitz.Rect(x0, y0, x1, y1)
            pix = page.get_pixmap(matrix=mat, clip=clip, alpha=False)
            name = labels[idx] if idx < len(labels) else f"icon_p{page_num+1}_{row}_{col}"
            name = re.sub(r"[^\w\-]", "_", name)[:50]
            out_path = ICONS_DIR / f"p{page_num+1}_{name}_{idx}.png"
            pix.save(str(out_path))
            cropped.append(out_path.name)
            idx += 1
    return cropped


def export_page_svg(doc, page_num):
    """Export full page as SVG for manual cropping or path extraction."""
    page = doc[page_num]
    svg = page.get_svg_image()
    out_path = EXTRACTED_DIR / f"icons_page{page_num+1}_full.svg"
    with open(out_path, "w") as f:
        f.write(svg)
    return out_path.name


def main():
    if not ICONS_PDF.exists():
        print(f"Missing: {ICONS_PDF}")
        return
    doc = fitz.open(ICONS_PDF)
    print(f"DriveNets Icons PDF: {len(doc)} pages")
    total = 0
    for p in range(len(doc)):
        labels = get_icon_labels(doc, p)
        print(f"  Page {p+1}: {len(labels)} labels, first few: {labels[:5]}")
        cropped = crop_icons_from_page(doc, p)
        total += len(cropped)
        # Export full-page SVG for pages 2 and 3 (network icons)
        if p in (1, 2):
            fn = export_page_svg(doc, p)
            print(f"    SVG: {fn}")
    doc.close()
    print(f"\nCropped {total} icon PNGs to {ICONS_DIR}")
    print(f"Full-page SVGs in {EXTRACTED_DIR} (icons_page2_full.svg, icons_page3_full.svg)")


if __name__ == "__main__":
    main()
