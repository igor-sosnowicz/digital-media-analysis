# Plan C: reguły codebooka i ludzie, bez modeli językowych

Zasady są w preregistracji [`hipotezy.md`](hipotezy.md), wpis z 26.10.2026 o planie C. Nie korzystamy z zewnętrznego API ani z lokalnych modeli językowych.

- Reguły codebooka etykietują tylko jednostki, które rozstrzygają same (`src/digital_media_analysis/rule_annotation.py`).
- Resztę kodują ludzie, na ślepo.
- Losowe 15% etykiet z reguł ludzie sprawdzają na ślepo; z tego liczymy precyzję reguł.
- Próba wzbogacona, wagi i warunek trafności H1-A są takie jak w planie B. Instrument H1-A to nadal `stance_v1`.

## 0. Przed startem

1. Commit wpisu w `docs/hipotezy.md` i kodu reguł. Skrypt 22 do tego czasu odmawia pracy.
2. Z `annotations/sheets/` usuń arkusze z podpowiedziami AI z sesji: `stance_*.xlsx` i ewentualnie skopiowane `audit_*`, `errors_dev.xlsx`. Puste oryginały są w `data/sheets_backup_2026-10-26/`.

## 1. Arkusze dla ludzi

```bash
make enriched-stance
```

Polecenie zapisuje próbę wzbogaconą (277 postów r/conspiracy) i puste arkusze `annotations/sheets/llm/stance_enriched_{IS,JP}.xlsx`. Potem dla każdego arkusza budujemy kolejkę (`OUTPUT` w `annotations/sheets/llm/review/`):

| Arkusz | `TASK` | `INPUT` (pusty szablon) | `SHEET` | `KEY` | Szacunek (reguła / człowiek) |
|---|---|---|---|---|---|
| stanowisko gold IS | `stance` | `data/sheets_backup_2026-10-26/stance_gold_IS.xlsx` | `Reddit` | | 20 / 47 |
| stanowisko gold JP | `stance` | `data/sheets_backup_2026-10-26/stance_gold_JP.xlsx` | `Reddit` | | 25 / 65 |
| stanowisko wzbogacone IS i JP | `stance` | `annotations/sheets/llm/stance_enriched_{IS,JP}.xlsx` | `Reddit` | | 27 / 112 (IS), 27 / 111 (JP) |
| audyt H1-B (JP) | `sources_reddit` | `data/sheets_backup_2026-10-26/audit_JP.xlsx` | `Reddit` | | 7 / 173 |
| przyczyny błędów | `error_cause` | `data/sheets_backup_2026-10-26/errors_dev.xlsx` | `Błędy` | `unit_id platform instrument variable` | 77 / 268 |
| domeny H2 | `domain` | `annotations/hypotheses/domain_review.csv` | | `domain` | 120 / 102 |

Przykład:

```bash
make rule-queue TASK=stance INPUT=data/sheets_backup_2026-10-26/stance_gold_JP.xlsx SHEET=Reddit OUTPUT=annotations/sheets/llm/review/stance_gold_JP.xlsx
```

**Pilotaż stanowiska bez reguł** (niezależna zgodność ludzi): obie osoby kodują puste `data/sheets_backup_2026-10-26/stance_pilot_{IS,JP}.xlsx`. Kopiujecie je do `annotations/sheets/` i importujecie: `make import-stance PHASE=pilot`.

## 2. Kodowanie

W arkuszach kolejki:
- **Wiersze `decided_by = auto` są szare.** Mają etykietę z reguły i liczą się bez sprawdzania.
- **Wiersze `decided_by = human` są pomarańczowe** (`queue_reason = do zakodowania`). Nie mają etykiety. Kodujecie je według codebooka i wpisujecie `verified = 1`.
- Część z nich to kontrola reguł. Arkusz tego nie pokazuje, żeby ocena była ślepa.

Sprawdzenie w trakcie: `make check-stance PHASE=gold PARTIAL=1`.

## 3. Import i wyniki

1. Sprawdzone arkusze kopiujecie do `annotations/sheets/` pod tymi samymi nazwami (`stance_gold_IS.xlsx`, `stance_enriched_JP.xlsx`, `audit_JP.xlsx`, `errors_dev.xlsx`). Domeny trafiają do mnie, a ja przenoszę zmiany do `codebook/domains.yaml`.
2. Precyzja reguł na próbie kontrolnej, dla każdego arkusza:
   ```bash
   make llm-quality NAME=stance_gold_JP TASK=stance QUEUE=annotations/llm/stance_gold_JP_queue.csv REVIEWED=annotations/sheets/stance_gold_JP.xlsx SHEET=Reddit
   ```
3. Stanowisko:
   1. `make import-stance PHASE=gold` i `PHASE=enriched`;
   2. strojenie, commit zamrażający, jeden test;
   3. `make label-h1`;
   4. `make hypotheses CONFIRMATORY=1`.

   Szczegóły: [`h1a_kroki.md`](h1a_kroki.md), kroki 3–8.
4. Faza B: `make audit-metrics`, `make errors IMPORT=1`, H2 po zmianach domen.
5. `make preprint-package`.

## 4. Nakład ludzi

Około 650 decyzji, czyli 9–11 godz. na dwie osoby.

## 5. W preprincie

- **Sekcja 3:**
  - procedura (reguły z numerami z codebooka, kodowanie na ślepo, 15% kontroli);
  - precyzja każdej reguły z przedziałem;
  - zgodność ludzi na pilotażu stanowiska.
- **Sekcja 4:** warunek trafności `stance_v1` na wierszach zakodowanych przez ludzi (główny) i na wszystkich (wrażliwość).
- **Sekcja 6:** reguły pokrywają tylko łatwe przypadki; regułę stanowiska zawęziliśmy po porównaniu z wstępnymi etykietami AI (wpis w preregistracji).
- **Sekcja 7:** bez modeli językowych w annotacji; AI pisało kod.
