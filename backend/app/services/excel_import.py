"""Parse product rows from .xlsx / .csv uploads."""

from __future__ import annotations

import csv
import io
from typing import Any

from openpyxl import load_workbook

from app.data.scenarios import STANDARD_TRAILER
from app.models.schemas import Product, Trailer


def _bool_cell(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    s = str(v).strip().lower()
    return s in ("1", "true", "yes", "y", "tak")


def _float_cell(v: Any, default: float = 0.0) -> float:
    if v is None or v == "":
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _int_cell(v: Any, default: int = 1) -> int:
    if v is None or v == "":
        return default
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def _norm_key(k: str) -> str:
    return "".join(ch for ch in k.lower().strip() if ch.isalnum())


def parse_excel(content: bytes) -> tuple[Trailer, list[Product]]:
    wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        return STANDARD_TRAILER, []
    header = [_norm_key(str(c or "")) for c in rows[0]]
    idx = {name: i for i, name in enumerate(header)}
    products: list[Product] = []
    for raw in rows[1:]:
        if raw is None or all(c is None or str(c).strip() == "" for c in raw):
            continue

        def g(*names: str, default=None):
            for n in names:
                nk = _norm_key(n)
                if nk in idx:
                    return raw[idx[nk]]
            return default

        name = g("productname", "name", default="Imported")
        pid = str(g("productid", "sku", default=f"IMP-{len(products)+1}"))
        products.append(
            Product(
                product_id=pid,
                name=str(name),
                length_mm=_float_cell(g("lengthmm", "length"), 400),
                width_mm=_float_cell(g("widthmm", "width"), 300),
                height_mm=_float_cell(g("heightmm", "height"), 250),
                weight_kg=_float_cell(g("weightkg", "weight"), 10),
                quantity=max(1, _int_cell(g("quantity", "qty"), 1)),
                fragile=_bool_cell(g("fragile", "fragility")),
                compressible=_bool_cell(g("compressible", "compress")),
                max_stack_weight_kg=_float_cell(g("maxstackweightkg", "maxstack"), 500) or None,
                can_rotate=not _bool_cell(g("norotate", "fixedorientation")),
                stacking_group=str(g("stackinggroup", "group") or "IMPORT"),
            )
        )
    return STANDARD_TRAILER, products


def parse_csv_text(text: str) -> tuple[Trailer, list[Product]]:
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return STANDARD_TRAILER, []
    fmap = {_norm_key(h): h for h in reader.fieldnames}

    def col(*candidates: str) -> str | None:
        for c in candidates:
            nk = _norm_key(c)
            if nk in fmap:
                return fmap[nk]
        return None

    products: list[Product] = []
    for row in reader:
        def gv(*names: str, default=None):
            k = col(*names)
            if not k:
                return default
            return row.get(k, default)

        name = gv("ProductName", "name", default="Imported")
        if not name or str(name).strip() == "":
            continue
        pid = str(gv("productid", "sku", default=f"IMP-{len(products)+1}"))
        products.append(
            Product(
                product_id=pid,
                name=str(name),
                length_mm=_float_cell(gv("LengthMm", "length"), 400),
                width_mm=_float_cell(gv("WidthMm", "width"), 300),
                height_mm=_float_cell(gv("HeightMm", "height"), 250),
                weight_kg=_float_cell(gv("WeightKg", "weight"), 10),
                quantity=max(1, _int_cell(gv("Quantity", "qty"), 1)),
                fragile=_bool_cell(gv("Fragile")),
                compressible=_bool_cell(gv("Compressible", "compressible")),
                max_stack_weight_kg=_float_cell(gv("MaxStackWeightKg", "maxstack"), 500) or None,
                can_rotate=not _bool_cell(gv("NoRotate")),
                stacking_group=str(gv("StackingGroup", "group") or "IMPORT"),
            )
        )
    return STANDARD_TRAILER, products
