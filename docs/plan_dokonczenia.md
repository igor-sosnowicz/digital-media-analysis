# Plan dokończenia eksperymentów i preprintu (7 stron)

Stan na 27.10.2026:
- **Gotowe:** dane, codebook, gold, walidacja instrumentów źródeł, H1-B i H2, plan C (reguły, kolejki, podpowiedzi AI, próba wzbogacona), pakiet preprintu z makrami.
- **Brakuje:** weryfikacji przez ludzi, prawdziwego testu `stance_v1`, audytu i domen „na czysto” oraz tekstu.
- **Przebieg próbny** na etykietach AI ([`przebieg_probny_2026-10-27.md`](przebieg_probny_2026-10-27.md)): H1-A niemierzalne `stance_v1`, audyt konsensusu na granicy (J = 0,20), H1-B i H2 bez zmian.

## Etap 0. Porządki (ja, zgody: Ty)
1. Commit poprawek z przebiegu próbnego i wpisu z 27.10.
2. Szkic preprintu zaktualizowany do planu C ([`preprint_szkic.md`](preprint_szkic.md)).
3. Pakiet preprintu rozszerzony:
   - makra planu C (reguły, poprawki podpowiedzi AI), próby wzbogaconej, audytu H1-B i jakości `stance_v1`;
   - Tab. 3 z jakością odniesienia;
   - Rys. 2b: macierz pomyłek `stance_v1`.
4. Z `annotations/sheets/` usunąć arkusze stanowiska z podpowiedziami z sesji z 26.10 (kopie są w `data/sheets_backup_2026-10-26/`).

## Etap 1. Weryfikacja przez ludzi (IS, JP; 1–2 dni)

| Arkusz | Kto | Wierszy | Czas |
|---|---|---|---|
| `stance_pilot_{IS,JP}.xlsx` (puste, bez podpowiedzi, z kopii) | obie osoby osobno | 30 + 30 | 2 × 30 min |
| `stance_gold_IS`, `stance_enriched_IS` | IS | 47 + 112 | ~2,5 godz. |
| `stance_gold_JP`, `stance_enriched_JP` | JP | 65 + 111 | ~3 godz. |
| `audit_JP` | JP | 173 | ~2 godz. |
| `errors_dev` (v1 i GLiNER; IS sprawdza 20%) | JP | ~150 | ~1,5 godz. |
| `domain_review.csv` | jedna osoba | 102 | ~1,5 godz. |

Arkusze są w `annotations/sheets/llm/review/`. Poprawiacie etykietę i wpisujecie `verified = 1`; wierszy `auto` nie ruszacie. Gotowe pliki kopiujecie do `annotations/sheets/`.

## Etap 2. Stanowisko (ja; 1–2 godz.)
Skrót: `make after-verification` wykonuje kroki 1–3 i zatrzymuje się przed commitem zamrażającym.

1. `make import-stance PHASE=pilot`, `PHASE=gold`, `PHASE=enriched`.
2. `make llm-quality …` dla każdego arkusza.
3. Strojenie: `make validate-stance SPLIT=dev STANCE_TUNE=1 STANCE_APPLY=1`.
4. **Commit zamrażający** (Twoja zgoda).
5. **Jeden test:** `make validate-stance SPLIT=test FROZEN=1`.
6. `make label-h1` (działa tylko przy spełnionym warunku).

## Etap 3. Faza B (ja)
1. `make audit-metrics`; jeśli J konsensusu > 0,2, wskaźnik konsensusu staje się zastępczym testem H1.
2. `make errors IMPORT=1`.
3. Zmiany domen do `codebook/domains.yaml` z wpisem w preregistracji; H2 w dwóch wersjach.

## Etap 4. Testy potwierdzające (ja)
1. `make hypotheses CONFIRMATORY=1`.
2. Porównanie z poprzednimi wynikami.
3. Commit.

Skrót dla etapów 3–5 po jedynym teście: `make finish-results` (etykiety H1, audyt, błędy, testy, tabele, pakiet, kontrola i paczka dla Overleafa).

## Etap 5. Pakiet (ja)
`make report-tables` i `make preprint-package`. Nowe makra wypełnią się same; brakujące dane pokazują napis „[czeka na dane]”.

## Etap 6. Tekst (zespół, 2–3 dni)
Sekcje, budżet 7,0 strony i tezy: [`preprint_szkic.md`](preprint_szkic.md).

## Etap 7. Kontrola i oddanie
`make check-preprint` (z `STRICT=1` przed oddaniem; `ZIP=data/preprint_overleaf.zip` buduje paczkę). Zarzuty i odpowiedzi: [`zarzuty_red_teaming.md`](zarzuty_red_teaming.md).

1. Paczka dla Overleafa i kompilacja.
2. Kontrola makr.
3. Lista zarzutów na red teaming.
4. Push i PR.

## Harmonogram

| Dzień | Zespół | Ja |
|---|---|---|
| 1 | pilotaż, stanowisko | Etap 0 |
| 2 | audyt, błędy, domeny; sekcje 1–2 | Etapy 2–4 |
| 3 | sekcje 3–5 | Etap 5, lista zarzutów |
| 4 | sekcje 6–7, streszczenie | Etap 7 |
