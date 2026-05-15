# TrackLoadSim — Backend

API FastAPI: scenariusze, optymalizacja układu ładunku, import produktów, walidacja PyBullet, analiza bezpieczeństwa.

## Uruchomienie

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Dokumentacja interaktywna: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)

## PyBullet (opcjonalnie)

Walidacja statyczna po optymalizacji wymaga PyBullet:

```bash
pip install -r requirements-physics.txt
```

Na Windowsie instalacja może wymagać Visual C++ Build Tools lub gotowego wheela dla danej wersji Pythona. Bez PyBullet endpoint `/api/optimize` zwraca wynik z `physics.mode: "skipped"`.

## Struktura

```text
app/
├── main.py              # Endpointy REST
├── models/schemas.py    # Modele Pydantic
├── data/scenarios.py    # Scenariusze S1–S6
├── optimizer/packer.py  # Heurystyczny pakowacz 3D
├── physics/
│   ├── validation.py    # Symulacja PyBullet (drop test)
│   └── dynamics_analysis.py
└── services/excel_import.py
```

## Zależności

- `requirements.txt` — FastAPI, uvicorn, pydantic, openpyxl, numpy
- `requirements-physics.txt` — pybullet

## CORS

Dozwolone originy: `localhost:5173`, `localhost:5174` (Vite dev server).

Pełna lista endpointów: [docs/API.md](../docs/API.md).
