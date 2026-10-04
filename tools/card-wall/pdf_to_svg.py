"""Convert the card PDFs printed by wall.mjs into SVG images whose text is drawn as paths.

Where this fits
---------------
wall.mjs builds the README images of the Wallbox card (assets/card/wall-*.svg) in four
steps:

1. Chrome prints every card scenario to a one-page PDF the exact size of the card.
2. This script turns each PDF into an SVG.
3. SVGO shrinks each SVG.
4. wall.mjs stacks the SVGs into one "wall" per theme.

Why go through a PDF
--------------------
Chrome cannot save a page as SVG, but it prints vector PDFs: shapes stay shapes and the
fonts are embedded. PyMuPDF then rewrites the PDF page as SVG.

Why the text becomes paths
--------------------------
GitHub shows the README images with <img>, which cannot load web fonts. Text kept as
<text> would fall back to whatever font the reader has, and change the layout. Drawn as
paths, each glyph looks the same everywhere.

Usage
-----
    python3 pdf_to_svg.py <pdf folder> <svg folder>

Every <name>.pdf in <pdf folder> becomes <name>.svg in <svg folder>, which is created
when missing. Needs PyMuPDF: pip install pymupdf.
"""

import pathlib
import re
import sys

import pymupdf

# A PDF measures in points (1/72 inch), CSS in pixels (1/96 inch): 1 pt = 4/3 px.
PX_PER_PT = 96 / 72


def convert(pdf: pathlib.Path, svg: pathlib.Path) -> None:
    """Write `pdf`, a single card, to `svg` at the card's size in CSS pixels."""
    doc = pymupdf.open(pdf)
    # wall.mjs sizes the page to the card, so a second page means the card overflowed it.
    if doc.page_count != 1:
        raise SystemExit(f"{pdf.name}: {doc.page_count} pages, expected 1")
    page = doc[0]
    content = page.get_svg_image(text_as_path=True)
    # PyMuPDF writes width and height in points, with a viewBox in points too. Only the
    # displayed size changes to pixels: the viewBox keeps the drawing scaled to fit.
    width = round(page.rect.width * PX_PER_PT)
    height = round(page.rect.height * PX_PER_PT)
    content = re.sub(
        r'width="[\d.]+" height="[\d.]+"', f'width="{width}" height="{height}"', content, count=1
    )
    svg.write_text(content)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: python3 pdf_to_svg.py <pdf folder> <svg folder>")
    src = pathlib.Path(sys.argv[1])
    dst = pathlib.Path(sys.argv[2])
    dst.mkdir(parents=True, exist_ok=True)
    for pdf in sorted(src.glob("*.pdf")):
        convert(pdf, dst / f"{pdf.stem}.svg")


if __name__ == "__main__":
    main()
