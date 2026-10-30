# Wyniki weryfikacji hipotez H1 i H2

*24.10.2026.* Przebieg potwierdzający `scripts/09_test_hypotheses.py --confirmatory` na preregistracji zacommitowanej jako `440b5fb` ([`docs/hipotezy.md`](hipotezy.md)). Tabele: `annotations/hypotheses/confirmatory_trends.csv` i `confirmatory_yearly.csv`; ustawienia i commit: `confirmatory_run.json`. Odstępstwa od planu są zapisane w preregistracji przed uruchomieniem:
- przegląd domen wykonał tylko asystent AI, nie człowiek;
- audyt kategorii nie został zrobiony;
- H1-A czeka na etykiety stanowiska.

Trend to iloraz szans (OR) na rok z ważonej regresji logistycznej z efektami stałymi subredditu albo strony, z 95% przedziałem i jednostronną wartością p w kierunku hipotezy.

## H1: spadek zaufania do konsensusu naukowego (Reddit 2005–2018)

- **H1-A (test główny): jeszcze nie przetestowane.** Nie ma ludzkich etykiet stanowiska, więc `stance_v1` nie został nastrojony ani zwalidowany. Arkusze stanowiska czekają na kodowanie.
- **H1-B (wskaźniki poboczne):** próba analityczna ma 6240 postów, w okresie głównym 5154 posty z powołaniem.

  | Wskaźnik (oczekiwany kierunek) | Analiza | OR / rok [95% CI] | p jednostronne |
  |---|---|---|---|
  | Źródła konsensusu (spadek) | główna | 1,03 [0,99; 1,06] | 0,93 |
  | | 2005–2020 | 1,04 [1,01; 1,08] | 0,99 |
  | | tylko r/science | 1,03 [0,99; 1,07] | 0,95 |
  | | tylko r/conspiracy | 1,01 [0,90; 1,14] | 0,58 |
  | Źródła alternatywne (wzrost) | główna | 0,99 [0,97; 1,01] | 0,85 |
  | | 2005–2020 | 0,99 [0,98; 1,01] | 0,76 |
  | | tylko r/science | 0,99 [0,96; 1,02] | 0,83 |
  | | tylko r/conspiracy | 1,00 [0,95; 1,04] | 0,59 |

- **Wniosek dla H1-B:** dane nie wspierają hipotezy.
  - Surowe ważone udziały zmieniają się w oczekiwanym kierunku: źródła konsensusu spadają z ok. 0,22 (2006) do 0,10–0,14 (2016–2018), a źródła alternatywne rosną z ok. 0,35 do 0,45–0,47.
  - Po uwzględnieniu subredditu trend znika, także osobno w r/science i w r/conspiracy.
  - Zmiana w danych łącznych wynika więc ze zmiany składu, czyli rosnącego udziału r/conspiracy, a nie ze zmiany postów w obrębie subredditów.
  - Wskaźnik konsensusu jest tylko opisowy (brak audytu).
  - Udziały skorygowane metodą Rogana–Gladena są niewiarygodne (wiele zer), bo gold zawiera bardzo mało przypadków `scientific` i `institutional`.
- **Status H1:** nie ma testu potwierdzającego, dopóki nie powstanie H1-A. Wskaźniki źródeł nie wspierają hipotezy.

## H2: częstsze powołania na źródła alternatywne (Wikipedia 2020–2026)

| Analiza | OR / rok [95% CI] | p jednostronne | linki | linki alternatywne |
|---|---|---|---|---|
| **główna** | **1,47 [1,09; 1,99]** | **0,006** | 1207 | 10 |
| bez strony COVID-19 | 1,39 [0,83; 2,33] | 0,10 | 105 | 2 |
| bez roku 2020 | 1,36 [0,78; 2,37] | 0,14 | 435 | 6 |
| tylko domeny sklasyfikowane | 1,47 [1,09; 1,98] | 0,005 | 1199 | 10 |
| *permutacja lat między rewizjami w obrębie strony (eksploracyjna, spoza preregistracji)* | *1,47* | *0,07* | 1207 | 10 |

- **Dane:**
  - w latach 2020–2026 dodano 1341 linków do przypisów, z czego 10 to domeny alternatywne;
  - te linki leżą w 9 rewizjach dwóch stron: COVID-19 (pscp.tv w 2020, 2021 i 2023 r., twitter.com w 2023 r.) i Globalne ocieplenie (video.google.com w 2021 r., monbiot.com w 2025 r.);
  - model z efektami stałymi korzysta tylko ze stron, na których wystąpił choć jeden link alternatywny (1207 linków).
