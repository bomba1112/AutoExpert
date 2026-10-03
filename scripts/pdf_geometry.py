"""Glyph positions of a PDF page from its content stream (pypdf only, no pdfplumber).

The cached page text (RAW_ROOT/pagetext) keeps the reading order but loses the columns of a
ruled grid; schedule grids (GM "Maintenance Schedule Additional Required Services": one column
per mileage point, a mark glyph per due service) need the x position of every mark. This module
replays the text operators of a page (BT/ET, Tm/Td/TD/T*, Tf/Tc/Tw/Tz/TL, Tj/TJ/'/", cm, q/Q)
with the font widths and returns one run per show operator:
  {"text", "glyphs": [(char, cx, cy)], "x", "y" (origin), "x_end", "cx", "cy" (centre), "size", "rotated"}
Text inside form XObjects is not read (the grids checked are drawn on the page itself).

  used by build_maintenance_gm.py
"""

from __future__ import annotations

from pypdf import PdfReader
from pypdf.generic import ArrayObject, ContentStream, NumberObject

IDENTITY = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def mult(m1: tuple, m2: tuple) -> tuple:
    """m1 applied first, then m2 (PDF row-vector convention)."""
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (a1 * a2 + b1 * c2, a1 * b2 + b1 * d2, c1 * a2 + d1 * c2, c1 * b2 + d1 * d2,
            e1 * a2 + f1 * c2 + e2, e1 * b2 + f1 * d2 + f2)


def apply(m: tuple, x: float, y: float) -> tuple[float, float]:
    return m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]


def font_info(font) -> dict:
    f = font.get_object()
    if f.get("/Subtype") == "/Type0":
        desc = f["/DescendantFonts"][0].get_object()
        widths, w = {}, desc.get("/W", [])
        i = 0
        while i < len(w):
            start, nxt = int(w[i]), w[i + 1]
            if isinstance(nxt, ArrayObject):
                for k, value in enumerate(nxt):
                    widths[start + k] = float(value)
                i += 2
            else:
                for code in range(start, int(nxt) + 1):
                    widths[code] = float(w[i + 2])
                i += 3
        return {"two_byte": True, "widths": widths, "default": float(desc.get("/DW", 1000))}
    first = int(f.get("/FirstChar", 0))
    widths = {first + k: float(v) for k, v in enumerate(f.get("/Widths") or [])}
    return {"two_byte": False, "widths": widths, "default": 500.0}


def raw_bytes(s) -> bytes:
    if isinstance(s, bytes):
        return bytes(s)
    original = getattr(s, "original_bytes", None)
    if original is not None:
        return bytes(original)
    return str(s).encode("latin-1", errors="replace")


def page_hrules(reader: PdfReader, index: int) -> list[tuple[float, float, float]]:
    """Horizontal ruling segments of a page (table row separators): [(x0, x1, y)]."""
    page = reader.pages[index]
    contents = page.get_contents()
    if contents is None:
        return []
    ctm, stack, cur, out = IDENTITY, [], None, []
    for operands, op in ContentStream(contents, reader).operations:
        if op == b"q":
            stack.append(ctm)
        elif op == b"Q":
            ctm = stack.pop() if stack else IDENTITY
        elif op == b"cm":
            ctm = mult(tuple(float(v) for v in operands), ctm)
        elif op == b"m":
            cur = apply(ctm, float(operands[0]), float(operands[1]))
        elif op == b"l" and cur is not None:
            nxt = apply(ctm, float(operands[0]), float(operands[1]))
            if abs(nxt[1] - cur[1]) < 1 and abs(nxt[0] - cur[0]) > 20:
                out.append((min(cur[0], nxt[0]), max(cur[0], nxt[0]), (cur[1] + nxt[1]) / 2))
            cur = nxt
        elif op == b"re":
            x, y, w, h = (float(v) for v in operands)
            (x0, y0), (x1, y1) = apply(ctm, x, y), apply(ctm, x + w, y + h)
            if abs(y1 - y0) < 2 and abs(x1 - x0) > 20:
                out.append((min(x0, x1), max(x0, x1), (y0 + y1) / 2))
    return out


