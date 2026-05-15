# TrackLoadSim — Backend

API FastAPI: scenariusze, optymalizacja ładunku, import produktów, analiza bezpieczeństwa, rekomendacje, AI (OpenAI), eksport PDF, walidacja PyBullet.

## Uruchomienie

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Dokumentacja interaktywna: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)

## OpenAI

```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:OPENAI_MODEL = "gpt-4o-mini"    # opcjonalnie
```

Endpointy: `POST /api/ai/verify`, `POST /api/ai/optimize`. Opis: [docs/AI.md](../docs/AI.md).

## PyBullet (opcjonalnie)

```bash
pip install -r requirements-physics.txt
```

Bez PyBullet: `physics.mode: "skipped"` w odpowiedzi optymalizacji.

## Struktura

```text
app/
├── main.py                    # Endpointy REST
├── models/schemas.py          # Modele Pydantic
├── data/scenarios.py          # Scenariusze S1–S6
├── optimizer/packer.py          # Pakowacz 3D (greedy / stacked)
├── physics/
│   ├── validation.py          # PyBullet (drop test)
│   └── dynamics_analysis.py   # Analiza dynamiczna
└── services/
    ├── excel_import.py        # Import XLSX / CSV
    ├── ai_optimizer.py        # GPT + pack_with_guidance
    ├── recommendations.py     # Podsumowanie i rekomendacje
    └── load_map_pdf.py        # Mapa załadunku PDF
```

## Zależności

| Plik | Zawartość |
|------|-----------|
| `requirements.txt` | FastAPI, uvicorn, pydantic, openpyxl, numpy, reportlab, openai |
| `requirements-physics.txt` | pybullet |

## Endpointy (skrót)

| Metoda | Ścieżka |
|--------|---------|
| GET | `/api/health` |
| GET | `/api/scenarios`, `/api/scenarios/{id}` |
| POST | `/api/optimize` |
| POST | `/api/analyze` |
| POST | `/api/ai/verify`, `/api/ai/optimize` |
| POST | `/api/import/products` |
| POST | `/api/export/plan`, `/api/export/load-map-pdf` |

Pełna specyfikacja: [docs/API.md](../docs/API.md)

## CORS

Dozwolone originy dev: `localhost:5173`, `localhost:5174`.
