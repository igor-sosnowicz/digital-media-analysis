# H1-A: od kodowania stanowiska do testu potwierdzającego

> **26.10.2026: plan B.** Etykiety referencyjne stanowiska mogą powstać automatycznie (dwóch annotatorów LLM, kolejka i 15% kontroli przez ludzi), z dodatkową próbą wzbogaconą r/conspiracy. Procedura i polecenia: [`plan_b_automatyzacja.md`](plan_b_automatyzacja.md). Kroki 3–8 poniżej się nie zmieniają.

Instrukcja dokończenia głównego testu hipotezy H1 (preregistracja [`hipotezy.md`](hipotezy.md)). Kod, arkusze i surowe wyniki modelu są gotowe. Brakuje tylko ludzkich etykiet stanowiska. Cały potok przeszedł próbny przebieg na sztucznych etykietach w kopii repozytorium (25.10.2026).

## 1. Kodowanie (ludzie)

| Plik w `annotations/sheets/` | Kto | Postów | Do czego |
|---|---|---|---|
| `stance_pilot_IS.xlsx` | IS | 30 | zgodność (te same posty co JP, runda `pilot2`) |
| `stance_pilot_JP.xlsx` | JP | 30 | zgodność |
| `stance_gold_IS.xlsx` | IS | 67 (dev 34, test 33) | strojenie i test instrumentu |
| `stance_gold_JP.xlsx` | JP | 90 (dev 45, test 45) | strojenie i test instrumentu |

Zasady są w [`instrukcja_annotacji_reddit.md`](instrukcja_annotacji_reddit.md), sekcja 11, i w regule R14 codebooka:
- kolumna `consensus_stance`: jedna wartość z listy (`supports`, `challenges`, `neutral`, `not_applicable`);
- w razie wątpliwości `uncertain = 1` i krótki opis w `notes`;
- kodujcie każdy swój arkusz samodzielnie, bez porównywania z drugą osobą przed końcem;
- nie zmieniajcie kolumn `unit_id` ani kolejności wierszy.

**Sprawdzenie arkusza przed oddaniem** (także w trakcie, wtedy z `PARTIAL=1`):

```bash
make check-stance PHASE=pilot
make check-stance PHASE=gold
```

Polecenie niczego nie zapisuje. Wypisuje błędy (np. pusta komórka, wartość spoza listy, inna osoba w kolumnie `annotator`) albo „OK” z liczbą etykiet. Gotowe pliki zostają w `annotations/sheets/`, bo są poza gitem.

### Podpowiedzi AI i weryfikacja (od 26.10.2026)

Wszystkie cztery arkusze mają wstępnie wypełnioną kolumnę `consensus_stance`. Wypełnił ją asystent AI (Claude Opus 5.5) na podstawie tytułu, treści i adresu linku, bez otwierania linków i bez wyników `stance_v1`.

Podpowiedzi są w git: [`annotations/ai_suggestions/stance_claude-opus-5-5.csv`](../annotations/ai_suggestions/stance_claude-opus-5-5.csv) (187 postów, bez tekstu). Dla każdego posta jest tam:
- etykieta;
- `ai_uncertain`: 1 przy 46 postach, w których AI miało wątpliwości;
- krótkie uzasadnienie.

Do arkuszy wpisał je skrypt `scripts/03c_prefill_stance.py`. Kopie arkuszy sprzed podpowiedzi są w `data/sheets_backup_2026-10-26/`.

W arkuszu dochodzą cztery kolumny za `annotator`:

| Kolumna | Kto | Znaczenie |
|---|---|---|
| `ai_stance` | AI (szara, nie zmieniać) | oryginalna podpowiedź |
| `ai_uncertain` | AI (pomarańczowa przy 1) | wątpliwość AI; te wiersze sprawdzić szczególnie uważnie |
| `ai_reason` | AI | uzasadnienie podpowiedzi |
| `verified` | **osoba** (żółta) | `1` po sprawdzeniu wiersza |

**Weryfikacja wiersza:**
1. Przeczytaj tytuł, treść i link, oceń według R14.
2. Jeśli się nie zgadzasz, popraw `consensus_stance`. Własne wątpliwości zaznacz w `uncertain` i `notes`.
3. Wpisz `verified = 1`.

Import liczy tylko wiersze z `verified = 1`. Bez `PARTIAL=1` odrzuca arkusz, w którym zostały niesprawdzone podpowiedzi. Po imporcie zapisuje `annotations/agreement/<faza>_stance_ai_review.csv`: ile podpowiedzi każda osoba sprawdziła i ile zmieniła. To liczba do ujawnienia roli AI w preprincie.

