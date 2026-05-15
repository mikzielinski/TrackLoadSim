"""Mapa załadunku PDF: plan z góry, profil boczny, rzędy, stosy, kierunki naczepy."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from functools import lru_cache
from io import BytesIO
from math import atan2, cos, sin

import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.models.schemas import LoadingPlan, PlacedBox, Trailer

TOL_Z = 8.0
TOL_XY = 25.0

FONT = "PdfSans"
FONT_BOLD = "PdfSans-Bold"


@lru_cache(maxsize=1)
def _register_pdf_fonts() -> None:
    rl_fonts = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
    # Vera nie ma pełnego alfabetu polskiego — preferuj systemowe / DejaVu.
    candidates: list[tuple[str, str]] = [
        (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
        (r"C:\Windows\Fonts\calibri.ttf", r"C:\Windows\Fonts\calibrib.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        (
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ),
        (os.path.join(rl_fonts, "Vera.ttf"), os.path.join(rl_fonts, "VeraBd.ttf")),
    ]
    for regular, bold in candidates:
        if os.path.isfile(regular):
            pdfmetrics.registerFont(TTFont(FONT, regular))
            pdfmetrics.registerFont(TTFont(FONT_BOLD, bold if os.path.isfile(bold) else regular))
            return
    pdfmetrics.registerFont(TTFont(FONT, os.path.join(rl_fonts, "Vera.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, os.path.join(rl_fonts, "VeraBd.ttf")))


def _hex_color(box: PlacedBox) -> colors.Color:
    raw = (box.color or "#3b82f6").lstrip("#")
    if len(raw) != 6:
        return colors.HexColor("#3b82f6")
    return colors.Color(int(raw[0:2], 16) / 255, int(raw[2:4], 16) / 255, int(raw[4:6], 16) / 255)


def _xy_overlap(a: PlacedBox, b: PlacedBox) -> bool:
    return not (
        a.x_mm + a.length_mm <= b.x_mm + TOL_XY
        or b.x_mm + b.length_mm <= a.x_mm + TOL_XY
        or a.y_mm + a.width_mm <= b.y_mm + TOL_XY
        or b.y_mm + b.width_mm <= a.y_mm + TOL_XY
    )


def _layer_index(box: PlacedBox, boxes: list[PlacedBox]) -> int:
    layer = 1
    for o in boxes:
        if o.instance_id == box.instance_id:
            continue
        if not _xy_overlap(box, o):
            continue
        if o.z_mm + o.height_mm <= box.z_mm + TOL_Z and o.z_mm < box.z_mm + TOL_Z:
            layer += 1
    return layer


def _stack_column_size(box: PlacedBox, boxes: list[PlacedBox]) -> int:
    col = [b for b in boxes if _xy_overlap(box, b)]
    return len(col)


def _assign_rows(boxes: list[PlacedBox]) -> dict[str, int]:
    if not boxes:
        return {}
    ordered = sorted(boxes, key=lambda b: b.y_mm + b.width_mm / 2)
    row_groups: list[list[PlacedBox]] = []
    for b in ordered:
        cy = b.y_mm + b.width_mm / 2
        matched = False
        for group in row_groups:
            ref = sum(x.y_mm + x.width_mm / 2 for x in group) / len(group)
            if abs(cy - ref) < max(b.width_mm, 120):
                group.append(b)
                matched = True
                break
        if not matched:
            row_groups.append([b])
    row_groups.sort(key=lambda g: sum(b.y_mm for b in g) / len(g))
    out: dict[str, int] = {}
    for idx, group in enumerate(row_groups, start=1):
        for b in group:
            out[b.instance_id] = idx
    return out


def _text_w(c: canvas.Canvas, text: str, size: float, bold: bool = False) -> float:
    return c.stringWidth(text, FONT_BOLD if bold else FONT, size)


def _draw_wrapped(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_w: float,
    size: float,
    *,
    bold: bool = False,
    leading: float | None = None,
    color: colors.Color | None = None,
) -> float:
    c.setFont(FONT_BOLD if bold else FONT, size)
    if color:
        c.setFillColor(color)
    lead = leading or size * 1.35
    words = text.split()
    lines: list[str] = []
    line: list[str] = []
    for word in words:
        trial = " ".join(line + [word]) if line else word
        if _text_w(c, trial, size, bold) <= max_w:
            line.append(word)
        else:
            if line:
                lines.append(" ".join(line))
            line = [word]
    if line:
        lines.append(" ".join(line))
    for i, ln in enumerate(lines):
        c.drawString(x, y - i * lead, ln)
    return len(lines) * lead if lines else 0


def _draw_arrow(
    c: canvas.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: colors.Color,
    width: float = 1.5,
    head: float = 4 * mm,
) -> None:
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(width)
    c.line(x1, y1, x2, y2)
    ang = atan2(y2 - y1, x2 - x1)
    hx1 = x2 - head * cos(ang - 0.35)
    hy1 = y2 - head * sin(ang - 0.35)
    hx2 = x2 - head * cos(ang + 0.35)
    hy2 = y2 - head * sin(ang + 0.35)
    p = c.beginPath()
    p.moveTo(x2, y2)
    p.lineTo(hx1, hy1)
    p.lineTo(hx2, hy2)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def _draw_compass(
    c: canvas.Canvas,
    ox: float,
    oy: float,
    tw: float,
    tl: float,
    accent: colors.Color,
) -> None:
    """Krótkie boki (lewo/prawo) = przód/tył · długie (góra/dół) = lewa/prawa."""
    mid_y = oy + tw / 2
    pad = 8 * mm
    label_color = colors.HexColor("#0f172a")
    c.setFont(FONT_BOLD, 8)

    _draw_arrow(c, ox - pad, mid_y, ox + 5 * mm, mid_y, accent, 2.0)
    c.setFillColor(label_color)
    c.drawRightString(ox - pad - 2, mid_y - 3, "PRZÓD")

    _draw_arrow(c, ox + tl + pad, mid_y, ox + tl - 5 * mm, mid_y, accent, 1.6)
    c.drawString(ox + tl + pad + 2, mid_y - 3, "TYŁ")

    _draw_arrow(c, ox + tl / 2, oy + tw + pad, ox + tl / 2, oy + tw - 4 * mm, accent, 1.6)
    c.drawCentredString(ox + tl / 2, oy + tw + pad + 2, "LEWA")

    _draw_arrow(c, ox + tl / 2, oy - pad, ox + tl / 2, oy + 4 * mm, accent, 1.6)
    c.drawCentredString(ox + tl / 2, oy - pad - 10, "PRAWA")


def build_load_map_pdf(trailer: Trailer, plan: LoadingPlan, title: str) -> bytes:
    _register_pdf_fonts()
    buf = BytesIO()
    page_w, page_h = landscape(A4)
    c = canvas.Canvas(buf, pagesize=landscape(A4))

    margin = 12 * mm
    header_h = 18 * mm
    footer_h = 22 * mm
    gap = 6 * mm

    content_bottom = margin + footer_h
    content_top = page_h - margin - header_h
    content_h = content_top - content_bottom

    plan_area_w = (page_w - 2 * margin - gap) * 0.58
    side_area_w = (page_w - 2 * margin - gap) * 0.38

    scale_plan = min(plan_area_w / max(trailer.length_mm, 1), content_h / max(trailer.width_mm, 1))
    tl = trailer.length_mm * scale_plan
    tw = trailer.width_mm * scale_plan
    ox = margin
    oy = content_bottom + max(0.0, (content_h - tw) / 2)

    h_max = min(trailer.height_mm, trailer.max_stack_height_mm)
    scale_side = min(side_area_w / max(trailer.length_mm, 1), content_h / max(h_max, 1))
    sx0 = margin + plan_area_w + gap
    sy0 = content_bottom + max(0.0, (content_h - h_max * scale_side) / 2)

    rows = _assign_rows(plan.boxes)
    max_layer = max((_layer_index(b, plan.boxes) for b in plan.boxes), default=1)
    max_row = max(rows.values(), default=1)
    has_stacks = max_layer > 1 or any(_stack_column_size(b, plan.boxes) > 1 for b in plan.boxes)

    def tx(x_mm: float) -> float:
        return ox + x_mm * scale_plan

    def ty(y_mm: float) -> float:
        return oy + y_mm * scale_plan

    def txs(x_mm: float) -> float:
        return sx0 + x_mm * scale_side

    def tzs(z_mm: float) -> float:
        return sy0 + z_mm * scale_side

    accent = colors.HexColor("#0284c7")
    muted = colors.HexColor("#64748b")
    ink = colors.HexColor("#0f172a")

    c.setFont(FONT_BOLD, 12)
    c.setFillColor(ink)
    c.drawString(margin, page_h - margin - 2 * mm, title)
    c.setFont(FONT, 8)
    c.setFillColor(colors.HexColor("#475569"))
    meta = (
        f"{trailer.name} · {int(trailer.length_mm)}×{int(trailer.width_mm)}×{int(trailer.height_mm)} mm · "
        f"{len(plan.boxes)} szt. · {plan.total_weight_kg:.0f} kg · objętość {plan.utilization_volume * 100:.1f}%"
    )
    if has_stacks:
        meta += f" · rzędy: {max_row} · max warstwa: {max_layer}"
    c.drawString(margin, page_h - margin - 9 * mm, meta)
    c.drawRightString(
        page_w - margin,
        page_h - margin - 9 * mm,
        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )

    c.setFont(FONT_BOLD, 9)
    c.setFillColor(ink)
    c.drawString(ox, oy + tw + 4 * mm, "Plan z góry")

    if max_row > 1:
        row_boxes: dict[int, list[PlacedBox]] = {}
        for b in plan.boxes:
            row_boxes.setdefault(rows[b.instance_id], []).append(b)
        for ridx, group in row_boxes.items():
            y0 = min(b.y_mm for b in group)
            y1 = max(b.y_mm + b.width_mm for b in group)
            band_y = ty(y0) - 1
            band_h = ty(y1) - ty(y0) + 2
            c.setFillColor(colors.HexColor("#f1f5f9" if ridx % 2 == 0 else "#e2e8f0"))
            c.rect(ox, band_y, tl, band_h, stroke=0, fill=1)
            c.setFillColor(muted)
            c.setFont(FONT_BOLD, 7)
            c.drawString(ox + 2, band_y + band_h / 2 - 3, f"R{ridx}")

    c.setStrokeColor(colors.HexColor("#334155"))
    c.setLineWidth(1.4)
    c.setFillColor(colors.white)
    c.rect(ox, oy, tl, tw, stroke=1, fill=1)
    _draw_compass(c, ox, oy, tw, tl, accent)

    for box in sorted(plan.boxes, key=lambda b: b.load_order):
        x0, y0 = tx(box.x_mm), ty(box.y_mm)
        bw, bh = box.length_mm * scale_plan, box.width_mm * scale_plan
        layer = _layer_index(box, plan.boxes)
        col_n = _stack_column_size(box, plan.boxes)
        fill = _hex_color(box)
        c.setFillColor(fill)
        c.setStrokeColor(colors.HexColor("#0f172a"))
        c.setLineWidth(1.2 if layer > 1 else 0.5)
        c.rect(x0, y0, bw, bh, stroke=1, fill=1)
        if layer > 1:
            c.setDash([2, 2])
            c.setLineWidth(0.6)
            c.setStrokeColor(colors.HexColor("#1e40af"))
            inset = 1.5
            c.rect(x0 + inset, y0 + inset, bw - 2 * inset, bh - 2 * inset, stroke=1, fill=0)
            c.setDash()

        c.setFillColor(colors.white)
        c.setFont(FONT_BOLD, max(5, min(7, bw * 0.32)))
        c.drawCentredString(x0 + bw / 2, y0 + bh / 2 + 1, str(box.load_order))
        if layer > 1 or col_n > 1:
            c.setFont(FONT_BOLD, max(4, min(6, bw * 0.28)))
            c.setFillColor(colors.HexColor("#fef08a"))
            tag = f"W{layer}" if layer > 1 else ""
            if col_n > 1:
                tag = f"{tag}×{col_n}".strip()
            c.drawCentredString(x0 + bw / 2, y0 + bh / 2 - 7, tag)

    sl = trailer.length_mm * scale_side
    sh = h_max * scale_side
    c.setFont(FONT_BOLD, 9)
    c.setFillColor(ink)
    c.drawString(sx0, sy0 + sh + 4 * mm, "Profil boczny (długość × wysokość)")
    c.setStrokeColor(colors.HexColor("#334155"))
    c.setLineWidth(1.0)
    c.rect(sx0, sy0, sl, sh, stroke=1, fill=0)

    mid_side_y = sy0 - 6 * mm
    c.setFont(FONT_BOLD, 7)
    c.setFillColor(ink)
    c.drawString(sx0, mid_side_y, "PRZÓD")
    c.drawRightString(sx0 + sl, mid_side_y, "TYŁ")
    _draw_arrow(c, sx0 + 4 * mm, mid_side_y + 2.5, sx0 + sl * 0.35, mid_side_y + 2.5, accent, 1.4, 3 * mm)
    _draw_arrow(c, sx0 + sl * 0.65, mid_side_y + 2.5, sx0 + sl - 4 * mm, mid_side_y + 2.5, accent, 1.4, 3 * mm)
    c.setFont(FONT, 7)
    c.setFillColor(muted)
    c.drawString(sx0 - 1, sy0 + sh + 2, "wys.")

    for box in sorted(plan.boxes, key=lambda b: (b.x_mm, b.z_mm)):
        x0 = txs(box.x_mm)
        z0 = tzs(box.z_mm)
        bw = box.length_mm * scale_side
        bh = box.height_mm * scale_side
        c.setFillColor(_hex_color(box))
        c.setStrokeColor(colors.HexColor("#0f172a"))
        c.setLineWidth(0.4)
        c.rect(x0, z0, bw, bh, stroke=1, fill=1)
        layer = _layer_index(box, plan.boxes)
        if layer > 1:
            c.setFillColor(colors.white)
            c.setFont(FONT_BOLD, 5)
            c.drawCentredString(x0 + bw / 2, z0 + bh / 2, f"W{layer}")

    c.setStrokeColor(accent)
    c.setLineWidth(1.5)
    c.line(sx0, sy0, sx0 + sl, sy0)

    foot_top = margin + footer_h - 3 * mm
    c.setStrokeColor(colors.HexColor("#e2e8f0"))
    c.setLineWidth(0.6)
    c.line(margin, foot_top, page_w - margin, foot_top)

    legend_w = page_w - 2 * margin
    leg_lines = [
        "Numer = kolejność załadunku · Wn = warstwa · ×k = liczba kartonów w kolumnie · "
        "R = rząd poprzeczny (oś Y).",
        "Krótkie boki naczepy: przód / tył (oś X) · długie boki: lewa / prawa (oś Y). "
        "Profil boczny: widok wzdłuż szerokości, stosy w górę (oś Z).",
    ]
    y_leg = foot_top - 5 * mm
    c.setFont(FONT, 7)
    c.setFillColor(colors.HexColor("#334155"))
    for line in leg_lines:
        used = _draw_wrapped(c, line, margin, y_leg, legend_w, 7, leading=8.5)
        y_leg -= used + 1.5

    if plan.warnings:
        warn = "Ostrzeżenia: " + " · ".join(plan.warnings[:3])
        if len(plan.warnings) > 3:
            warn += f" (+{len(plan.warnings) - 3})"
        _draw_wrapped(c, warn, margin, y_leg - 2, legend_w, 7, leading=8.5, color=colors.HexColor("#b45309"))

    c.showPage()
    c.save()
    return buf.getvalue()
