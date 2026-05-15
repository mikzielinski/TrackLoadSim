# Instalacja TrackLoadSim — krok po kroku

## Windows

### 1. Python 3.11+

Pobierz z [python.org](https://www.python.org/downloads/). Przy instalacji zaznacz **Add Python to PATH**.

```powershell
cd D:\TrackSim\TrackLoadSim\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Jeśli PowerShell blokuje skrypty:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 2. Node.js 18+

Pobierz LTS z [nodejs.org](https://nodejs.org/).

```powershell
cd D:\TrackSim\TrackLoadSim\frontend
npm install
```

### 3. Uruchomienie (dwa terminale)

**Terminal A — backend:**

```powershell
cd D:\TrackSim\TrackLoadSim\backend
.\.venv\Scripts\Activate.ps1
$env:OPENAI_API_KEY = "sk-..."   # opcjonalnie
uvicorn app.main:app --reload --port 8001
```

**Terminal B — frontend:**

```powershell
cd D:\TrackSim\TrackLoadSim\frontend
npm run dev
```

Przeglądarka: http://localhost:5173

### 4. PyBullet (opcjonalnie)

```powershell
pip install -r requirements-physics.txt
```

Na Windows może być potrzebny [Build Tools for Visual Studio](https://visualstudio.microsoft.com/visual-cpp-build-tools/).

---

## Linux / macOS

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...   # opcjonalnie
uvicorn app.main:app --reload --port 8001
```

```bash
cd frontend
npm install
npm run dev
```

---

## Weryfikacja

| Test | URL / akcja |
|------|-------------|
| Backend | http://127.0.0.1:8001/api/health |
| Swagger | http://127.0.0.1:8001/docs |
| Frontend | http://localhost:5173 |
| AI | Panel → Zweryfikuj połączenie AI |

---

## Build produkcyjny (frontend)

```bash
cd frontend
npm run build
npm run preview
```

Backend w produkcji: `uvicorn app.main:app --host 0.0.0.0 --port 8001` (bez `--reload`). Skonfiguruj reverse proxy (nginx) i CORS w `main.py` jeśli frontend na innym hoście.

---

## Plik `.env` (opcjonalnie)

W katalogu `backend/` możesz utworzyć `.env` (nie commituj go):

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Załaduj zmienne ręcznie lub użyj `python-dotenv` — obecnie projekt czyta **zmienne środowiskowe** bezpośrednio z OS.
