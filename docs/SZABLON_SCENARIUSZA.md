# Własne scenariusze — szablon i import

Ten przewodnik opisuje, jak przygotować **własny scenariusz** (lista towaru + opcjonalnie naczepa) i wczytać go do TrackLoadSim.

---

## 1. Szybki start

1. Pobierz szablon:
   - **Excel (zalecany):** [TrackLoadSim_scenario_template.xlsx](../templates/TrackLoadSim_scenario_template.xlsx)  
     lub z API: `GET /api/templates/scenario.xlsx`
   - **CSV (tylko towar):** [TrackLoadSim_scenario_products.csv](../templates/TrackLoadSim_scenario_products.csv)  
     lub `GET /api/templates/scenario.csv`
2. Uzupełnij wiersze towaru (i opcjonalnie arkusz **Trailer** w Excelu).
3. W aplikacji: **Import .xlsx / .csv** (panel boczny).
4. Scenariusz pojawi się na liście rozwijanej — wybierz go i kliknij **Przelicz rozmieszczenie** lub **Optymalizuj z AI**.

---

## 2. Szablon Excel (.xlsx)

Plik ma **dwa arkusze**:

### Arkusz `Products` (wymagany)

Jedna linia = jeden **typ** produktu (SKU). Kolumna **Quantity** określa liczbę sztuk do ułożenia.

| Kolumna | Wymagane | Opis | Przykład |
|---------|----------|------|----------|
| ProductId | tak | Unikalny kod SKU | `BOX-A` |
| ProductName | tak | Nazwa wyświetlana | `Karton zbiorczy A` |
| LengthMm | tak | Długość [mm] | `1200` |
| WidthMm | tak | Szerokość [mm] | `800` |
| HeightMm | tak | Wysokość [mm] | `900` |
| WeightKg | tak | Masa jednej szt. [kg] | `180` |
| Quantity | tak | Liczba sztuk | `6` |
| Fragile | nie | Kruche: TAK/NIE, 1/0 | `NIE` |
| Compressible | nie | Ściskalne opakowanie | `NIE` |
| MaxStackWeightKg | nie | Max obciążenie od góry [kg] | `2000` |
| StackingGroup | nie | Grupa stosowania (te same = można piętrować) | `GENERAL` |
| NoRotate | nie | TAK = brak obrotu kartonu | `NIE` |
| PackagingKind | nie | `rigid` \| `compressible` \| `max_packed` | `rigid` |
| InternalVoidRatio | nie | Luz wewnątrz opak. 0–0.85 | `0` |

**Alternatywne nazwy kolumn** (też działają): `Nazwa`, `sku`, `Ilosc`, `Waga`, `Kruche`, `GrupaStosowania` itd. — importer normalizuje nagłówki.

Puste wiersze są pomijane.

### Arkusz `Trailer` (opcjonalny)

Format **dwóch kolumn**: `Pole` | `Wartość` (lista kluczy).

| Pole | Opis | Przykład |
|------|------|----------|
| ScenarioId | ID scenariusza w aplikacji (litery, cyfry, `_`) | `MOJ_SCENARIUSZ_01` |
| ScenarioTitle | Tytuł na liście scenariuszy | `Mój załadunek — test` |
| ScenarioDescription | Opis pod listą | `Palety z magazynu X` |
| TrailerName | Nazwa naczepy w UI | `Naczepa 13,6 m` |
| LengthMm | Długość skrzyni [mm] | `13600` |
| WidthMm | Szerokość [mm] | `2450` |
| HeightMm | Wysokość [mm] | `2700` |
| MaxWeightKg | Limit masy [kg] | `24000` |
| MaxStackHeightMm | Max wysokość stosu [mm] | `2700` |
| FrontAxleLimitKg | Limit osi przedniej [kg] | `8000` |
| RearAxleLimitKg | Limit osi tylnej [kg] | `18000` |

Jeśli **brak arkusza Trailer**, używana jest **naczepa standardowa** (jak w scenariuszach S1–S6).

