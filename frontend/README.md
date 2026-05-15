# TrackLoadSim — Frontend

Interfejs React z widokiem 3D naczepy (React Three Fiber), optymalizacją AI, rekomendacjami, metrykami i analizą bezpieczeństwa.

## Uruchomienie

```bash
npm install
npm run dev
```

Aplikacja: [http://localhost:5173](http://localhost:5173)

Backend na porcie **8001** — Vite proxy: `/api` → `http://127.0.0.1:8001`.

Instrukcja użytkownika: [docs/INSTRUKCJA.md](../docs/INSTRUKCJA.md)

## Skrypty

| Polecenie | Opis |
|---------|------|
| `npm run dev` | Serwer deweloperski |
| `npm run build` | Build produkcyjny |
| `npm run preview` | Podgląd buildu |

## Struktura

```text
src/
├── App.tsx                         # Stan, scenariusze, optymalizacja
├── components/
│   ├── TrailerViewport.tsx         # Widok 3D
│   ├── ProductPanel.tsx            # Lista produktów
│   ├── AiOptimizePanel.tsx         # Panel GPT
│   ├── RecommendationsPanel.tsx    # Podsumowanie + rekomendacje
│   ├── LoadInsightsPanel.tsx       # Metryki (masa, warstwy, LDM…)
│   └── SafetyAnalysisPanel.tsx     # Analiza dynamiczna
├── services/api.ts                 # Klient REST
├── types/api.ts                    # Typy TypeScript
└── utils/loadMetrics.ts            # Metryki po stronie klienta
```

## Główne akcje w UI

| Przycisk | API |
|----------|-----|
| Przelicz rozmieszczenie | `POST /api/optimize` (`greedy`) |
| Optymalizuj układ (stosy) | `POST /api/optimize` (`stacked`) |
| Optymalizuj z AI | `POST /api/ai/optimize` |
| Zweryfikuj połączenie AI | `POST /api/ai/verify` |
| Mapa załadunku (PDF) | `POST /api/export/load-map-pdf` |
| Eksport JSON | `POST /api/export/plan` |
| Import | `POST /api/import/products` |

Analiza bezpieczeństwa odświeża się po zmianie planu (`POST /api/analyze`); po AI wynik może przyjść od razu w `safety_analysis`.

## Klucz OpenAI w przeglądarce

Panel AI zapisuje opcjonalny klucz w `localStorage` (`trackloadsim_openai_key`). Wysyłany jest do backendu tylko przy żądaniach AI — preferuj `OPENAI_API_KEY` na serwerze w środowisku produkcyjnym.

## Proxy

`vite.config.ts`:

```ts
proxy: { "/api": { target: "http://127.0.0.1:8001", changeOrigin: true } }
```
