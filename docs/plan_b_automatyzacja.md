# Plan B: automatyczne generowanie i weryfikacja annotacji

> **Zastąpiony przez plan C** ([`plan_c_reguly.md`](plan_c_reguly.md), wpis w `hipotezy.md` z 26.10.2026): bez modeli językowych. Ten opis zostaje dla historii; kod planu B jest nieużywany.

Zasady są w preregistracji: [`hipotezy.md`](hipotezy.md), wpis z 26.10.2026. W skrócie:
- dwóch annotatorów LLM (A1: Claude przez API, A2: lokalny otwarty model) etykietuje te same wiersze na podstawie samego codebooka;
- etykieta przechodzi automatycznie, gdy oba się zgadzają, są pewne, żadna reguła codebooka nie protestuje, a etykieta nie jest rzadka;
- ludzie sprawdzają resztę oraz losowe 15% przyjętych (próba kontrolna);
- instrument H1-A się nie zmienia: nadal `stance_v1`.

| Element | Plik |
|---|---|
| prompty, annotatorzy, reguły, kolejka | `src/digital_media_analysis/llm_annotation.py` |
| próba wzbogacona, ramka walidacyjna | `src/digital_media_analysis/stance.py` (`draw_enriched`, `validation_frame`) |
| annotacja (A1 albo A2) | `scripts/19_llm_annotate.py`, `make llm-annotate` |
| kolejka i arkusz do sprawdzenia | `scripts/20_review_queue.py`, `make llm-queue` |
| jakość annotacji AI | `scripts/21_llm_quality.py`, `make llm-quality` → `annotations/agreement/llm_quality.csv` |
| próba wzbogacona r/conspiracy | `scripts/03e_enriched_stance_sample.py`, `make enriched-stance` |
| odpowiedzi modeli (cache, poza gitem) | `data/llm_cache/*.jsonl` |
| etykiety bez tekstu i kolejki (w git) | `annotations/llm/*.csv` |

## 0. Warunki wstępne (raz)

1. **Commit poprawki i kodu.** Skrypt 19 odmawia pracy, dopóki `docs/hipotezy.md`, codebook i kod annotacji nie są zacommitowane.
2. **Dostęp do API dla A1.** Ustawiasz to Ty: zmienna `ANTHROPIC_API_KEY` albo `ant auth login`. Model: `claude-opus-5-5`, nakład `low`, odpowiedź w formacie JSON, z mechanizmem awaryjnym API przy odmowie (`fallbacks: "default"`). Koszt rzędu kilkunastu dolarów za około 1200 wierszy. Najpierw warto sprawdzić koszt na jednym arkuszu.
3. **Model A2.** `Qwen/Qwen2.5-3B-Instruct` (grupa `ml`). Przy pierwszym użyciu pobierze się około 6 GB. Na CPU to około 2–5 s na wiersz.

## 1. Stanowisko (H1.1)

```bash
make enriched-stance
```

Polecenie losuje 277 postów r/conspiracy (warstwy: temat konsensusu 67, termin naukowy 150, reszta 60). Zapisuje `annotations/hypotheses/stance_enriched_sample.csv` (do commita) i dwa puste arkusze `annotations/sheets/llm/stance_enriched_{IS,JP}.xlsx`.

Szablony gold to puste kopie arkuszy sprzed podpowiedzi: `data/sheets_backup_2026-10-26/stance_gold_{IS,JP}.xlsx`. Dla każdego z czterech arkuszy (gold IS, gold JP, enriched IS, enriched JP), np. gold JP:

```bash
make llm-annotate TASK=stance INPUT=data/sheets_backup_2026-10-26/stance_gold_JP.xlsx SHEET=Reddit ANNOTATOR=A1
make llm-annotate TASK=stance INPUT=data/sheets_backup_2026-10-26/stance_gold_JP.xlsx SHEET=Reddit ANNOTATOR=A2
make llm-queue TASK=stance INPUT=data/sheets_backup_2026-10-26/stance_gold_JP.xlsx SHEET=Reddit A1=annotations/llm/stance_gold_JP_Reddit_A1.csv A2=annotations/llm/stance_gold_JP_Reddit_A2.csv OUTPUT=annotations/sheets/llm/review/stance_gold_JP.xlsx
```

