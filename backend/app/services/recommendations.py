"""Rekomendacje załadunku, jazdy i podsumowanie operacyjne."""

from __future__ import annotations

from typing import Literal

from app.models.schemas import (
    LoadSafetyAnalysis,
    LoadingPlan,
    Product,
    RecommendationSection,
    RecommendationsReport,
    SummaryReport,
    Trailer,
)

Status = Literal["ok", "caution", "critical"]


def _worst(*statuses: Status) -> Status:
    if "critical" in statuses:
        return "critical"
    if "caution" in statuses:
        return "caution"
    return "ok"


def _com_x_mm(boxes: list) -> float | None:
    if not boxes:
        return None
    wx = wsum = 0.0
    for b in boxes:
        m = max(b.weight_kg, 1e-6)
        wx += (b.x_mm + b.length_mm / 2) * m
        wsum += m
    return wx / wsum if wsum else None


def build_recommendations(
    trailer: Trailer,
    products: list[Product],
    plan: LoadingPlan,
    safety: LoadSafetyAnalysis,
) -> RecommendationsReport:
    boxes = plan.boxes
    requested = sum(max(0, p.quantity) for p in products)
    placed = len(boxes)
    tw = plan.total_weight_kg
    weight_ratio = tw / trailer.max_weight_kg if trailer.max_weight_kg else 0
    util_pct = plan.utilization_volume * 100

    high_risks = [r for r in safety.packaging_risks if r.risk_level == "high"]
    med_risks = [r for r in safety.packaging_risks if r.risk_level == "medium"]
    ceiling_n = len(safety.ceiling_packed_ids)
    unstable_n = sum(1 for b in boxes if b.unstable)

    loading_items: list[str] = []
    loading_status: Status = "ok"

    if placed == 0:
        loading_items.append("Brak ułożonych kartonów — użyj „Przelicz rozmieszczenie” lub importu Excel.")
        loading_status = "critical"
    else:
        if placed < requested:
            loading_items.append(
                f"Ułożono tylko {placed} z {requested} szt. — zwolnij miejsce, zmniejsz quantity lub zmień wymiary."
            )
            loading_status = _worst(loading_status, "critical")
        if weight_ratio > 1.0:
            loading_items.append(
                f"Masa {tw:.0f} kg przekracza limit {trailer.max_weight_kg:.0f} kg — usuń lub rozłóż ładunek."
            )
            loading_status = _worst(loading_status, "critical")
        elif weight_ratio > 0.95:
            loading_items.append("Masa blisko limitu — unikaj dodatkowych sztuk bez przeliczenia osi.")
            loading_status = _worst(loading_status, "caution")

        com_x = _com_x_mm(boxes)
        if com_x is not None and trailer.length_mm > 0:
            pct = com_x / trailer.length_mm * 100
            if pct > 62:
                loading_items.append(
                    f"Środek masy w {pct:.0f}% długości (od przodu) — przesuń cięższe kartony ku przodowi (niższe x)."
                )
                loading_status = _worst(loading_status, "caution")
            elif pct < 38:
                loading_items.append(
                    f"Środek masy w {pct:.0f}% długości — rozważ przesunięcie masy ku tyłowi dla równowagi osi."
                )
                loading_status = _worst(loading_status, "caution")

        if util_pct < 45 and placed >= requested * 0.9:
            loading_items.append(
                f"Niskie wykorzystanie objętości ({util_pct:.0f}%) — możesz dodać towaru lub użyć „Optymalizuj układ (stosy)”."
            )
        elif util_pct > 92:
            loading_items.append(
                f"Bardzo wysokie wypełnienie ({util_pct:.0f}%) — sprawdź luz przy suficie i ściskalne opakowania."
            )
            loading_status = _worst(loading_status, "caution")

        if high_risks:
            loading_items.append(
                f"{len(high_risks)} kartonów z wysokim ryzykiem przesunięcia — użyj „Optymalizuj układ (stosy)”, "
                "dociśnij warstwy, zabezpiecz pasy / kątowniki (EN 12195)."
            )
            loading_status = _worst(loading_status, "critical")
        elif med_risks:
            loading_items.append(
                f"{len(med_risks)} kartonów na granicy tarcia — rozważ stosy grupowe i dodatkowe zabezpieczenie."
            )
            loading_status = _worst(loading_status, "caution")

        if ceiling_n:
            loading_items.append(
                f"{ceiling_n} szt. przy suficie — obniż stosy ściskalnego towaru lub zmień orientację opakowań."
            )
            loading_status = _worst(loading_status, "caution")

        if unstable_n:
            loading_items.append(
                f"{unstable_n} szt. oznaczonych jako niestabilne (symulacja) — popraw podparcie lub kolejność warstw."
            )
            loading_status = _worst(loading_status, "caution")

        joined = " ".join(loading_items)
        for w in plan.warnings[:4]:
            if w not in joined:
                loading_items.append(w)
                joined += " " + w
                if "Nie udało się" in w or "przekracza" in w:
                    loading_status = _worst(loading_status, "critical")
                else:
                    loading_status = _worst(loading_status, "caution")

        z_bands = {int(round(b.z_mm / 40.0)) for b in boxes}
        stack_layers = len(z_bands)
        if stack_layers <= 1 and util_pct < 55:
            loading_items.append(
                f"Układ jednowarstwowy (z≈0) przy {util_pct:.0f}% objętości — rozważ „Optymalizuj układ (stosy)” lub AI ze stacked."
            )
            loading_status = _worst(loading_status, "caution")
        elif stack_layers >= 2:
            loading_items.append(f"Wykryto ok. {stack_layers} warstwy w pionie (wg pozycji z).")

        if loading_status == "ok" and not loading_items:
            loading_items.append(
                f"Układ {placed} szt., {stack_layers} warstw(y), wykorzystanie {util_pct:.0f}%, "
                f"masa {weight_ratio * 100:.0f}% limitu — parametry załadunku w normie modelu."
            )

    loading_headlines = {
        "ok": "Załadunek — OK",
        "caution": "Załadunek — wymaga korekty",
        "critical": "Załadunek — nie gotowy",
    }

    # --- Jazda ---
    driving_items: list[str] = []
    driving_status: Status = "ok"

    max_safe_speed: int | None = None
    for row in sorted(safety.speed_scenarios, key=lambda r: r.speed_kmh):
        if row.loose_units_at_risk == 0:
            max_safe_speed = row.speed_kmh
        else:
            break

    if not safety.speed_scenarios:
        driving_items.append("Brak scenariuszy prędkości — uzupełnij plan ładunku.")
        driving_status = "caution"
    else:
        if not safety.rollover.ok:
            driving_items.append(safety.rollover.summary)
            driving_items.append("Ogranicz prędkość na łukach; unikaj gwałtownych manewrów poprzecznych.")
            driving_status = _worst(driving_status, "critical")
        elif safety.rollover.utilization_ratio > 0.72:
            driving_items.append(
                f"{safety.rollover.summary} Zalecana ostrożność na zakrętach autostradowych."
            )
            driving_status = _worst(driving_status, "caution")

        if high_risks:
            driving_items.append(
                "Przed wyjazdem: dodatkowe mocowanie ładunku luzem (pasy, siatka, wypełnienie luzów)."
            )
            driving_status = _worst(driving_status, "critical")

        if max_safe_speed is not None:
            if max_safe_speed < 80 and (high_risks or med_risks):
                driving_items.append(
                    f"Model: przy {max_safe_speed} km/h brak jednostek „luzem” w ryzyku — "
                    f"trzymaj się ≤ {max_safe_speed} km/h do czasu poprawy układu."
                )
                driving_status = _worst(driving_status, "caution")
            elif high_risks:
                driving_items.append("Po poprawie układu: test hamowania na placu przed trasą ekspresową.")
            else:
                driving_items.append(
                    f"Prędkość referencyjna modelu: do {max_safe_speed} km/h bez wykrytego ryzyka przesunięcia luzem."
                )
        else:
            driving_items.append(
                "Przy wszystkich analizowanych prędkościach wykryto ryzyko przesunięcia — "
                "nie rozpoczynaj jazdy bez korekty załadunku lub mocowania."
            )
            driving_status = _worst(driving_status, "critical")

        driving_items.append(
            f"Hamowanie projektowe {trailer.max_brake_accel_g} g · poprzecznie {trailer.max_lateral_accel_g} g — "
            "płynna jazda, unikaj gwałtownego hamowania."
        )

    driving_headlines = {
        "ok": "Jazda — standardowa ostrożność",
        "caution": "Jazda — ograniczenia",
        "critical": "Jazda — wysokie ryzyko",
    }

    # --- Podsumowanie ---
    overall = _worst(loading_status, driving_status)
    if not safety.global_ok:
        overall = _worst(overall, "critical" if high_risks else "caution")

    risk_label = f"{len(high_risks)} wys. / {len(med_risks)} śr. ryzyko przesunięcia"
    paragraph_parts = [
        f"Plan: {placed}/{requested} szt., masa {tw:.0f} kg ({weight_ratio * 100:.0f}% limitu), "
        f"objętość {util_pct:.0f}%.",
        f"Bezpieczeństwo modelu: {'zgodne' if safety.global_ok else 'wymaga uwagi'} ({risk_label}).",
    ]
    if safety.rollover.ok:
        paragraph_parts.append(
            f"Stateczność poprzeczna: OK (CM nad jezdnią ~{safety.rollover.com_height_road_m:.1f} m)."
        )
    else:
        paragraph_parts.append(f"Stateczność: {safety.rollover.summary}")

    verdicts = {
        "ok": "Gotowe do załadunku i jazdy wg uproszczonego modelu — zweryfikuj mocowanie na placu.",
        "caution": "Wyjazd możliwy po wdrożeniu rekomendacji załadunku i ograniczeniu prędkości.",
        "critical": "Nie zalecamy wyjazdu — popraw układ, masę lub zabezpieczenie przed trasą.",
    }

    key_metrics = [
        f"Status globalny: {'OK' if safety.global_ok else 'UWAGA'}",
        f"Kartony w planie: {placed}",
        f"Wykorzystanie obj.: {util_pct:.1f}%",
    ]
    if max_safe_speed is not None and driving_status != "critical":
        key_metrics.append(f"Prędkość ref. modelu: ≤ {max_safe_speed} km/h")

    summary_headlines = {
        "ok": "Podsumowanie — gotowe",
        "caution": "Podsumowanie — warunkowo",
        "critical": "Podsumowanie — stop",
    }

    return RecommendationsReport(
        loading=RecommendationSection(
            status=loading_status,
            headline=loading_headlines[loading_status],
            items=loading_items[:8],
        ),
        driving=RecommendationSection(
            status=driving_status,
            headline=driving_headlines[driving_status],
            items=driving_items[:8],
        ),
        summary=SummaryReport(
            status=overall,
            headline=summary_headlines[overall],
            paragraph=" ".join(paragraph_parts),
            verdict=verdicts[overall],
            key_metrics=key_metrics,
        ),
    )
