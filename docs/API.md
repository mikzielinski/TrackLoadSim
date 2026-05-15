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
  "run_physics": true
}
```

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

## Import

### `POST /api/import/products`

`multipart/form-data`, pole `file` — `.xlsx`, `.xlsm` lub `.csv`.

Zwraca obiekt `Scenario` z wyliczonym planem i ewentualnym ostrzeżeniem fizyki.

**Kolumny CSV/Excel (przykład):**

| ProductName | LengthMm | WidthMm | HeightMm | WeightKg | Quantity | Fragile | Compressible | MaxStackWeightKg |
|-------------|----------|---------|----------|----------|----------|---------|--------------|------------------|

## Eksport

### `POST /api/export/plan`

**Body:** `LoadingPlan`

**Odpowiedź:**

```json
{ "json": "<sformatowany JSON planu>" }
```

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

**Odpowiedź:** `LoadSafetyAnalysis` (metryki, ostrzeżenia, ocena ryzyka).

## Modele (skrót)

- **Trailer** — wymiary mm, `max_weight_kg`, limity osi, parametry dynamiki
- **Product** — wymiary, waga, ilość, `fragile`, `compressible`, orientacje, `physics`
- **LoadingPlan** — `boxes` (PlacedBox), wykorzystanie objętości/masy, ostrzeżenia
- **PlacedBox** — pozycja `x_mm`, `y_mm`, `z_mm`, wymiary po obrocie, `instance_id`

Szczegóły pól: `backend/app/models/schemas.py`.

## OpenAPI

Swagger UI: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
