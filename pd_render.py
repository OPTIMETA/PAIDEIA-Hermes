"""Render PDF pages to PNGs for the agent's native-vision ingest/grade path.

This is the deterministic half of the "Claude/native vision" OCR tier: it turns
a PDF into one PNG per page (dpi=160, long edge capped at 1800px) so the
hermes agent can ``read_file`` each page image **sequentially** and transcribe
it to LaTeX markdown. Sequential reads are non-negotiable — batching images
trips multimodal pixel-dimension limits and wastes the whole turn.

Run standalone (so the agent can invoke it via the ``terminal`` tool):

    python pd_render.py <input.pdf> <out_dir> [--dpi=160] [--max-px=1800]

Prints one rendered PNG path per line on stdout.
"""
from __future__ import annotations

import sys
from pathlib import Path

DEFAULT_DPI = 160
DEFAULT_MAX_PX = 1800


def _missing(dep: str) -> "SystemExit":
    return SystemExit(
        f"[pd_render] missing dependency '{dep}'. Install with:\n"
        f"    pip install pdf2image pillow\n"
        f"and the poppler binaries (macOS: brew install poppler)."
    )


def render_pdf_pages(
    pdf_path: Path,
    out_dir: Path,
    dpi: int = DEFAULT_DPI,
    max_px: int = DEFAULT_MAX_PX,
) -> list[Path]:
    """Render every page of *pdf_path* to ``<out_dir>/pNN.png``; return paths."""
    try:
        from pdf2image import convert_from_path
    except ImportError:
        raise _missing("pdf2image")
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        raise _missing("pillow")

    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    images = convert_from_path(str(pdf_path), dpi=dpi)
    out: list[Path] = []
    for i, img in enumerate(images, start=1):
        longest = max(img.width, img.height)
        if longest > max_px:
            ratio = max_px / longest
            img = img.resize((int(img.width * ratio), int(img.height * ratio)))
        dest = out_dir / f"p{i:02d}.png"
        img.save(dest, format="PNG")
        out.append(dest)
    return out


def _parse_args(argv: list[str]) -> tuple[Path, Path, int, int]:
    dpi, max_px, positional = DEFAULT_DPI, DEFAULT_MAX_PX, []
    for arg in argv[1:]:
        if arg.startswith("--dpi="):
            dpi = int(arg.split("=", 1)[1])
        elif arg.startswith("--max-px="):
            max_px = int(arg.split("=", 1)[1])
        else:
            positional.append(arg)
    if len(positional) != 2:
        print(
            "usage: python pd_render.py <input.pdf> <out_dir> "
            "[--dpi=160] [--max-px=1800]",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return Path(positional[0]), Path(positional[1]), dpi, max_px


if __name__ == "__main__":
    pdf, out_dir, dpi, max_px = _parse_args(sys.argv)
    for p in render_pdf_pages(pdf, out_dir, dpi=dpi, max_px=max_px):
        print(p)
