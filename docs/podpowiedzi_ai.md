# Podpowiedzi AI w arkuszach (26.10.2026)

Na prośbę zespołu asystent AI (Claude Opus 5.5) wstępnie wypełnił arkusze Fazy A (stanowisko) i Fazy B. Każdą etykietę sprawdza człowiek. Podpowiedzi bez tekstu postów są w git, w [`annotations/ai_suggestions/`](../annotations/ai_suggestions/). Arkusze leżą poza gitem, w `annotations/sheets/ai_2026-10-26/`. Kopie oryginałów sprzed podpowiedzi są w `data/sheets_backup_2026-10-26/`.

## Jak weryfikować

W każdym arkuszu, za dotychczasowymi kolumnami, są szare kolumny `ai_*`: podpowiedź, `ai_uncertain` (wiersze z 1 są pomarańczowe) i `ai_reason`. Ostatnia jest żółta kolumna `verified`.

1. Sprawdź wiersz według codebooka.
2. Jeśli się nie zgadzasz, popraw żółtą etykietę.
3. Wpisz `verified = 1`.

Kolumn `ai_*` nie zmieniaj, bo z nich liczymy, ile podpowiedzi poprawiono. Importy (`annotation_sheets.read_workbook`, `stance.read_workbook`, `errors.read_review`) pomijają wiersze z podpowiedzią bez `verified = 1`. Bez `PARTIAL=1` zgłaszają je jako problem.

Gotowe pliki kopiujemy do `annotations/sheets/` pod tymi samymi nazwami.

| Zadanie | Plik | Wierszy z podpowiedzią | Kto weryfikuje |
|---|---|---|---|
| A: stanowisko | `stance_{pilot,gold}_{IS,JP}.xlsx` | 217 (187 postów) | IS, JP |
| B1: audyt H1-B | `audit_IS.xlsx`, `audit_JP.xlsx` | 180 i 180 (te same podpowiedzi) | IS, JP |
| B2: `pilot2` u IS | `pilot_IS.xlsx` (dopisane 30 + 30 wierszy) | 60 | IS |
| B3: spory pilotażu | `adjudication_pilot.xlsx` | 20 | IS i JP razem |
| B4: domeny H2 | `domain_review.csv` (5 proponowanych zmian w `reviewed_category`) | 222 | jedna osoba |
| B5: przyczyny błędów | `errors_dev.xlsx` | 345 | JP, a IS sprawdza 20% |

Uwagi do poszczególnych zadań:
- **B2:** `pilot_IS.xlsx` powstał z lokalnej, starszej kopii (Wikipedia 20 z 21 etykiet). Jeśli IS ma nowszy plik, trzeba dopisać `pilot2` do niego i wpisać podpowiedzi ponownie: `scripts/03d_prefill_sheet.py` z plikiem `pilot2_IS_claude-opus-5-5.csv`.
- **B4:** CSV nie ma importu. Do `codebook/domains.yaml` przenosimy tylko zweryfikowane wiersze.

## Co to zmienia w wynikach

- **Zgodność nie jest niezależna** tam, gdzie dwie osoby widzą tę samą podpowiedź: pilotaż stanowiska i audyt. α i κ podajemy jako zgodność po podpowiedzi AI, razem z odsetkiem poprawionych podpowiedzi. Niezależną miarę daje tylko kodowanie bez podpowiedzi z kopii oryginałów, na przykład przez jedną osobę.
- **B2:** IS koduje `pilot2` z podpowiedzią, a JP bez niej. Zgodność IS z JP mierzy więc w części zgodność AI z JP.
- **B3:** podpowiedź AI rozstrzyga spór. To wymaga wyraźnego ujawnienia w preprincie.
- **B4:** lista domen została już sklasyfikowana przez AI, więc druga klasyfikacja AI nie usuwa odstępstwa. Usuwa je tylko weryfikacja człowieka.
- **B5, możliwe błędy w gold:** w 20 jednostkach części `dev`, kodowanych przez jedną osobę, etykieta gold wydaje się niezgodna z codebookiem. Na przykład imgur oznaczony jako `social_blog` (R3), opis „ja nie znam” jako powołanie, rewerty i opisy narzędzi jako `personal` (R9). Dotyczy to 80 z 345 błędów: podpowiedź to `inne` z opisem w `ai_reason`. Jeśli weryfikacja to potwierdzi, część „błędów” instrumentów to błędy etykiet referencyjnych. Takie jednostki warto przekazać do uzgadniania, a w preprincie opisać jako ograniczenie gold standardu. Wynik testu instrumentów jest zamrożony i się nie zmienia.