- **Roczne udziały linków alternatywnych:** 0,5% (2020), 0,8% (2021), 0% (2022), 1,5% (2023), 0% (2024), 4,8% (2025, 1 z 21 linków), 0% (2026).
- **Wniosek dla H2:**
  - test główny spełnia kryterium z preregistracji (p < 0,05), więc formalnie hipoteza jest potwierdzona;
  - dowód jest słaby i niestabilny: wynik opiera się na 10 zdarzeniach, a „wzrost” wynika głównie z tego, że po 2020 r. dodawano znacznie mniej linków, przy kilku pojedynczych linkach alternatywnych;
  - analizy wrażliwości (bez 2020, bez COVID-19) i eksploracyjny test permutacyjny nie są istotne;
  - przy tak rzadkich zdarzeniach błędy z regresji logistycznej mogą być zaniżone.

  Uczciwie: wynik zgodny z H2, ale niekonkluzywny. Listę domen trzeba jeszcze przejrzeć ręcznie (odstępstwo 1). Sprawdzenie pomiaru w następnej sekcji pokazuje, że po przypisaniu wpisów do ich właścicieli dane nie wspierają H2.

## H2: analizy odporności i sprawdzenie pomiaru (eksploracyjne, 24.10.2026)

Analizy spoza preregistracji, na tych samych danych: `scripts/10_h2_robustness.py` (`make h2-robustness`), `src/digital_media_analysis/robustness.py`. Tabele: `annotations/hypotheses/exploratory_h2_robustness.csv` i `exploratory_h2_leave_one_out.csv`; permutacja: `exploratory_h2_permutation.json`; dokładny test: `exploratory_h2_exact_by_owner.json`. Regresja Firtha (logit z karą, odporny na rzadkie zdarzenia, zostawia też strony bez linków alternatywnych) ma test ilorazu wiarygodności z karą i przedział z tej samej profilowanej penalizowanej wiarygodności; implementację sprawdza wynik dokładny dla tabeli 2×2.

**Poprawka z 30.10.2026.** Pierwsza wersja tej tabeli (24.10) miała dwa błędy w wierszach Firtha:
- **test ilorazu wiarygodności** porównywał model z rokiem z modelem bez roku, każdy z inną karą Firtha. Różnica kar dodawała do statystyki około 3 (dla wszystkich stron 6,29 zamiast 3,06), więc $p$ wychodziło za małe;
- **przedział** był przedziałem Walda, niezgodnym z tym testem.

Teraz $p$ i przedział pochodzą z profilowanej penalizowanej wiarygodności (Heinze i Schemper 2002): współczynnik roku jest ustalony, a kara liczona dla pełnego modelu. Wynik sprawdzono niezależną optymalizacją numeryczną.

Tabela pochodzi też z danych po przeglądzie domen z 27.10, dlatego zmieniły się definicja szeroka i źródła ustalone.

Permutacja i test dokładny powstały 24.10 kodem spoza repozytorium; teraz liczy je skrypt 10 (permutacja: $p$ = 0,070 zamiast 0,0705, test dokładny bez zmian).

| Analiza | Efekt / rok [95% CI] | p jednostronne | zdarzenia |
|---|---|---|---|
| model z preregistracji (dla porównania) | OR 1,47 [1,09; 1,99] | 0,006 | 10 |
| Firth, wszystkie strony | OR 1,43 [0,96; 2,16] | 0,040 | 10 |
| Firth, bez efektów stałych | OR 1,32 [0,92; 1,80] | 0,062 | 10 |
| Firth, bez 2026 (rok niepełny) | OR 1,46 [0,96; 2,22] | 0,038 | 10 |
| Firth, bez 2020 | OR 1,27 [0,72; 2,43] | 0,196 | 6 |
| Firth, bez COVID-19 | OR 1,31 [0,72; 2,48] | 0,170 | 2 |
| poziom rewizji: czy dodała link alternatywny (Firth) | OR 2,25 [1,22; 4,20] | 0,004 | 9 |
| poziom rewizji: liczba linków alternatywnych (Poisson) | RR 1,46 [1,09; 1,97] | 0,006 | 10 |
| tylko media społecznościowe i wideo (bez blogów) | OR 1,31 [0,82; 2,03] | 0,120 | 9 |
| szeroka definicja (social_blog, other, niesklasyfikowane) | OR 1,03 [0,90; 1,19] | 0,327 | 175 |
| źródła ustalone (scientific, institutional) maleją | OR 0,99 [0,84; 1,17] | 0,445 | 739 |
| bez jednego linku alternatywnego (10 przeliczeń) | OR 1,33–1,67 | p < 0,05 w 7 z 10; największe 0,055 | 9 |
| permutacja lat między rewizjami (już w wynikach) | OR 1,47 | 0,070 | 10 |

