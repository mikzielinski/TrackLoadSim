# TrackLoadSim — REST API

Bazowy URL (dev): `http://127.0.0.1:8001`  
Przez frontend Vite: `/api/...`

## Health

### `GET /api/health`

```json
{ "status": "ok" }
```

## Scenariusze

### `GET /api/scenarios`

Lista wbudowanych scenariuszy.

**Odpowiedź:** tablica `{ "scenario_id": string, "title": string }`

### `GET /api/scenarios/{scenario_id}`

Pełny scenariusz: naczepa, produkty, opcjonalny plan.

**Scenariusze:** `S1_HALF_LOADED`, `S2_OPTIMIZED`, `S3_OVERLOAD`, `S4_FRAGILE`, `S5_MIXED`, `S6_MAX_PACKED`

## Optymalizacja

### `POST /api/optimize`

Oblicza plan załadunku (greedy packer) i opcjonalnie waliduje fizykę.

**Body:**

```json
{
  "trailer": { "...": "Trailer" },
  "products": [ { "...": "Product" } ],
  "scenario_id": "optional",
  "run_physics": true,
  "mode": "greedy"
}
```

`mode`: `greedy` (domyślnie, wypełnianie od podłogi) lub `stacked` (stosy pionowe, cięższe na dole).

**Odpowiedź:**

```json
{
  "plan": { "...": "LoadingPlan" },
  "physics": {
    "ok": true,
    "mode": "pybullet | skipped | ...",
    "message": "...",
    "steps_simulated": 0
  }
}
```

## Szablony scenariuszy

### `GET /api/templates/scenario.xlsx`

Pobiera szablon Excel: arkusze **Products** + **Trailer** (przykładowe dane).

### `GET /api/templates/scenario.csv`

Pobiera szablon CSV (tylko lista towaru).

Instrukcja: [SZABLON_SCENARIUSZA.md](./SZABLON_SCENARIUSZA.md)

## Import

### `POST /api/import/products`

`multipart/form-data`, pole `file` — `.xlsx`, `.xlsm` lub `.csv`.

Zwraca obiekt `Scenario` z wyliczonym planem i ewentualnym ostrzeżeniem fizyki.

**Excel (.xlsx):**

- Arkusz **Products** — wiersze towaru (nagłówek + dane).
- Arkusz **Trailer** (opcjonalny) — kolumny `Pole` / `Wartość`: `ScenarioId`, `ScenarioTitle`, `ScenarioDescription`, wymiary naczepy, limity osi.

**CSV:** tylko produkty; naczepa standardowa; `scenario_id` z nazwy pliku.

**Kolumny Products (przykład):**

| ProductId | ProductName | LengthMm | WidthMm | HeightMm | WeightKg | Quantity | Fragile | Compressible | MaxStackWeightKg |
|-----------|-------------|----------|---------|----------|----------|----------|---------|--------------|------------------|

## Eksport

### `POST /api/export/load-map-pdf`

Mapa załadunku (widok z góry) w PDF.

**Body:** `{ "trailer", "plan", "title"?, "scenario_id"? }`  
**Odpowiedź:** `application/pdf` (plik do pobrania).

### `POST /api/export/plan`

**Body:** `LoadingPlan`

**Odpowiedź:**

```json
{ "json": "<sformatowany JSON planu>" }
```

## Optymalizacja AI (OpenAI)

Wymaga skonfigurowanego klucza API (`OPENAI_API_KEY` na serwerze lub `api_key` w żądaniu).

### `POST /api/ai/verify`

Sprawdza połączenie z OpenAI.

**Body (opcjonalne):** `{ "api_key": "sk-..." }`

**Odpowiedź:** `AiConnectionStatus` — `configured`, `connected`, `model`, `message`

### `POST /api/ai/optimize`

Plan od GPT (kolejność SKU + tryb) + pakowacz 3D + analiza na **nowym** planie.

**Body:**

```json
{
  "trailer": { "...": "Trailer" },
  "products": [ { "...": "Product" } ],
  "scenario_id": "S1_HALF_LOADED",
  "run_physics": true,
  "user_notes": "Piętruj cięższe na dole",
  "api_key": null,
  "baseline_plan": null
}
```

- `baseline_plan` — opcjonalny bieżący plan z UI; jeśli pominięty, liczony jest greedy.
- `user_notes` — uwagi operatora trafiają do promptu GPT.

**Odpowiedź:**

```json
{
  "plan": { "...": "LoadingPlan" },
  "physics": { "...": "PhysicsValidationResult" },
  "guidance": {
    "pack_mode": "greedy | stacked",
    "item_sequence_product_ids": ["..."],
    "fragile_floor_only": false,
    "strategy_summary": "...",
    "loading_tips": ["..."],
    "model": "gpt-4o-mini"
  },
  "connection": { "...": "AiConnectionStatus" },
  "safety_analysis": { "...": "LoadSafetyAnalysis" }
}
```

`safety_analysis.recommendations` — podsumowanie i rekomendacje dla **wynikowego** układu (w tym wskazówki AI w sekcji `loading`).

Szczegóły: [AI.md](./AI.md)

## Analiza bezpieczeństwa

### `POST /api/analyze`

Analiza dynamiczna (hamowanie, zakręty) dla danego planu.

**Body:**

```json
{
  "trailer": { "...": "Trailer" },
  "products": [ { "...": "Product" } ],
  "plan": { "...": "LoadingPlan" },
  "speeds_kmh": [50, 80]
}
```

**Odpowiedź:** `LoadSafetyAnalysis` (metryki, ostrzeżenia, ocena ryzyka) oraz `recommendations`:

- `loading` — rekomendacja załadunku (status, punkty)
- `driving` — rekomendacja jazdy
- `summary` — podsumowanie operacyjne (akapit, werdykt, metryki kluczowe)

## Modele (skrót)

- **Trailer** — wymiary mm, `max_weight_kg`, limity osi, parametry dynamiki
- **Product** — wymiary, waga, ilość, `fragile`, `compressible`, orientacje, `physics`
- **LoadingPlan** — `boxes` (PlacedBox), wykorzystanie objętości/masy, ostrzeżenia
- **PlacedBox** — pozycja `x_mm`, `y_mm`, `z_mm`, wymiary po obrocie, `instance_id`

Szczegóły pól: `backend/app/models/schemas.py`.

## OpenAPI

Swagger UI: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
