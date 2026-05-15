# TrackLoadSim

Symulator i optymalizator ładowania luźnego towaru w naczepie — planowanie układu, wizualizacja 3D oraz walidacja fizyczna (PyBullet).

## Stos technologiczny

| Warstwa | Technologie |
|---------|-------------|
| Frontend | React, TypeScript, Vite, Tailwind CSS, React Three Fiber |
| Backend | Python, FastAPI, Pydantic |
| Fizyka (opcjonalnie) | PyBullet |
| Import danych | Excel (.xlsx) / CSV |

## Szybki start

### Wymagania

- Python 3.11+
- Node.js 18+

### Backend (port 8001)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
pip install -r requirements-physics.txt   # opcjonalnie — walidacja PyBullet
uvicorn app.main:app --reload --port 8001
```

### Frontend (port 5173)

```bash
cd frontend
npm install
npm run dev
```

Otwórz [http://localhost:5173](http://localhost:5173). Żądania `/api/*` są proxyowane do backendu (patrz `frontend/vite.config.ts`).

## Scenariusze demonstracyjne

| ID | Opis |
|----|------|
| `S1_HALF_LOADED` | Naczepa w połowie załadowana — dużo wolnej przestrzeni |
| `S2_OPTIMIZED` | Zoptymalizowany układ, wysokie wykorzystanie |
| `S3_OVERLOAD` | Agresywne pakowanie, ryzyko przeciążenia |
| `S4_FRAGILE` | Towary delikatne |
| `S5_MIXED` | Mieszany asortyment |
| `S6_MAX_PACKED` | Maksymalne zagęszczenie |

## Dokumentacja

- [Specyfikacja projektu i wymagania MVP](docs/PROJECT_SPEC.md)
- [Opis API REST](docs/API.md)
- [Backend — uruchomienie i struktura](backend/README.md)
- [Frontend — uruchomienie i struktura](frontend/README.md)

## Struktura repozytorium

```text
TrackLoadSim/
├── backend/          # FastAPI, optymalizator, fizyka, import Excel
├── frontend/         # UI React + widok 3D naczepy
└── docs/             # Specyfikacja i API
```

## Licencja

Projekt demonstracyjny — ustal warunki użycia w repozytorium organizacji.