**Konsekwencje dla wyników:**
- **Zgodność pilotażu nie jest niezależna**, bo IS i JP widzą tę samą podpowiedź. Jeśli obie osoby ją przyjmą, κ wyjdzie bliskie 1. W raporcie podajemy ją jako zgodność po podpowiedzi AI, razem z odsetkiem zmienionych podpowiedzi. Niezależną miarę daje tylko kodowanie pilotażu bez podpowiedzi: przywrócić `stance_pilot_*.xlsx` z kopii.
- Etykiety referencyjne to etykiety AI zweryfikowane przez człowieka. Walidacja `stance_v1` sprawdza więc zgodność z takim odniesieniem. Opisujemy to w sekcji o ujawnieniu użycia AI.
- **Mało postów `challenges`:** według podpowiedzi 1 w części `dev`, 3 w części testowej i 3 w `pilot2`. Strojenie progów i F1 dla `challenges` w warunku trafności opierają się więc na pojedynczych postach. Warto to rozważyć przed testem (pkt 3).

## 2. Potok (po kodowaniu; uruchamia osoba z modelem, około 30 minut)

| Krok | Polecenie | Co powstaje | Punkt decyzji |
|---|---|---|---|
| 1 | `make import-stance PHASE=pilot` | `annotations/labels/pilot/stance_*.csv`, `annotations/agreement/pilot_stance_agreement.csv` | zgodność dwóch osób (α, κ) do raportu |
| 2 | `make import-stance PHASE=gold` | `annotations/labels/gold/stance_*.csv` | – |
| 3 | `make validate-stance SPLIT=dev STANCE_TUNE=1 STANCE_APPLY=1` | `annotations/validation/stance_dev_tuning.csv`; najlepsze progi wpisane do `instruments/stance_v1.py` i `TUNED = True` | przejrzeć `git diff` instrumentu |
| 4 | commit: „Freezes stance_v1 thresholds tuned on dev” | zamrożony instrument | **przed testem**, inaczej krok 5 odmówi |
| 5 | `make validate-stance SPLIT=test FROZEN=1` | `stance_test_metrics.csv`, `stance_test_run.json` z wynikiem warunku trafności | **warunek trafności: F1 dla `challenges` ≥ 0,5 i κ ≥ 0,4.** Test uruchamia się tylko raz; drugi przebieg skrypt odrzuci |
| 6 | `make label-h1` | `annotations/frame_labels/h1_stance_v1.csv` (6240 postów), tylko gdy warunek jest spełniony | – |
| 7 | `make hypotheses CONFIRMATORY=1` | `annotations/hypotheses/confirmatory_*` z H1-A, H1-B i H2 | porównać H1-B i H2 z poprzednim przebiegiem (`git diff`): mają być identyczne |
| 8 | commit wyników, `make report-tables`, `make preprint-package` | tabele i makra preprintu z H1-A | dopisać wynik do `docs/wyniki_hipotez.md` |

## 3. Interpretacja wyniku

| Sytuacja | Werdykt dla H1 (według preregistracji) |
|---|---|
| warunek spełniony, `challenges` rośnie, jednostronne p < 0,05 | H1-A potwierdzona |
| warunek spełniony, brak istotnego wzrostu | H1-A niepotwierdzona: wynik negatywny, raportowany na równi z pozytywnym |
| warunek **niespełniony** | H1-A niemierzalna instrumentem `stance_v1`. Zastępczy wskaźnik konsensusu z H1-B wymaga audytu, którego nie ma, więc H1 zostaje bez testu potwierdzającego. To wynik negatywny co do pomiaru |

Analizy wrażliwości są w preregistracji: tylko r/science, tylko r/conspiracy, lata 2005–2020. Udział `supports` (kierunek: spadek) jest wskaźnikiem pobocznym.

## 4. Co jest już przygotowane

- Wyniki modelu dla 6240 postów próby H1 są w cache (`data/model_cache/stance_v1_h1.csv`). Krok 6 nie liczy ich od nowa.
- Etykiety stanowiska leżą obok etykiet źródeł (`annotations/labels/<faza>/stance_*.csv`), ale skrypty etykiet źródeł je pomijają. Bez tego import stanowiska psułby walidację i test potwierdzający.
- Skrypt 07b sprawdza warunek trafności i zapisuje wynik. Skrypt 08 etykietuje próbę tylko po spełnieniu warunku, więc skrypt 09 nie policzy H1-A na niezwalidowanym instrumencie.
- Część `dev` ma 79 postów, a część testowa 78. Przy tak małej próbie progi mogą być niestabilne. Wynik podajemy z przedziałami.
- Wyniki modelu dla 157 postów gold też są już w cache (`stance_v1_dev.csv`, `stance_v1_test.csv`), więc kroki 3 i 5 nie liczą modelu od nowa, o ile wszystkie posty dostaną etykietę. Policzenie ich na CPU zajęło około 40 minut.
- **Próbny przebieg (25.10.2026)** w osobnej kopii repozytorium, na sztucznych etykietach: wszystkie kroki 1–7 zadziałały. Drugi przebieg testu został odrzucony, a wyniki H1-B i H2 w teście potwierdzającym były identyczne z zacommitowanymi.
- Przy remisie wielu zestawów progów na `dev` skrypt wybiera pierwszy w kolejności siatki (najniższe progi). Wybór widać w `stance_dev_tuning.csv`.
