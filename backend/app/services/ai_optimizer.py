"""Optymalizacja załadunku wspomagana GPT (OpenAI)."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from app.models.schemas import (
    AiConnectionStatus,
    AiPackingGuidance,
    LoadingPlan,
    Product,
    Trailer,
)
from app.optimizer.packer import PackMode, _expand_products, pack_trailer

DEFAULT_MODEL = "gpt-4o-mini"
_LAYER_HINTS = ("warstw", "warstwow", "stos", "stosów", "piętr", "na górze", "górnej", "dolnych warstw", "układ pionowy")


def _resolve_api_key(override: str | None) -> str | None:
    key = (override or os.environ.get("OPENAI_API_KEY") or "").strip()
    return key or None


def _resolve_model() -> str:
    return (os.environ.get("OPENAI_MODEL") or DEFAULT_MODEL).strip() or DEFAULT_MODEL


def _openai_client(api_key: str):
    from openai import OpenAI

    base_url = (os.environ.get("OPENAI_BASE_URL") or "").strip() or None
    return OpenAI(api_key=api_key, base_url=base_url)


def verify_ai_connection(api_key_override: str | None = None) -> AiConnectionStatus:
    api_key = _resolve_api_key(api_key_override)
    model = _resolve_model()
    if not api_key:
        return AiConnectionStatus(
            configured=False,
            connected=False,
            model=model,
            message="Brak klucza API. Ustaw OPENAI_API_KEY na serwerze lub podaj klucz w panelu AI.",
        )
    try:
        client = _openai_client(api_key)
        client.models.list()
        return AiConnectionStatus(
            configured=True,
            connected=True,
            model=model,
            message=f"Połączenie OK · model: {model}",
        )
    except Exception as exc:  # noqa: BLE001
        return AiConnectionStatus(
            configured=True,
            connected=False,
            model=model,
            message=f"Nie udało się połączyć z OpenAI: {exc}",
        )


def _product_payload(p: Product) -> dict[str, Any]:
    return {
        "product_id": p.product_id,
        "name": p.name,
        "length_mm": p.length_mm,
        "width_mm": p.width_mm,
        "height_mm": p.height_mm,
        "weight_kg": p.weight_kg,
        "quantity": p.quantity,
        "fragile": p.fragile,
        "compressible": p.compressible,
        "max_stack_weight_kg": p.max_stack_weight_kg,
        "stacking_group": p.stacking_group,
        "packaging_kind": p.packaging_kind,
        "can_rotate": p.can_rotate,
    }


def _build_prompt(
    trailer: Trailer,
    products: list[Product],
    *,
    baseline: LoadingPlan | None,
    safety_notes: list[str],
    recommendation_items: list[str],
    user_notes: str,
) -> tuple[str, str]:
    expanded = _expand_products(products)
    system = (
        "Jesteś ekspertem od załadunku naczep. Odpowiadasz WYŁĄCZNIE poprawnym JSON (bez markdown). "
        "Układ współrzędnych: x = długość naczepy (0 = przód), y = szerokość, z = wysokość od podłogi. "
        "Kruche i ciężkie reguły są priorytetem. load_order musi zawierać dokładnie jeden product_id na każdą "
        "sztukę do ułożenia (łączna liczba wpisów = liczba sztuk w zadaniu)."
    )
    user_obj: dict[str, Any] = {
        "trailer": {
            "name": trailer.name,
            "length_mm": trailer.length_mm,
            "width_mm": trailer.width_mm,
            "height_mm": trailer.height_mm,
            "max_weight_kg": trailer.max_weight_kg,
            "max_stack_height_mm": trailer.max_stack_height_mm,
        },
        "products": [_product_payload(p) for p in products],
        "units_to_place": len(expanded),
        "baseline_plan": None,
        "safety_notes": safety_notes,
        "recommendations": recommendation_items,
        "operator_notes": user_notes.strip() or None,
        "required_json_schema": {
            "pack_mode": "greedy | stacked",
            "load_order": ["product_id per unit, length = units_to_place"],
            "fragile_floor_only": "boolean",
            "strategy_summary": "string PL, 2-4 zdania",
            "loading_tips": ["string PL, max 6"],
        },
    }
    if baseline and baseline.boxes:
        user_obj["baseline_plan"] = {
            "placed": len(baseline.boxes),
            "utilization_volume_pct": round(baseline.utilization_volume * 100, 1),
            "warnings": baseline.warnings,
            "sample_boxes": [
                {
                    "product_id": b.product_id,
                    "x_mm": b.x_mm,
                    "y_mm": b.y_mm,
                    "z_mm": b.z_mm,
                    "load_order": b.load_order,
                }
                for b in sorted(baseline.boxes, key=lambda x: x.load_order)[:12]
            ],
        }
    user = json.dumps(user_obj, ensure_ascii=False, indent=2)
    return system, user


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _normalize_load_order(
    raw_order: list[str],
    expanded: list[Product],
) -> list[Product]:
    by_id: dict[str, list[Product]] = {}
    for p in expanded:
        by_id.setdefault(p.product_id, []).append(p)

    used: dict[str, int] = {}
    sequence: list[Product] = []
    for pid in raw_order:
        pool = by_id.get(pid)
        if not pool:
            continue
        idx = used.get(pid, 0)
        if idx >= len(pool):
            continue
        sequence.append(pool[idx])
        used[pid] = idx + 1

    remaining: list[Product] = []
    for pid, pool in by_id.items():
        start = used.get(pid, 0)
        remaining.extend(pool[start:])
    remaining.sort(key=lambda p: (-p.weight_kg, -(p.length_mm * p.width_mm * p.height_mm)))
    sequence.extend(remaining)
    return sequence


def request_packing_guidance(
    trailer: Trailer,
    products: list[Product],
    *,
    baseline: LoadingPlan | None,
    safety_notes: list[str],
    recommendation_items: list[str],
    user_notes: str,
    api_key_override: str | None = None,
) -> AiPackingGuidance:
    api_key = _resolve_api_key(api_key_override)
    if not api_key:
        raise ValueError("Brak klucza OpenAI API.")

    expanded = _expand_products(products)
    system, user = _build_prompt(
        trailer,
        products,
        baseline=baseline,
        safety_notes=safety_notes,
        recommendation_items=recommendation_items,
        user_notes=user_notes,
    )
    model = _resolve_model()
    client = _openai_client(api_key)
    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    raw = response.choices[0].message.content or "{}"
    data = _extract_json(raw)

    pack_mode: PackMode = "stacked" if data.get("pack_mode") == "stacked" else "greedy"
    raw_order = data.get("load_order")
    if not isinstance(raw_order, list):
        raw_order = []
    load_order = [str(x) for x in raw_order]
    item_sequence = _normalize_load_order(load_order, expanded)

    tips = data.get("loading_tips")
    if not isinstance(tips, list):
        tips = []
    loading_tips = [str(t) for t in tips[:6]]

    guidance = AiPackingGuidance(
        pack_mode=pack_mode,
        item_sequence_product_ids=[p.product_id for p in item_sequence],
        fragile_floor_only=bool(data.get("fragile_floor_only", False)),
        strategy_summary=str(data.get("strategy_summary") or "Brak podsumowania AI."),
        loading_tips=loading_tips,
        model=model,
    )
    return _align_pack_mode_with_strategy(guidance)


def _align_pack_mode_with_strategy(guidance: AiPackingGuidance) -> AiPackingGuidance:
    """GPT często opisuje stosy w tekście, a w JSON podaje pack_mode=greedy (tylko podłoga)."""
    blob = (guidance.strategy_summary + " " + " ".join(guidance.loading_tips)).lower()
    if guidance.pack_mode == "greedy" and any(h in blob for h in _LAYER_HINTS):
        return guidance.model_copy(update={"pack_mode": "stacked"})
    return guidance


def _stack_layer_count(plan: LoadingPlan) -> int:
    if not plan.boxes:
        return 0
    bands: set[int] = set()
    for b in plan.boxes:
        bands.add(int(round(b.z_mm / 40.0)))
    return len(bands)


def _run_pack(trailer: Trailer, products: list[Product], guidance: AiPackingGuidance) -> LoadingPlan:
    expanded = _expand_products(products)
    by_id: dict[str, list[Product]] = {}
    for p in expanded:
        by_id.setdefault(p.product_id, []).append(p)

    sequence: list[Product] = []
    used: dict[str, int] = {}
    for pid in guidance.item_sequence_product_ids:
        pool = by_id.get(pid)
        if not pool:
            continue
        idx = used.get(pid, 0)
        if idx >= len(pool):
            continue
        sequence.append(pool[idx])
        used[pid] = idx + 1
    for pid, pool in by_id.items():
        sequence.extend(pool[used.get(pid, 0) :])

    return pack_trailer(
        trailer,
        products,
        mode=guidance.pack_mode,
        item_sequence=sequence,
        fragile_floor_only=guidance.fragile_floor_only,
    )


def pack_with_guidance(
    trailer: Trailer,
    products: list[Product],
    guidance: AiPackingGuidance,
) -> LoadingPlan:
    guidance = _align_pack_mode_with_strategy(guidance)
    plan = _run_pack(trailer, products, guidance)
    layers = _stack_layer_count(plan)
    if layers <= 1 and guidance.pack_mode == "greedy":
        stacked_guidance = guidance.model_copy(update={"pack_mode": "stacked"})
        stacked_plan = _run_pack(trailer, products, stacked_guidance)
        if _stack_layer_count(stacked_plan) > 1:
            guidance = stacked_guidance
            plan = stacked_plan
            layers = _stack_layer_count(plan)

    extra_warn: list[str] = []
    if layers <= 1 and any(h in guidance.strategy_summary.lower() for h in _LAYER_HINTS):
        extra_warn.append(
            "AI opisało układ warstwowy, ale pakowacz ułożył tylko jedną warstwę (brak podparcia / wysokości)."
        )

    ai_warn = f"AI ({guidance.model}): {guidance.strategy_summary}"
    tips = [f"AI: {t}" for t in guidance.loading_tips[:4]]
    return LoadingPlan(
        boxes=plan.boxes,
        total_weight_kg=plan.total_weight_kg,
        utilization_volume=plan.utilization_volume,
        warnings=[ai_warn, *tips, *extra_warn, *plan.warnings],
    )
