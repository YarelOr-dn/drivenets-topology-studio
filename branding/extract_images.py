#!/usr/bin/env python3
"""Extract all images from DriveNets brand PDFs into branding/extracted/"""
import fitz  # PyMuPDF
import os
from pathlib import Path

BRANDING_DIR = Path(__file__).resolve().parent
EXTRACTED_DIR = BRANDING_DIR / "extracted"
EXTRACTED_DIR.mkdir(exist_ok=True)

# Skip macOS resource fork files
PDF_FILES = [
    f for f in BRANDING_DIR.glob("*.pdf")
    if not f.name.startswith("._")
]

def main():
    total = 0
    for pdf_path in sorted(PDF_FILES):
        base = pdf_path.stem.replace(" ", "_").replace("DriveNets___", "").replace("__", "_")
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                images = page.get_images(full=True)
                for img_idx, img_info in enumerate(images):
                    xref = img_info[0]
                    try:
                        base_img = doc.extract_image(xref)
                        img_bytes = base_img["image"]
                        ext = base_img["ext"]
                        w, h = base_img["width"], base_img["height"]
                        out_name = f"{base}_p{page_num+1}_i{img_idx}_{w}x{h}.{ext}"
                        out_path = EXTRACTED_DIR / out_name
                        with open(out_path, "wb") as f:
                            f.write(img_bytes)
                        total += 1
                        print(f"  {out_name}")
                    except Exception as e:
                        print(f"  Skip xref {xref}: {e}")
            doc.close()
            print(f"  -> {len(list(EXTRACTED_DIR.glob(f'{base}_*')))} from {pdf_path.name}")
        except Exception as e:
            print(f"Error {pdf_path.name}: {e}")
    print(f"\nExtracted {total} images to {EXTRACTED_DIR}")

if __name__ == "__main__":
    main()
