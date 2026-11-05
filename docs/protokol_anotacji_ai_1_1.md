# Protokół anotacji AI (A1), wersja 1.1 (02.11.2026)

Wersja 1.1 protokołu z `docs/protokol_anotacji_ai.md`, który w wersji 1.0 zostaje bez zmian, bo jego sumy kontrolne są w `annotations/ai_protocol/freeze_A.json` i `freeze_B.json`. Krok 1.2 i 1.3 planu `docs/plan_poprawy_krok_po_kroku.md`.

## Zmiany względem wersji 1.0

- Instrukcją jest codebook 2.3. Zmiany wynikają z decyzji D0.5: opinie → `personal`, interwiki i „dodaj link” → `encyclopedia`, posty-reklamy → kategoria linkowanej strony.
- Nowe zadanie: stanowisko wobec konsensusu naukowego (`consensus_stance`, R14) dla postów z Reddita.
- Przebieg może się składać z części kodowanych przez osobnych agentów. Część nie widzi innych części ani innych przebiegów.

## Przebiegi

| Przebieg | Zadanie | Jednostki | Ziarno |
|---|---|---|---|
| C, D | źródła (`source_types`, `edit_about_sources`) | 253 jednostki zakodowane przez IS bez AI | 20261102, 20261103 |
| S1, S2 | stanowisko (`consensus_stance`) | 434 posty odniesienia planu C (157 gold, 277 z próby wzbogaconej) | 20261104, 20261105 |

## Anotator

- **Model:** Claude Opus 5.5 (`claude-opus-5-5`).
- **Agent:** każda część przebiegu to nowy agent uruchomiony z sesji Claude Code, bez rozmowy tej sesji.
- **Materiały:** agent dostaje w osobnym folderze tylko kopie trzech plików: `codebook.md`, tego protokołu i swojej części partii. Nie otwiera innych plików, linków ani internetu i nie uruchamia gita.
- **Kontekst od harnessu:** harness dołącza do kontekstu agenta indeks pamięci projektu, stan gita (nazwy plików) i tytuły commitów. Raportujemy to jako ograniczenie.

## Instrukcja

- **Codebook:** `codebook/codebook.md` (v2.3) w całości.
- **Zadanie „źródła”:** jak w wersji 1.0, czyli `source_types` (R1–R13) i `edit_about_sources` (tylko Wikipedia).
- **Zadanie „stanowisko”:** `consensus_stance` z wartościami `supports`, `challenges`, `neutral` lub `not_applicable`, według R14 i R6.
  - Podstawą jest to, co autor pisze sam albo jak przedstawia linkowany materiał w tytule.
  - Nie oceniamy, kto ma rację.
  - `consensus_topic` (R15) nie jest kodowany w tym ćwiczeniu.
- **Wątpliwości:** wybieramy najlepszą etykietę i ustawiamy `uncertain = 1` (R12).
- **Etykietowanie:** każdą jednostkę etykietuje się samodzielnie, czytając ją. Bez programów, reguł słów kluczowych i wyrażeń regularnych przypisujących etykiety.

## Co widzi anotator

- **Pola:** te same, które ludzie widzieli w arkuszach (`annotation_sheets.CONTENT_COLUMNS`). Reddit: subreddit, tytuł, treść i link posta, jeśli prowadzi poza wątek. Wikipedia: nazwa strony i opis zmiany.
- **Kody i kolejność:** losowy kod zamiast identyfikatora i losowa kolejność z ziarna przebiegu.
- **Czego anotator nie widzi:** identyfikatora, roku, podziału, wag, etykiet ludzi, preannotacji, wyników instrumentów ani etykiet innych przebiegów.
- **Klucz** (kod → jednostka) leży poza repozytorium, dopóki przebieg nie zostanie zamrożony.

## Zapis

- **Źródła:** `code,source_types,edit_about_sources,uncertain`.
- **Stanowisko:** `code,consensus_stance,uncertain`.
- **Zamrożenie:** `scripts/26_ai_protocol.py blind --run <przebieg>` zapisuje sumy kontrolne codebooka i protokołu przed kodowaniem. Po zakończeniu przebiegu etykiet się nie zmienia.

## Ocena

- **Źródła (C, D):** jak w wersji 1.0, czyli zgodność z IS, wcześniejsze etykiety Claude i instrumenty (N6). Do tego:
  - K1 jako stabilność D względem C;
  - porównanie z przebiegami A i B: ile etykiet zmienił codebook 2.3.
- **Stanowisko (S1, S2):**
  - K1: κ przebiegów S1 i S2, próg ≥ 0,8;
  - zgodność z odniesieniem planu C: κ (cztery wartości), F1, czułość, swoistość i precyzja dla `challenges`, osobno dla próby gold i wzbogaconej oraz dla wierszy rozstrzygniętych przez ludzi i przez reguły.
  - Bramka B2 planu: czułość dla `challenges` ≥ 0,8 względem odniesienia.
  - Odniesienie planu C nie jest niezależne od AI: to preannotacje AI zweryfikowane przez JP i reguły R14. Zgodność jest więc zawyżona i raportujemy to wprost.