**Sprawdzenie pomiaru: co jest „źródłem alternatywnym”.** Przeczytaliśmy wszystkie 10 linków.

- **8 z 10 to oficjalne źródła instytucjonalne udostępnione na platformach społecznościowych:**
  - transmisja konferencji WHO na Periscope (`pscp.tv/WHO/…`): jeden i ten sam link dodany 6 razy (2020 ×4, 2021, 2023), najpewniej przy cofaniu i przywracaniu edycji;
  - wpis Głównego Inspektoratu Sanitarnego na Twitterze (`twitter.com/GIS_gov/…`): dodany 2 razy w 2023 r.
- **Prawdziwie alternatywne są tylko 2 linki**, oba na stronie Globalne ocieplenie: film z video.google.com (2021) i wpis z bloga George'a Monbiota (2025).
- **Wniosek o mierze:** klasyfikacja po domenie nie odróżnia konta instytucji od blogera czy influencera, a miara „dodanych linków” liczy wielokrotnie link przywracany po rewertach.

| Sprawdzenie pomiaru | Efekt / rok [95% CI] | p jednostronne | zdarzenia |
|---|---|---|---|
| tylko pierwsze dodanie każdego linku na stronie (Firth) | OR 1,59 [0,92; 3,74] | 0,048 | 4 |
| właściciel posta: wpisy WHO i GIS jako instytucjonalne (Firth) | OR 1,31 [0,73; 2,50] | 0,169 | 2 |
| właściciel posta, dokładny test warunkowy (2 linki wśród 105 linków strony) | lata 2021 i 2025 | 0,21 | 2 |

Test ilorazu wiarygodności przy 2 zdarzeniach jest mało wiarygodny, bo asymptotyka nie działa. Rozstrzyga test dokładny: p = 0,21. Po poprawce z 30.10 logit Firtha daje zgodny wynik (p = 0,17); wcześniejsze p = 0,027 było skutkiem błędu w teście.

**Wniosek dla H2.** Formalne potwierdzenie z testu preregistrowanego (p = 0,006) jest artefaktem pomiaru. Wzrost tworzą głównie oficjalne wpisy WHO i GIS na platformach społecznościowych, policzone wielokrotnie. Po przypisaniu ich do instytucji zostają 2 linki alternatywne w siedmiu latach i dane nie wspierają H2 (test dokładny p = 0,21).

Osiem stron Wikipedii daje zbyt mało powołań na źródła alternatywne, by tę hipotezę rozstrzygnąć. Przyszły test potwierdzający H2 powinien klasyfikować źródło według właściciela konta, a nie domeny, i liczyć każdy link raz (pierwsze dodanie). Trzeba to zapisać w nowej preregistracji, przed zobaczeniem nowych danych.

## Co dalej

1. **Kodowanie stanowiska:** `stance_pilot_*` (zgodność), `stance_gold_*`, import (`make import-stance`). Pełna instrukcja od kodowania do testu potwierdzającego: [`h1a_kroki.md`](h1a_kroki.md).
2. **Strojenie i test `stance_v1`:** `make validate-stance SPLIT=dev STANCE_TUNE=1`, ustawienie `TUNED = True`, commit, `make validate-stance SPLIT=test FROZEN=1`.
3. **Etykiety stanowiska próby i test H1-A:** `make label-h1`, potem `make hypotheses CONFIRMATORY=1`.
4. **Audyt i przegląd domen:** audyt kategorii (`audit_IS/JP.xlsx`, potem `make audit-metrics`: czułość i swoistość `gliner_v1` z audytu i gold, warunek trafności i udziały skorygowane, według poprawki z 25.10.2026 w preregistracji) i ręczny przegląd domen (`domain_review.csv`). Jeśli przegląd zmieni klasyfikację domen alternatywnych, powtarzamy H2 i raportujemy obie wersje.
