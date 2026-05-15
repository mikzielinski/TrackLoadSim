# TrackLoadSim — Frontend

Interfejs React z widokiem 3D naczepy (React Three Fiber), panelami produktów, metrykami załadunku i analizą bezpieczeństwa.

## Uruchomienie

```bash
npm install
npm run dev
```

Aplikacja: [http://localhost:5173](http://localhost:5173)

Backend musi działać na porcie **8001** — Vite proxy przekierowuje `/api` do `http://127.0.0.1:8001`.

## Skrypty

| Polecenie | Opis |
|---------|------|
| `npm run dev` | Serwer deweloperski |
| `npm run build` | Kompilacja TypeScript + build produkcyjny |
| `npm run preview` | Podgląd buildu |

## Struktura

```text
src/
├── App.tsx                      # Layout i stan aplikacji
├── components/
│   ├── TrailerViewport.tsx      # Widok 3D
│   ├── ProductPanel.tsx         # Lista produktów
│   ├── LoadInsightsPanel.tsx    # Metryki i ostrzeżenia
│   └── SafetyAnalysisPanel.tsx  # Analiza dynamiczna
├── services/api.ts              # Klient REST
├── types/api.ts                 # Typy TypeScript
└── utils/loadMetrics.ts         # Obliczenia po stronie klienta
```

## Konfiguracja proxy

W `vite.config.ts`:

```ts
proxy: { "/api": { target: "http://127.0.0.1:8001", changeOrigin: true } }
```

Zmiana portu backendu wymaga aktualizacji tego pliku.

## Import Excel / CSV

Przycisk importu wysyła plik na `POST /api/import/products` i ładuje zwrócony scenariusz z gotowym planem pakowania.
