# Wariant A wykonany automatycznie (27.10.2026)

Zasady: wpis z 27.10.2026 w [`hipotezy.md`](hipotezy.md). Polecenia: `make control-draw` (raz) i `make control-score`.

## Co zrobiono

1. `scripts/25_control_check.py draw` wylosował próby (ziarno 20261027). Klucz jest w `annotations/control/control_sample.csv`. Pliki z samym tekstem i arkusz dla ludzi `human_check.xlsx` są w `annotations/sheets/control/`, poza gitem.
2. Asystent AI zakodował 144 jednostki na ślepo, widząc tylko tekst, w losowej kolejności: `annotations/control/ai_blind_claude-opus-5-5.csv`.
3. `score` porównał to kodowanie z etykietami z arkuszy (stanowisko, audyt) oraz z etykietami ludzi (źródła). Wyniki są w `control_scores.csv`, rozbieżności w `control_disagreements.csv`, a makra `\resControl…` w `report/numbers.tex`.

## Wyniki (opisowe)

| Próba | Co mierzy | Wynik |
|---|---|---|
| Stanowisko, 84 wiersze (42 `challenges` z części testowej i 42 inne) | stabilność etykiet AI | zgodność 90 % [82; 95], κ = 0,84; 87 % [75; 94] etykiet `challenges` potwierdzonych |
| Audyt, 30 wierszy | stabilność etykiet AI | identyczny zbiór kategorii 87 % [70; 95], `cites_source` 97 % |
| Źródła, 30 postów zakodowanych przez ludzi przed AI | **błąd AI względem ludzi** | identyczny zbiór 93 % [79; 98]: wobec zgodnych IS i JP 16/16, wobec jednej osoby (gold) 12/14 |

**Rozbieżności w stanowisku (8 z 84):**
- 6 wierszy oznaczonych w arkuszu jako `challenges` drugie kodowanie oznaczyło jako `neutral` albo `not_applicable`; to głównie nagłówki przekazane bez komentarza;
- 1 wiersz `neutral` → `challenges`;
- 1 wiersz `neutral` → `not_applicable`.

Te wiersze warto sprawdzić w pierwszej kolejności, gdy ludzie siądą do arkusza `human_check.xlsx`.

## Czego to nie daje

- **Brak zgodności ludzi dla stanowiska.** Pilotaż stanowiska (dwie osoby) nadal nie jest zakodowany; nie zastępujemy go modelem.
- **Stabilność to nie trafność.** Ten sam model może dwa razy popełnić ten sam błąd. Dla stanowiska nie ma żadnej etykiety człowieka.
- **Ślepota jest niepełna.** Asystent wiedział z losowania, że połowa wierszy stanowiska pochodzi z warstwy `challenges` (bez wskazania których). Komunikat błędu pierwszego przebiegu pokazał też zbiór etykiet ludzi z pilotażu źródeł, bez identyfikatorów postów.
- Porównanie źródeł z ludźmi dotyczy zadania audytu (`source_types`), a nie stanowiska.

## Zdanie do sekcji Walidacja (szkic do przepisania przez autorów)

Ślepe drugie kodowanie przez asystenta AI potwierdziło etykiety stanowiska w \resControlStanceAgreement{} wierszy (κ = \resControlStanceKappa{}). W zadaniu audytu jego etykiety zgadzały się z etykietami ludzi w \resControlSourcesExact{} postów. Etykiet stanowiska nie sprawdził żaden człowiek.
