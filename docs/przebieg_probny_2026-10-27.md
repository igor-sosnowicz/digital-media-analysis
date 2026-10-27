# Przebieg próbny na etykietach AI (27.10.2026)

**Wyniki wstępne, nie do raportowania jako wynik potwierdzający.** Cały potok uruchomiłem w osobnej kopii repozytorium (commit `c2cbafe` i jeden lokalny commit zamrażający). Etykiety AI z arkuszy planu C zostały tam potraktowane tak, jakby ludzie je sprawdzili (`verified = 1` wpisane automatycznie, tylko w kopii).

W prawdziwym repozytorium nic się nie zmieniło: `stance_v1` jest nienastrojony, prawdziwy jednorazowy test nie został użyty, arkusze i etykiety są nietknięte. Wyniki kopii zapisałem poza gitem, w `data/dryrun_2026-10-27/`.

## Co uruchomiono

| Krok | Wynik |
|---|---|
| import stanowiska (gold 157, próba wzbogacona 277) | etykiety reguł i AI; brak pilotażu, więc brak zgodności ludzi |
| strojenie na `dev` (218 postów: gold 79, wzbogacona 139) | progi: relevance 0,30, supports 0,30, challenges 0,70; F1 `challenges` 0,25, κ 0,33 |
| commit zamrażający i **jeden test** na `test` (216 postów: gold 78, wzbogacona 138) | **warunek trafności niespełniony**: F1 `challenges` 0,33 (próg 0,5), κ 0,24 (próg 0,4); na wszystkich wierszach κ 0,27 |
| `08_label_h1_sample.py` | odmówił etykietowania próby H1 stanowiskiem, tak jak przewiduje preregistracja |
| audyt H1-B (`07c`, arkusz JP) | wskaźnik konsensusu: J = 0,20 (łącznie), czyli tylko opis; wskaźnik alternatywny: J = 0,59, ważny |
| test potwierdzający (`09`) | H1-B i H2 identyczne jak dotąd: konsensus OR/rok 1,026 (p = 0,93), alternatywne 0,988 (p = 0,85), H2 1,470 (p = 0,006) |
| przyczyny błędów (`11 --import`) | Pareto z przyczyn „potwierdzonych”: v1 głównie „pominięte pole url” (71 z 127), GLiNER „brak kontekstu” (34 z 88) |
| pakiet preprintu (`18`) | stan H1-A: `gate_failed`; makra metryk wypełnione, makra trendów H1-A pozostają zastępcze |

## Co to znaczy dla wyników (gdyby ludzie potwierdzili etykiety)

1. **H1-A (H1.1): niemierzalne instrumentem `stance_v1`.** To wynik negatywny co do pomiaru.

   Przyczyna jest wyraźna w macierzy pomyłek na teście (wartości nieważone):

   | odniesienie \ `stance_v1` | challenges | neutral | not_applicable |
   |---|---|---|---|
   | challenges (42) | 7 | 12 | 23 |
   | neutral (43) | 0 | 20 | 23 |
   | not_applicable (122) | 2 | 15 | 105 |
   | supports (9) | 0 | 1 | 8 |

   Model jest precyzyjny dla `challenges` (precyzja 0,81), ale wyłapuje mało takich postów (czułość 0,21). Większość postów podważających naukę uznaje za niezwiązane z nauką i nigdy nie przypisuje `supports`. Próba wzbogacona zadziałała: na teście jest 42 postów `challenges` zamiast 3, więc wynik negatywny nie wynika z małej liczby przypadków.
2. **H1 bez testu potwierdzającego.** Zgodnie z preregistracją zastępczym testem byłby wskaźnik konsensusu z H1-B, ale jego audyt daje J = 0,20, a reguła wymaga J > 0,2. Wskaźnik źródeł alternatywnych przechodzi audyt (J = 0,59) i ma wynik negatywny (brak wzrostu).
3. **H2 bez zmian:** istotna formalnie, ale artefakt pomiaru (WHO i GIS).

## Ważne zastrzeżenia

- **Odniesienie to etykiety AI bez sprawdzenia przez ludzi.** Po weryfikacji liczby się zmienią. Kierunek wniosku dla H1-A (duża rozbieżność ze `stance_v1`) jest jednak wyraźny.
- **Widzieliśmy już wynik na części testowej** (na etykietach AI). Prawdziwy test po weryfikacji obejmie te same posty i ten sam zamrożony sposób strojenia. Ten przebieg trzeba ujawnić w preregistracji (sekcja „Zmiany”) i w preprincie. Zmiana instrumentu lub progów warunku trafności po tym przebiegu byłaby decyzją podjętą po zobaczeniu wyniku i musiałaby być raportowana jako analiza eksploracyjna.
- **J audytu (0,20)** leży dokładnie na granicy reguły, więc po weryfikacji przez ludzi może się przesunąć w każdą stronę.

## Co poprawić w kodzie przed prawdziwym przebiegiem

1. `09_test_hypotheses.py` wypisuje „H1-A: czeka na etykiety stanowiska”, także gdy warunek trafności jest niespełniony. Powinien podawać stan z `stance_test_run.json`.
2. `18_preprint_package.py` przy stanie `gate_failed` zostawia w makrach trendów H1-A napis „[czeka na H1-A]”. Powinien wpisać „nie testowano (warunek trafności niespełniony)”.
3. Licznik `ai_review` w `04b` liczy także wiersze z reguł (mają `ai_consensus_stance`). Powinien liczyć tylko wiersze z `decided_by = human`.

## Następne kroki

1. Weryfikacja arkuszy przez ludzi (`verified = 1`) i pilotaż stanowiska bez podpowiedzi.
2. Wpis w preregistracji o tym przebiegu próbnym.
3. Prawdziwy potok według `docs/plan_c_reguly.md`.
