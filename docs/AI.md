# Optymalizacja AI (OpenAI)

Techniczny opis integracji GPT z pakowaczem TrackLoadSim.

## Architektura

```
POST /api/ai/optimize
  ├─ verify_ai_connection(api_key)
  ├─ baseline_plan ← body.baseline_plan || pack_trailer(greedy)
  ├─ analyze_load_safety(baseline) → notatki + rekomendacje do promptu
  ├─ request_packing_guidance() → OpenAI Chat Completions (JSON)
  ├─ pack_with_guidance() → LoadingPlan
  ├─ validate_static_drop() [opcjonalnie]
  └─ analyze_load_safety(nowy plan) + wskazówki AI w rekomendacjach
```

Implementacja: `backend/app/services/ai_optimizer.py`, endpoint: `backend/app/main.py`.

## Konfiguracja środowiska

| Zmienna | Domyślnie | Opis |
|---------|-----------|------|
| `OPENAI_API_KEY` | — | Klucz API (wymagany do AI) |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model chat |
| `OPENAI_BASE_URL` | OpenAI | Np. proxy kompatybilne z API OpenAI |

Alternatywa: klucz w body `api_key` (panel UI) — nadpisuje zmienną serwera na czas żądania.

## Endpointy

### `POST /api/ai/verify`

Sprawdza klucz (body opcjonalne: `{ "api_key": "..." }`).

**Odpowiedź:** `AiConnectionStatus` — `configured`, `connected`, `model`, `message`.

### `POST /api/ai/optimize`

**Body (`AiOptimizeRequest`):**

```json
{
  "trailer": { "...": "Trailer" },
  "products": [ { "...": "Product" } ],
  "scenario_id": "S1_HALF_LOADED",
  "run_physics": true,
  "user_notes": "Piętruj A, B na górze",
  "api_key": null,
  "baseline_plan": null
}
```

- `baseline_plan` — opcjonalnie bieżący plan z UI; jeśli `null`, liczony jest greedy od zera.
- `user_notes` — uwagi operatora w promptcie.

**Odpowiedź (`AiOptimizeResponse`):**

```json
{
  "plan": { "...": "LoadingPlan" },
  "physics": { "...": "PhysicsValidationResult" },
  "guidance": {
    "pack_mode": "stacked",
    "item_sequence_product_ids": ["BOX-A", "BOX-A", "..."],
    "fragile_floor_only": false,
    "strategy_summary": "...",
    "loading_tips": ["..."],
    "model": "gpt-4o-mini"
  },
  "connection": { "...": "AiConnectionStatus" },
  "safety_analysis": { "...": "LoadSafetyAnalysis" }
}
```

`safety_analysis` zawiera `recommendations` dla **nowego** planu (nie baseline).

## Format odpowiedzi GPT

Model musi zwrócić **czysty JSON** (bez markdown):

```json
{
  "pack_mode": "greedy | stacked",
  "load_order": ["product_id", "..."],
  "fragile_floor_only": false,
  "strategy_summary": "2-4 zdania PL",
  "loading_tips": ["max 6 stringów PL"]
}
```

- `load_order` — dokładnie jeden `product_id` na każdą sztukę do ułożenia (suma = `units_to_place`).
- Współrzędne w promptcie: x = długość (0 = przód), y = szerokość, z = wysokość.

## Logika po stronie serwera

### `_align_pack_mode_with_strategy`

Jeśli w `strategy_summary` / `loading_tips` są słowa typu „warstw”, „stos”, „na górze”, a `pack_mode` = `greedy` → zmiana na `stacked`.

### `pack_with_guidance`

1. Pakowanie według `guidance.pack_mode` i kolejności SKU.
2. Gdy wynik ma 1 warstwę i tryb był `greedy` → ponowna próba ze `stacked`.
3. Ostrzeżenie w planie, gdy tekst AI sugeruje warstwy, a pakowacz dał tylko podłogę.

Ostrzeżenia planu:

- linia `AI (model): {strategy_summary}`,
- do 4× `AI: {loading_tip}`,
- ostrzeżenia pakowacza (np. brak miejsca, tryb stosy).

## Frontend

- `AiOptimizePanel` — klucz, uwagi, weryfikacja, strategia.
- `optimizeWithAi()` w `services/api.ts` — wysyła `baseline_plan: plan` z App.
- Po sukcesie: `setPlan`, `setSafetyAnalysis(res.safety_analysis)`, `setAiStrategy`.

Klucz w `localStorage`: `trackloadsim_openai_key`.

## Koszty i limity

- Każde „Optymalizuj z AI” = 1 wywołanie chat + 2× analiza bezpieczeństwa (baseline do promptu, wynik końcowy).
- Limit rozszerzonych produktów w pakowaczu: **80 szt. na SKU** (`_expand_products`).
- Temperature GPT: `0.2`, `response_format: json_object`.

## Błędy HTTP

| Kod | Przyczyna |
|-----|-----------|
| 503 | Brak połączenia z OpenAI / brak klucza |
| 400 | Walidacja (np. brak klucza w `request_packing_guidance`) |
| 502 | Błąd wywołania OpenAI lub parsowania JSON |

## Rozszerzenia (pomysły)

- Zapisywanie historii strategii per scenariusz.
- Wymuszenie `pack_mode` z UI niezależnie od GPT.
- Fine-tuning / function calling z twardym schematem Pydantic.