**Weryfikacja przez ludzi:** w `annotations/sheets/llm/review/` sprawdzacie tylko wiersze z `decided_by = human` (pomarańczowe). Kolumna `queue_reason` mówi, dlaczego wiersz trafił do kolejki: spór, niska pewność, rzadka etykieta (`challenges`) albo kontrola.
1. Popraw `consensus_stance`, jeśli trzeba.
2. Wpisz `verified = 1`.

Wierszy z `decided_by = auto` nie ruszacie.

**Przeniesienie:**
1. Z `annotations/sheets/` usuń arkusze `stance_*.xlsx` z podpowiedziami z sesji. Kopie są w `data/sheets_backup_2026-10-26/`, a pilotaż stanowiska w planie B nie jest potrzebny.
2. Skopiuj tam cztery sprawdzone arkusze.

Potem:

```bash
make import-stance PHASE=gold
make import-stance PHASE=enriched
make llm-quality NAME=stance_gold_JP TASK=stance QUEUE=annotations/llm/stance_gold_JP_queue.csv REVIEWED=annotations/sheets/stance_gold_JP.xlsx SHEET=Reddit
```

(`llm-quality` uruchamiamy dla każdego arkusza.)

Dalej jak w [`h1a_kroki.md`](h1a_kroki.md), punkty 3–8:
1. strojenie progów na wszystkich wierszach `dev`;
2. commit zamrażający;
3. **jeden** test: warunek trafności rozstrzygany na wierszach sprawdzonych przez ludzi, z wagą / `p_review`; wersja na wszystkich wierszach w `gate_all_rows`;
4. `make label-h1`;
5. `make hypotheses CONFIRMATORY=1`;
6. `make preprint-package`.

## 2. Faza B

| Zadanie | Szablon (`INPUT`) | `TASK` | `SHEET` | `KEY` | Po sprawdzeniu |
|---|---|---|---|---|---|
| audyt H1-B (jedna osoba) | `data/sheets_backup_2026-10-26/audit_JP.xlsx` | `sources_reddit` | `Reddit` | `unit_id` | skopiować do `annotations/sheets/audit_JP.xlsx`, `make audit-metrics` |
| przyczyny błędów | `annotations/sheets/errors_dev.xlsx` (oryginał bez przyczyn) | `error_cause` | `Błędy` | `unit_id platform instrument variable` | skopiować do `annotations/sheets/errors_dev.xlsx`, `make errors IMPORT=1` |
| domeny H2 | `annotations/hypotheses/domain_review.csv` | `domain` | – | `domain` | zmiany kategorii przenoszę do `codebook/domains.yaml`, H2 w dwóch wersjach |

Uwagi:
- **Audyt:** `audit_IS.xlsx` w `annotations/sheets/` zostaje pusty. Skrypt audytu czyta tylko wiersze z etykietą, więc etykietą referencyjną jest arkusz JP po sprawdzeniu.
- **Domeny:** każda domena, której kategoria by się zmieniła, trafia do kolejki (`queue_reason = zmiana kategorii`), podobnie jak `social_blog` i `unknown`.
- **`pilot2` i uzgadnianie sporów pilotażu** nie wchodzą do planu B. Zgodność dwóch osób zastępuje zgodność A1 z A2 i próba kontrolna. Dotychczasowe wyniki pilotażu (32 + 21 jednostek) zostają w preprincie jako zgodność ludzi przed automatyzacją.

## 3. Co trafia do preprintu

- **Sekcja 3:** procedura (A1, A2, reguły, kolejka, 15% kontroli) i tabela z `llm_quality.csv`:
  - zgodność A1 z A2 (κ);
  - udział przyjętych automatycznie;
  - odsetek sugestii zachowanych na próbie kontrolnej, z przedziałem.
- **Sekcja 4:** `stance_v1`: warunek trafności główny (wiersze sprawdzone przez ludzi) i wrażliwość (wszystkie).
- **Sekcja 6:** ograniczenia: odniesienie zbudowane z udziałem LLM, wersje modeli w API, wielkość próby kontrolnej.
- **Sekcja 7:** modele, skróty promptów (`system_sha`), liczby decyzji ludzi i ich poprawek.
