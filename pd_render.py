"""Render PDF pages to PNGs for the agent's native-vision ingest/grade path.

This is the deterministic half of the "Claude/native vision" OCR tier: it turns
a PDF into one PNG per page (dpi=160, long edge capped at 1800px) so the
hermes agent can ``read_file`` each page image **sequentially** and transcribe
it to LaTeX markdown. Sequential reads are non-negotiable — batching images
trips multimodal pixel-dimension limits and wastes the whole turn.

Every caller in this plugin goes through here (``/paideia ingest``,
``/paideia grade``'s claude tier) rather than inlining its own render+resize
snippet, so the page-ordering and dimension-ceiling guarantees below hold once
instead of three times.

Run standalone (so the agent can invoke it via the ``terminal`` tool):

    python pd_render.py <input.pdf> <out_dir> [--dpi=160] [--max-px=1800]

Prints one rendered PNG path per line on stdout, in page order.
"""
from __future__ import annotations

import sys
from pathlib import Path

DEFAULT_DPI = 160
# The many-image request limit rejects any image whose long edge exceeds ~2000px;
# 1800 leaves margin without blurring subscripts at dpi=160.
DEFAULT_MAX_PX = 1800


def _missing(dep: str) -> "SystemExit":
    return SystemExit(
        f"[pd_render] missing dependency '{dep}'. Install with:\n"
        f"    pip install pdf2image pillow\n"
        f"and the poppler binaries (macOS: brew install poppler)."
    )


def _pdf2image():
    try:
        import pdf2image
    except ImportError:
        raise _missing("pdf2image")
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        raise _missing("pillow")
    return pdf2image


def page_count(pdf_path: Path) -> int:
    """Number of pages in *pdf_path* (0 if poppler can't report it)."""
    p2i = _pdf2image()
    try:
        return int(p2i.pdfinfo_from_path(str(pdf_path))["Pages"])
    except Exception:
        return 0


def iter_pages(pdf_path: Path, dpi: int = DEFAULT_DPI, total: int | None = None):
    """Yield ``(page_number, PIL.Image)`` one page at a time.

    ``convert_from_path`` without ``first_page``/``last_page`` decodes the entire
    PDF into memory: a 200-page textbook at dpi=160 is ~1.4 GB of RGB bitmaps,
    and a 40-page scan at dpi=300 is ~1 GB. Rendering one page per call keeps
    peak memory at a single page, which is what makes ingest survive a real
    textbook instead of asking the user to split the PDF by hand.
    """
    p2i = _pdf2image()
    if total is None:
        total = page_count(pdf_path)
    if total <= 0:
        # poppler couldn't report a count (encrypted, or an old pdfinfo).
        # Fall back to one whole-file decode rather than failing outright.
        for i, img in enumerate(p2i.convert_from_path(str(pdf_path), dpi=dpi), 1):
            yield i, img
        return
    for i in range(1, total + 1):
        imgs = p2i.convert_from_path(
            str(pdf_path), dpi=dpi, first_page=i, last_page=i
        )
        if not imgs:
            continue
        img = imgs[0]
        try:
            yield i, img
        finally:
            img.close()


def _fit(img, max_px: int):
    """Downscale *img* so its long edge is <= *max_px*. LANCZOS: text stays crisp."""
    from PIL import Image

    longest = max(img.width, img.height)
    if longest <= max_px:
        return img
    ratio = max_px / longest
    size = (max(1, round(img.width * ratio)), max(1, round(img.height * ratio)))
    return img.resize(size, Image.LANCZOS)


def render_pdf_pages(
    pdf_path: Path,
    out_dir: Path,
    dpi: int = DEFAULT_DPI,
    max_px: int = DEFAULT_MAX_PX,
) -> list[Path]:
    """Render every page of *pdf_path* to ``<out_dir>/pNN.png``; return paths.

    The page-number field is zero-padded to the width of the total page count,
    so a 120-page chapter yields ``p001.png … p120.png``. Fixed 2-digit padding
    would sort ``p100`` between ``p10`` and ``p11``, and the agent reads these in
    sorted order — a silently scrambled transcript is worse than a loud failure.
    """
    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    total = page_count(pdf_path)
    if total > 0:
        pages = iter_pages(pdf_path, dpi=dpi, total=total)
    else:
        # poppler couldn't report a count. Decode once — memory is the price of
        # not knowing — but count first, because guessing the padding width is
        # how p1000.png ends up sorting before p999.png.
        images = _pdf2image().convert_from_path(str(pdf_path), dpi=dpi)
        total = len(images)
        pages = enumerate(images, 1)
    width = max(2, len(str(total)))

    out: list[Path] = []
    for i, img in pages:
        dest = out_dir / f"p{i:0{width}d}.png"
        _fit(img, max_px).save(dest, format="PNG", optimize=True)
        out.append(dest)
    return out


def _int_flag(arg: str) -> int:
    """Parse ``--name=<int>``, reporting a usage error rather than a traceback."""
    name, _, raw = arg.partition("=")
    try:
        return int(raw)
    except ValueError:
        print(f"error: {name} needs an integer (got {raw!r})", file=sys.stderr)
        raise SystemExit(2) from None


def _parse_args(argv: list[str]) -> tuple[Path, Path, int, int]:
    dpi, max_px, positional = DEFAULT_DPI, DEFAULT_MAX_PX, []
    for arg in argv[1:]:
        if arg.startswith("--dpi="):
            dpi = _int_flag(arg)
        elif arg.startswith("--max-px="):
            max_px = _int_flag(arg)
        else:
            positional.append(arg)
    if len(positional) != 2:
        print(
            "usage: python pd_render.py <input.pdf> <out_dir> "
            "[--dpi=160] [--max-px=1800]",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if dpi <= 0 or max_px <= 0:
        print("error: --dpi and --max-px must be positive", file=sys.stderr)
        raise SystemExit(2)
    return Path(positional[0]), Path(positional[1]), dpi, max_px


UNREADABLE_HINT = (
    "poppler could not read this PDF. It is usually one of:\n"
    "  - password-protected  → qpdf --password=… --decrypt in.pdf out.pdf, then retry\n"
    "  - truncated/corrupt   → check `pdfinfo <pdf>`; re-download or re-export it\n"
    "  - not actually a PDF  → check `file <pdf>`"
)

if __name__ == "__main__":
    pdf, out_dir, dpi, max_px = _parse_args(sys.argv)
    if not pdf.is_file():
        print(f"error: no such PDF: {pdf}", file=sys.stderr)
        raise SystemExit(2)
    try:
        pages = render_pdf_pages(pdf, out_dir, dpi=dpi, max_px=max_px)
    except SystemExit:
        raise                       # missing dependency: _missing() already explains
    except Exception as exc:
        # An agent reads this. A raw pdf2image traceback tells it nothing it can
        # act on, and the caller has to report a specific reason to the user.
        print(f"error: cannot render {pdf}: {type(exc).__name__}", file=sys.stderr)
        print(UNREADABLE_HINT, file=sys.stderr)
        raise SystemExit(1) from None
    if not pages:
        print(f"error: {pdf} rendered 0 pages", file=sys.stderr)
        print(UNREADABLE_HINT, file=sys.stderr)
        raise SystemExit(1)
    for p in pages:
        print(p)
    print(
        f"[pd_render] {len(pages)} page(s) → {out_dir} (dpi={dpi}, max={max_px}px)",
        file=sys.stderr,
    )