def page_runs(reader: PdfReader, index: int) -> list[dict]:
    page = reader.pages[index]
    resources = page.get("/Resources") or {}
    fonts = {}
    font_dict = resources.get("/Font") if resources else None
    if font_dict:
        for name in font_dict:
            try:
                fonts[name] = font_info(font_dict[name])
            except Exception:  # noqa: BLE001 - an odd font must not stop the page
                fonts[name] = {"two_byte": False, "widths": {}, "default": 500.0}
    contents = page.get_contents()
    if contents is None:
        return []
    ops = ContentStream(contents, reader).operations
    ctm, stack = IDENTITY, []
    tm = lm = IDENTITY
    font, size, tc, tw, th, tl = None, 1.0, 0.0, 0.0, 1.0, 0.0
    runs = []

    def show(s):
        nonlocal tm
        info = fonts.get(font) or {"two_byte": False, "widths": {}, "default": 500.0}
        data = raw_bytes(s)
        codes = ([data[i] * 256 + data[i + 1] for i in range(0, len(data) - 1, 2)] if info["two_byte"] else list(data))
        glyphs = []
        start = mult(tm, ctm)
        for code in codes:
            w = info["widths"].get(code, info["default"]) / 1000.0
            m = mult(tm, ctm)
            cx, cy = apply(m, w * size / 2, 0.35 * size)
            ch = chr(code) if not info["two_byte"] and 32 <= code < 256 else "?"
            glyphs.append((ch, cx, cy))
            adv = (w * size + tc + (tw if (code == 32 and not info["two_byte"]) else 0.0)) * th
            tm = mult((1, 0, 0, 1, adv, 0), tm)
        return glyphs, start

    def record(glyphs, start):
        if not glyphs:
            return
        text = "".join(g[0] for g in glyphs)
        x, y = apply(start, 0, 0)
        eff = (start[2] ** 2 + start[3] ** 2) ** 0.5 * size
        visible = [g for g in glyphs if g[0].strip()]
        cx = sum(g[1] for g in visible) / len(visible) if visible else x
        cy = sum(g[2] for g in visible) / len(visible) if visible else y
        x_end, _ = apply(mult(tm, ctm), 0, 0)  # text position after the last glyph
        runs.append({"text": text, "glyphs": glyphs, "x": x, "y": y, "cx": cx, "cy": cy, "size": eff, "x_end": x_end,
                     "rotated": abs(start[1]) > abs(start[0])})

    for operands, op in ops:
        if op == b"q":
            stack.append(ctm)
        elif op == b"Q":
            ctm = stack.pop() if stack else IDENTITY
        elif op == b"cm":
            ctm = mult(tuple(float(v) for v in operands), ctm)
        elif op == b"BT":
            tm = lm = IDENTITY
        elif op == b"Tf":
            font, size = operands[0], float(operands[1])
        elif op == b"Tc":
            tc = float(operands[0])
        elif op == b"Tw":
            tw = float(operands[0])
        elif op == b"Tz":
            th = float(operands[0]) / 100.0
        elif op == b"TL":
            tl = float(operands[0])
        elif op == b"Tm":
            tm = lm = tuple(float(v) for v in operands)
        elif op in (b"Td", b"TD"):
            tx, ty = float(operands[0]), float(operands[1])
            if op == b"TD":
                tl = -ty
            lm = mult((1, 0, 0, 1, tx, ty), lm)
            tm = lm
        elif op == b"T*":
            lm = mult((1, 0, 0, 1, 0, -tl), lm)
            tm = lm
        elif op == b"Tj":
            record(*show(operands[0]))
        elif op in (b"'", b'"'):
            if op == b'"':
                tw, tc = float(operands[0]), float(operands[1])
            lm = mult((1, 0, 0, 1, 0, -tl), lm)
            tm = lm
            record(*show(operands[-1]))
        elif op == b"TJ":
            glyphs, start = [], mult(tm, ctm)
            for element in operands[0]:
                if isinstance(element, (NumberObject, int, float)) or type(element).__name__ == "FloatObject":
                    if float(element) < -100 and glyphs:  # a word gap set by kerning
                        gx, gy = apply(mult(tm, ctm), 0, 0)
                        glyphs.append((" ", gx, gy))
                    tm = mult((1, 0, 0, 1, -float(element) / 1000.0 * size * th, 0), tm)
                else:
                    g, _ = show(element)
                    glyphs += g
            record(glyphs, start)
    return runs
