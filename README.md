# TrackLoadSim

Symulator i optymalizator ładowania luźnego towaru w naczepie — planowanie układu, wizualizacja 3D, analiza bezpieczeństwa, rekomendacje oraz optymalizacja wspomagana GPT.

## Funkcje

- **Pakowanie 3D** — tryby `greedy` (podłoga) i `stacked` (stosy / warstwy)
- **Widok 3D** — React Three Fiber, środek masy, wybór skrzynki
- **Analiza dynamiczna** — hamowanie, zakręty, ryzyko przewrótu
- **Rekomendacje** — podsumowanie operacyjne, załadunek, jazda
- **Optymalizacja AI** — OpenAI GPT (kolejność SKU, strategia, dopasowanie trybu)
- **Import** Excel / CSV · **Eksport** JSON + mapa załadunku PDF
- **PyBullet** (opcjonalnie) — test stabilności po optymalizacji

## Szybki start

```bash
# Backend (port 8001)
cd backend && python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Frontend (port 5173) — osobny terminal
cd frontend && npm install && npm run dev
```

→ [http://localhost:5173](http://localhost:5173)

Szczegóły: **[docs/INSTALACJA.md](docs/INSTALACJA.md)**

## Dokumentacja

| Dokument | Opis |
|----------|------|
| **[docs/INSTRUKCJA.md](docs/INSTRUKCJA.md)** | **Pełna instrukcja użytkownika** (workflow, panele, AI, FAQ) |
| **[docs/SZABLON_SCENARIUSZA.md](docs/SZABLON_SCENARIUSZA.md)** | **Szablon Excel/CSV** — własne scenariusze |
| [docs/INSTALACJA.md](docs/INSTALACJA.md) | Instalacja Windows / Linux / macOS |
| [templates/](templates/) | Pliki szablonów do pobrania |
| [docs/API.md](docs/API.md) | REST API |
| [docs/AI.md](docs/AI.md) | Integracja OpenAI |
| [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md) | Specyfikacja MVP |
| [backend/README.md](backend/README.md) | Backend FastAPI |
| [frontend/README.md](frontend/README.md) | Frontend React |

Interaktywne API: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
<img width="1795" height="1238" alt="image" src="https://github.com/user-attachments/assets/709291d4-3e5b-4c68-9dd1-68dad585857e" />
<img width="1737" height="1194" alt="image" src="https://github.com/user-attachments/assets/32d4620f-7b96-4449-a53e-e47080201ab0" />
<img width="467" height="1170" alt="image" src="https://github.com/user-attachments/assets/99186910-a5b8-4412-9ea4-fb61c33d0833" />


## Stos technologiczny

| Warstwa | Technologie |
|---------|-------------|
| Frontend | React, TypeScript, Vite, Tailwind CSS, React Three Fiber |
| Backend | Python, FastAPI, Pydantic, ReportLab |
| AI | OpenAI API (`openai`) |
| Fizyka (opcjonalnie) | PyBullet |
| Import | Excel (.xlsx) / CSV |

## OpenAI (opcjonalnie)

```powershell
$env:OPENAI_API_KEY = "sk-..."
```

Klucz można też podać w panelu **Optymalizacja AI** w UI. Model domyślny: `gpt-4o-mini`.

## Scenariusze demonstracyjne

| ID | Opis |
|----|------|
| `S1_HALF_LOADED` | ~50% podłogi, dużo wolnej wysokości |
| `S2_OPTIMIZED` | Układ 2-warstwowy, wysokie wykorzystanie |
| `S3_OVERLOAD` | Ryzyko przeciążenia masy |
| `S4_FRAGILE` | Towary delikatne |
| `S5_MIXED` | Mieszany asortyment |
| `S6_MAX_PACKED` | Maksymalne zagęszczenie |

## Struktura repozytorium

```text
TrackLoadSim/
├── backend/          # FastAPI, pakowacz, AI, fizyka, PDF
├── frontend/         # UI React + widok 3D
└── docs/             # Instrukcja, API, instalacja
```

## Licencja

Projekt demonstracyjny — ustal warunki użycia w repozytorium organizacji.