Inne dozwolone nazwy arkuszy:

- towar: `Products`, `Produkty`, `Ladunek`, `Cargo`
- naczepa: `Trailer`, `Naczepa`

---

## 3. Szablon CSV (.csv)

CSV zawiera **tylko produkty** (nagłówek + wiersze danych). Separator: przecinek. Kodowanie: **UTF-8** (z BOM OK).

Po imporcie CSV:

- `scenario_id` = `IMPORT_<nazwa_pliku>`
- naczepa = standardowa
- tytuł = `Import: nazwa_pliku.csv`

Aby ustawić własną naczepę i tytuł scenariusza, użyj **Excela** z arkuszem `Trailer`.

Przykład (skrót):

```csv
ProductId,ProductName,LengthMm,WidthMm,HeightMm,WeightKg,Quantity,Fragile,Compressible,MaxStackWeightKg,StackingGroup,NoRotate,PackagingKind,InternalVoidRatio
BOX-A,Karton A,1200,800,900,180,10,NIE,NIE,2000,GENERAL,NIE,rigid,0
```

---

## 4. Import w aplikacji

1. Uruchom backend i frontend ([INSTALACJA.md](./INSTALACJA.md)).
2. W panelu bocznym kliknij **Import .xlsx / .csv**.
3. Wybierz uzupełniony plik.
4. Aplikacja:
   - wczyta produkty i naczepę,
   - zbuduje **plan startowy** (pakowacz greedy),
   - doda scenariusz do listy rozwijanej.

Komunikat: `Import: nowy plan z backendu.`

### Po imporcie

| Akcja | Efekt |
|-------|--------|
| Przelicz rozmieszczenie | Nowy układ od zera (greedy) |
| Optymalizuj układ (stosy) | Piętrowanie |
| Optymalizuj z AI | Kolejność + strategia GPT |
| Mapa załadunku (PDF) | Eksport po przeliczeniu |

---

## 5. Wskazówki

### Jednostki

Wszystkie wymiary w **milimetrach**, masa w **kilogramach**.

### Quantity vs wiersze

- **Quantity = 8** → pakowacz układa **8 sztuk** tego samego SKU.
- Nie dodawaj 8 osobnych wierszy z tym samym `ProductId`, chyba że to różne warianty (różne wymiary).

### Limity

- Maks. **80 sztuk na jeden ProductId** w jednym imporcie (limit pakowacza).
- Bardzo duże quantity → część może nie zostać ułożona (komunikat w UI).

### ScenarioId

- Dozwolone: litery, cyfry, `_`, `-`.
- Spacje i znaki specjalne są zamieniane na `_`.
- Unikaj duplikatów — drugi import z tym samym ID **nadpisze** wybór na liście po odświeżeniu sesji.

### Grupy stosowania

`StackingGroup` — ten sam kod ułatwia piętrowanie w trybie **stacked** (np. `PALETA`, `GENERAL`).

### Kruche towary

`Fragile` = TAK → w trybie stacked często tylko podłoga; uwzględnij to w planie i analizie.

---

## 6. Rozwiązywanie problemów

| Problem | Rozwiązanie |
|---------|-------------|
| `No product rows parsed` | Sprawdź nagłówek arkusza Products, usuń puste wiersze |
| Zły scenariusz na liście | Ustaw `ScenarioId` w arkuszu Trailer |
| Naczepa się nie zmienia | Użyj .xlsx z arkuszem `Trailer`, nie samego CSV |
| Polskie znaki w CSV | Zapisz jako UTF-8; w Excelu „CSV UTF-8” |
| Import OK, 0 skrzynek w 3D | Kliknij **Przelicz rozmieszczenie** |
| Błąd 400 | Tylko `.xlsx`, `.xlsm`, `.csv` |

---

## 7. Powiązane dokumenty

- [INSTRUKCJA.md](./INSTRUKCJA.md) — obsługa aplikacji
- [API.md](./API.md) — `POST /api/import/products`, szablony GET
- [templates/README.md](../templates/README.md) — pliki w repozytorium
