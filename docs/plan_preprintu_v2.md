# Plan nowego preprintu (v2): krok po kroku — wersja 2 (03.11.2026)

**Wersja 2:** plan przebudowany wokół wyników eksperymentów z **02.11.2026**:
- przebiegi źródeł C i D (codebook 2.3, protokół 1.1);
- przebiegi stanowiska S1 i S2;
- analiza mocy z błędem pomiaru;
- bramka mocy.

Wymagany układ:
- **Abstract**;
- **1. Introduction** (z przeglądem literatury);
- **2. Methodology**;
- **3. Experiment and Results**;
- **4. Conclusion**.

Treść pisze zespół. Ten dokument mówi, co napisać, skąd wziąć liczby i w jakiej kolejności pracować. Termin: **06.11.2026** (notatki z zajęć 30.10).

## Stan przygotowania (03.11.2026)

- **`scripts/28_preprint_v2_package.py`** zapisuje 110 makr w `report/numbers_v2.tex`, tabele `v2_sources_runs.tex`, `v2_stance.tex` i `v2_power.tex` oraz rysunki `v2_sources_runs.png`, `v2_stance_confusion.png` i `v2_power.png`.
  - Liczy też przedziały Wilsona i bootstrapowe, etykiety pewne, McNEmara i test Fishera, więc liczby z rozdz. 1 są odtwarzalne.
  - Uruchomienie: `uv run python scripts/28_preprint_v2_package.py`.
- **`report/preprint_v2.tex`** to szkielet:
  - Abstract i sekcje Introduction, Methodology, Experiment and Results, Conclusion;
  - podrozdziały z tego planu jako ramki `\punkty` z faktami i makrami;
  - tabele i rysunki v1 oraz nowe v2, wraz z bibliografią v1.
  - Brakuje rysunku potoku: ramka `\dopisania` w 3.1.
- **`scripts/24_check_preprint.py`** sprawdza nowy plik: `--preprint preprint_v2.tex --numbers numbers.tex numbers_v2.tex`. Dziś zgłasza 25 ramek do zastąpienia tekstem i jedno makro czekające na v2.
- **Ilustracja bramki** (`scripts/27 --plan`) liczy z domyślnymi założeniami: 50 tys. jednostek H1 i 4 tys. linków H2. Testami głównymi zostałyby wtedy H1-S3 i H2-S2.

## 0. W skrócie

1. **Wyniki z 02.11 są rdzeniem sekcji 3.** Preprint pokazuje cztery eksperymenty pomiarowe poprawionego badania (E1–E4) i jeden punkt odniesienia:

   | Eksperyment | Data | Co mierzy | Najważniejszy wynik |
   |---|---|---|---|
   | **S0 (odniesienie): badanie v1** | 24–30.10 | preregistrowane testy H1 i H2, walidacja instrumentów | H1 nierozstrzygnięty (`stance_v1` nie przeszedł warunku trafności); H2 formalnie istotny (OR 1,47, p = 0,006), ale artefakt pomiaru |
   | **E1: anotacja AI źródeł, protokół 1.0** (A, B) | 31.10 | stabilność i zgodność z IS | κ 0,96; na Wikipedii F1 tylko 0,29–0,32 (systematyczna różnica odczytania reguł) |
   | **E2: codebook 2.3 i protokół 1.1** (C, D) | **02.11** | czy luka wynika z reguł codebooka | κ C–D 0,96 [0,92; 0,99]; na Wikipedii F1 0,63–0,66, MASI 0,82–0,84 |
   | **E3: anotacja AI stanowiska** (S1, S2) | **02.11** | stabilność i trafność wobec odniesienia planu C | κ S1–S2 0,94 [0,91; 0,96]; etykiety pewne: czułość 0,81 [0,72; 0,88], swoistość 0,98, F1 0,86 [0,80; 0,92] |
   | **E4: moc z błędem pomiaru i bramka mocy** | **02.11** | ile danych trzeba, żeby H1 i H2 rozstrzygnąć | H1: 55–77 tys. jednostek (TOST 77–107 tys.); H2 według właściciela ≥ 227 tys. linków; słabsze warianty: H1-S3 21,5 tys., H2-S1 4,0 tys. |

2. **Istotność raportujemy tam, gdzie uczciwie jest:**
   - wiarygodność anotatora AI: dolne granice przedziałów κ (0,90–0,92) leżą powyżej progu 0,8 we wszystkich trzech parach przebiegów;
   - błędy stanowiska skupiają się w jednostkach z flagą `uncertain`: dokładny test Fishera, p < 10⁻¹⁸ (eksploracyjnie);
   - preregistrowane testy v1 z werdyktami i testy odporności H2.
3. **Wyniki „ładne”, ale nieistotne albo w próbie, mówimy wprost:**
   - poprawa zgodności z IS po codebooku 2.3 jest **w próbie**: reguły 2.3 wybrano po obejrzeniu sporów A i B z IS na tych samych 253 jednostkach, a McNemar dla trafności `cites_source` na Wikipedii daje p = 0,064 (A→C) i 0,26 (B→D);
   - bramka B2 przechodzi tylko punktowo (czułość 0,81, test „> 0,8” p = 0,44).
4. **Wyników potwierdzających v2 nie ma.** Zmiana 1 nie jest zatwierdzona, a danych v2 nie pobrano. Bramkę mocy pokazujemy na wartościach planistycznych, z podpisem „illustrative”.
5. **Każda liczba z makra.** Wartości w tym planie są orientacyjne. W preprincie liczby wstawia nowy skrypt pakietu (rozdz. 7), a nie ręka.
6. **Ujawnienie AI** w Methodology (anotacja AI jako metoda) i w deklaracji na końcu Conclusion, także pomoc w pisaniu. Teksty szkicowane przez AI mogą zostać oznaczone przez Pangram.

## 1. Wyniki z 02.11 (źródła liczb)

| Wynik | Plik | Wartość orientacyjna (95% CI) |
|---|---|---|
| E2: stabilność C–D, κ `cites_source` / α (MASI) / κ `edit_about_sources` | `annotations/ai_protocol/scores_D.json` (`stability_vs_C`) | 0,96 [0,92; 0,99] / 0,95 [0,91; 0,98] / 0,98 [0,92; 1,00] |
| E2: zgodność z IS, Reddit (F1 `cites_source`; MASI) | `scores_C.json`, `scores_D.json` | C: 0,98 [0,96; 1,00]; 0,66 [0,57; 0,75]. D: 0,98; 0,65 |
| E2: zgodność z IS, Wikipedia (F1; MASI; κ) | j.w. | C: 0,66 [0,50; 0,78]; 0,84 [0,77; 0,89]; 0,57. D: 0,63 [0,47; 0,76]; 0,82; 0,53 |
| E1 dla porównania: Wikipedia F1 / MASI | `scores_A.json`, `scores_B.json` | A: 0,29 [0,10; 0,47] / 0,79. B: 0,32 [0,13; 0,49] / 0,79 |
| E2: zmiana etykiet przez codebook (κ C, D względem A, B) | `scores_C.json`, `scores_D.json` | 0,74–0,79 (`cites_source`), 0,73–0,78 (α) |
| E2: McNemar trafności `cites_source` na Wikipedii (A→C; B→D) | do dodania w skrypcie | 14 poprawionych i 5 zepsutych, p = 0,064; 13 i 7, p = 0,26 |
| E2: pominięte powołania na Wikipedii względem IS (A, B → C, D) | `scores_*.json` | 28, 27 → 14, 14 |
| E2: niezależność błędów K2 | `scores_C.json`, `scores_D.json` | zero-shot i reguły v1: spełnione; GLiNER: niespełnione (Wikipedia, typy ≈ 0,5; Reddit przy kilku błędach) |
| E3: stabilność S1–S2, κ (4 wartości) / κ `challenges` | `scores_S2.json` (`stability_vs_S1`) | 0,94 [0,91; 0,96] / 0,95 |
| E3: S1 / S2: czułość, swoistość, F1, κ | `scores_S1.json`, `scores_S2.json` | S1: 0,76 [0,66; 0,84]; 0,98; 0,83 [0,76; 0,89]; 0,84. S2: 0,82 [0,72; 0,88]; 0,98; 0,86 [0,80; 0,91]; 0,85 |
| E3: etykiety pewne (zgodne w S1 i S2, 417 postów) | do dodania w skrypcie | czułość 0,81 [0,72; 0,88]; swoistość 0,98 [0,96; 0,99]; F1 0,86 [0,80; 0,92]; κ 0,87 [0,83; 0,91] |
| E3: struktura błędów | `disagreements_S1.csv`, `disagreements_S2.csv` | głównie `challenges` → `neutral` (18 i 14 postów; konflikt R14). Błędy S1: 39 ze 127 postów z flagą wobec 4 z 307 bez flagi, Fisher p ≈ 6·10⁻¹⁹ |
| E4: moc i liczebności | `annotations/hypotheses_v2/power_plan.csv`, `power_plan_values.json` | wymagania z punktu 0.1; implikowany DEFF H1 2,8; DEFF H2 2,9 bez rewizji masowych (14 z nimi) |
| E4: bramka na wartościach planistycznych | `annotations/hypotheses_v2/power_gate_plan.json` | przy założonych N testem głównym zostają H1-S3 i H2-S2; przy N H1 80/70 tys. i 6 tys. linków H2: H1-S1 |

**Zastrzeżenia, które muszą trafić do tekstu:**
- **Czym jest poprawa po codebooku 2.3.** Codebook 2.3 przyjął odczytanie IS (decyzja D0.5), więc poprawa zgodności z IS to dowód, że AI stosuje jawne reguły, a nie niezależna walidacja.
- **Odniesienie stanowiska nie jest niezależne.** To preannotacje AI zweryfikowane przez JP oraz reguły R14; sprawdzenia przez człowieka bez podpowiedzi nie było (D0.4).
- **Przebieg agentów.** Agenci dostali od harnessu indeks pamięci, nazwy plików i tytuły commitów. Przebiegi C i D przerwał limit sesji i zostały wznowione tymi samymi instrukcjami.

## 2. Tytuł i Abstract

**Propozycje tytułu:**
- *Reliable but Rule-Bound: Validating AI Annotation of Sources and Stance for Measuring Trust in Science on Reddit and Wikipedia*
- *Can AI Measure Trust in Science Online? Annotation Experiments, Preregistered Tests and Power on Reddit and Wikipedia*

**Abstract (200–250 słów, pisany na końcu):**
1. **Tło i luka (1–2 zdania):** pomiar zaufania do nauki w danych cyfrowych zależy od trafności automatycznych instrumentów.
2. **Cel (1 zdanie):** H1 (Reddit 2005–2018) i H2 (polska Wikipedia 2020–2026) oraz walidacja anotacji AI na danych odniesienia.
3. **Metoda (2 zdania):**
   - preregistrowane testy trendu z TOST;
   - ślepy protokół anotacji AI z dwoma niezależnymi przebiegami, ocenianymi względem etykiet ludzi;
   - moc z błędem pomiaru.
4. **Wyniki (4 zdania, z makr):**
   - κ przebiegów 0,94–0,96 (dolne granice > 0,8);
   - zgodność z IS zależy od reguł (Wikipedia: F1 0,29 → 0,66 po codebooku 2.3, w próbie);
   - stanowisko: czułość 0,81 i swoistość 0,98;
   - H1 nierozstrzygnięty, H2 formalnie istotny, ale artefakt;
   - rozstrzygnięcie wymaga 55–107 tys. jednostek.
5. **Wniosek (1 zdanie):** wąskim gardłem jest pomiar, nie liczebność; preregistrowany v2 z bramką mocy.

## 3. Sekcja 1: Introduction (z przeglądem literatury)

Bez zmian względem wersji 1 planu: 7 akapitów, przegląd literatury w akapitach 1.2–1.5. Dwie zmiany akcentu:
- **1.5:** więcej miejsca dla anotatorów LLM i ich walidacji (Gilardi i in. 2023; Törnberg 2023; Ziems i in. 2024; Pangakis i in. 2023) oraz dla wpływu błędu klasyfikacji na regresję (Fong i Tyler 2021; TeBlunthuis i in. 2024), bo E1–E3 to eksperymenty z anotatorem LLM.
- **1.7 (wkład):**
  - (a) ślepy protokół anotacji AI i jego walidacja na danych odniesienia (E1–E3);
  - (b) preregistrowane testy H1 i H2 (S0);
  - (c) moc z błędem pomiaru i bramka mocy (E4).

| Akapit | Treść | Literatura (sprawdzić przed cytowaniem) |
|---|---|---|
| 1.1 | Problem: czy zaufanie do nauki spada i czy da się to zmierzyć w danych z platform | Gauchat 2012; Krause i in. 2019; Algan i in. 2021 |
| 1.2 | Zaufanie do nauki: polityzacja, stabilność i polaryzacja, pandemia | Gauchat 2012; Krause i in. 2019; Rutjens i in. 2018; Cologna i in. 2025 |
| 1.3 | Źródła alternatywne i dezinformacja | Vosoughi i in. 2018; Lewandowsky i in. 2012 |
| 1.4 | Reddit i Wikipedia jako dane; weryfikowalność i przypisy | Proferes i in. 2021; Ford i in. 2013; Redi i in. 2019; Piccardi i in. 2020; Steinsson 2024 |
| 1.5 | Automatyczna analiza treści, anotatory LLM, błąd klasyfikacji, PPI i DSL | Grimmer i Stewart 2013; Laurer i in. 2024; Zaratiana i in. 2024; prace z akcentu powyżej; Angelopoulos i in. 2023; Egami i in. 2023 |
| 1.6 | Luka: walidacja instrumentu rzadko jest powiązana z mocą testu trendu | – |
| 1.7 | Wkład (a)–(c) i mapa sekcji | – |

## 4. Sekcja 2: Methodology

Podrozdziały 2.1–2.4 i 2.6–2.7 jak w wersji 1. Zmienione albo nowe są 2.5, 2.8 i 2.9:

| Podrozdział | Treść | Źródło |
|---|---|---|
| 2.1 Research design and preregistration | v1 (24.10) i v2 (25.10; Zmiana 1 w projekcie); reguła decyzji z TOST; SESOI 1,25 i 1,5 | `docs/hipotezy*.md` |
| 2.2 Data and sampling | Reddit i Wikipedia, ramy, wagi, liczebności | obecna sekcja 2 |
| 2.3 Measurement: codebook | konstrukt, 9 kodów, R1–R15; wersje 2.2 i 2.3, z dokładnie opisanymi zmianami 2.3: R3 (reklamy), R8 (opinie → `personal`), R9 (interwiki → `encyclopedia`) | `codebook/codebook.md` |
| 2.4 Reference labels | gold standard: IS bez AI; JP z preannotacją AI. Odniesienie stanowiska planu C: 434 posty, 92 `challenges`, 99 wierszy z reguł | obecna sekcja 3 |
| **2.5 Blind AI annotation protocol** | protokół 1.0 i 1.1: zamrożenie sum kontrolnych przed kodowaniem; losowe kody i kolejność (ziarna); pola jak u ludzi; świeży agent na przebieg albo połowę partii; klucz poza repozytorium; zakaz programów nadających etykiety; kontrola zapisów pracy agentów; przerwanie i wznowienie C i D | `docs/protokol_anotacji_ai*.md`, `scripts/26` |
| **2.6 Annotation experiments E1–E3 and their measures** | jednostki i odniesienia każdego eksperymentu; miary: κ i α (MASI) z przedziałem bootstrapowym (2000 losowań), F1, czułość i swoistość z przedziałem Wilsona; McNemar dla par przebiegów; test Fishera dla flagi `uncertain`; K1 (≥ 0,8), K2 (κ błędów < 0,4 przy ≥ 10 błędach), B2 (czułość ≥ 0,8) | `docs/cwiczenie_protokolu_ai.md` |
| 2.7 Instruments and statistical analysis | instrumenty v1, walidacja, modele trendu, TOST, Firth, test dokładny, korekta błędu klasyfikacji | obecne sekcje 4–5 (metody) |
| **2.8 Power with measurement error (E4)** | wzór z czułością, swoistością i DEFF; sprawdzenie symulacją; wartości planistyczne z v1 bez trendów; implikowany DEFF | `power.py`, `scripts/17 --plan` |
| **2.9 Hypothesis ladders and the power gate** | drabiny H1-S1–S3 i H2-S1–S5; reguła wyboru testu głównego bez danych o trendzie; Holm; TOST na skali skorygowanej | `ladders.py`, `scripts/27`, Zmiana 1 |

## 5. Sekcja 3: Experiment and Results (rdzeń: E2–E4)

Każdy podrozdział: pytanie, wynik z przedziałami i testem, jednozdaniowy wniosek, oznaczenie „preregistered” albo „exploratory”.

| Podrozdział | Akapity | Rysunki i tabele |
|---|---|---|
| **3.1 Experimental pipeline** | Etapy: pobieranie → próba → etykiety ludzi i AI → instrumenty → testy → moc i bramka → pakiet wyników. Gdzie są zamrożenia i jeden przebieg. Gdzie wchodzą E1–E4 | **Rys. 1 (nowy):** schemat potoku z miejscami E1–E4 |
| **3.2 Baseline: Study 1 (v1)** | (1) instrumenty v1 na teście: F1 i MASI, McNemar GLiNER a zero-shot; (2) `stance_v1` nie przeszedł warunku: F1 0,33, κ 0,24, czułość 0,21, więc H1-A nie było testowane; (3) H1-B i H2 z werdyktami; (4) odporność H2: Firth według właściciela p = 0,169, test dokładny 0,205, permutacje 0,070 | istniejące tabele testu, H1 i H2; jeden rysunek (H2) |
| **3.3 E1–E2: AI annotation of sources** | (1) stabilność: κ A–B i C–D z przedziałami, obie dolne granice > 0,8; (2) zgodność z IS według platformy: A/B a C/D, F1 i MASI z przedziałami; (3) co zmienił codebook 2.3: pominięte powołania 28 → 14, κ `personal` 0 → 0,51–0,58, κ C/D względem A/B 0,74–0,79; (4) zastrzeżenie, że poprawa jest w próbie, a McNemar daje p = 0,064 i 0,26; (5) AI a instrumenty: MASI AI > GLiNER, K2 tylko dla zero-shot i reguł | **Tab. (nowa):** przebiegi A–D, stabilność i zgodność z IS; **Rys. (nowy):** F1 i MASI z przedziałami dla A–D oraz instrumentów, osobno dla obu platform |
| **3.4 E3: AI annotation of stance** | (1) stabilność S1–S2: κ 0,94 [0,91; 0,96]; (2) trafność wobec planu C: S1, S2 i etykiety pewne, czułość i swoistość z przedziałami Wilsona; (3) bramka B2 spełniona punktowo, test „> 0,8” p = 0,44; (4) struktura błędów: `challenges` → `neutral`, konflikt R14 zgłoszony przez wszystkich agentów; (5) flaga `uncertain` skupia błędy (Fisher, eksploracyjnie) | **Tab. (nowa):** S1, S2 i etykiety pewne; **Rys. (nowy):** macierz pomyłek etykiet pewnych |
| **3.5 E4: power and the power gate** | (1) dlaczego v1 nie rozstrzygnęło: moc v1 0,11–0,43; (2) liczebności przy błędzie instrumentu i DEFF: H1, H1-S1, H1-S3, H2, H2-S1; (3) pomiar a liczebność: ze `stance_v1` moc ≤ 0,49 nawet przy 70 tys.; (4) bramka na wartościach planistycznych: które warianty zostałyby testami głównymi (illustrative) | **Rys. (nowy):** moc a N dla instrumentów (`power_plan.csv`); **Tab. (nowa):** wymagania liczebności według wariantów |
| **3.6 Contradiction analysis** | trzy sprzeczności: (a) H2 formalnie istotny a testy odporności; (b) AI a IS: różnica znika po zmianie reguł, czyli jest sprawą definicji, a nie losowym błędem; (c) wysoka stabilność AI (κ 0,94–0,96) a ograniczona trafność wobec ludzi, bo stabilność to nie trafność | **Tab. (nowa):** sprzeczność, dowód, interpretacja |
| **3.7 Status of the v2 confirmatory study** | co jest gotowe (kod, projekt Zmiany 1), czego brakuje (zatwierdzenie, dane, etykiety, instrument, bramka, jeden przebieg) i co rozstrzygnie każdy werdykt | – |

**Zasady pisania wyników:**
- Każdy wynik: wartość, 95% CI i p tam, gdzie jest test. Werdykt tylko dla testów preregistrowanych.
- „Exploratory” przy McNemarze A→C, teście Fishera, ilustracji bramki i analizie sprzeczności.
- Słowa „improved” przy zgodności z IS używamy tylko z dopiskiem „in-sample (rules chosen on the same units)”.

## 6. Sekcja 4: Conclusion

| Podrozdział | Treść |
|---|---|
| 4.1 Summary | Anotator AI jest stabilny (κ 0,94–0,96) i stosuje jawne reguły. Rozbieżności z ludźmi wynikają głównie z reguł codebooka (E2), a stanowisko ma wysoką swoistość i czułość ok. 0,8 (E3). Testy v1: H1 nierozstrzygnięty, H2 artefakt. Rozstrzygnięcie wymaga pomiaru lepszego niż `stance_v1` i dziesiątek tysięcy jednostek (E4) |
| 4.2 Limitations | Jeden kodujący bez AI; odniesienie stanowiska zależne od AI i brak sprawdzenia przez człowieka; poprawa po 2.3 w próbie; konflikt R14; K2 niespełnione dla GLiNER; kontekst harnessu; przerwane i wznowione przebiegi; wyniki v2 jeszcze nie istnieją |
| 4.3 Future work | Zatwierdzenie Zmiany 1 i przebieg v2 z bramką mocy; doprecyzowanie R14 (codebook 2.4); niezależna walidacja na nowych jednostkach; kodowanie przez człowieka jako najtańsze wzmocnienie trafności |
| 4.4 Reproducibility and use of AI | Repozytorium i komendy (skrypty 17, 26, 27, 28); co jest poza gitem (teksty); rola AI: preannotacje, anotator w E1–E3, pomoc w kodzie i w pisaniu |

## 7. Pakiet wyników: makra, tabele, rysunki

**Krok techniczny przed pisaniem sekcji 3.**
- **Skrypt 26 (`score`)** dopisuje do wyników trzy rzeczy:
  - przedziały Wilsona dla czułości i swoistości;
  - przedziały bootstrapowe F1 i MASI;
  - etykiety pewne S1 ∩ S2, test McNemara dla par przebiegów i test Fishera dla flagi `uncertain`.

  Dziś te liczby są tylko w skrypcie roboczym, a muszą być odtwarzalne.
- **Nowy `scripts/28_preprint_v2_package.py`** (wzorowany na 18) czyta `scores_*.json`, `power_plan.csv` i `power_gate_plan.json` i zapisuje:
  - `report/numbers_v2.tex`;
  - `report/tables/v2_*.tex`;
  - `report/figures/v2_*.png`.

  Wyniki v2, których jeszcze nie ma, dostają `\textit{[awaiting v2 data]}`.

| Makra (propozycja nazw) | Źródło |
|---|---|
| `\resEOneKappa…`, `\resETwoKappaCites`, `\resETwoAlphaMasi`, `\resETwoKappaEdit` (z przedziałami) | `scores_B.json`, `scores_D.json` |
| `\resETwoWikiF1A`…`D`, `\resETwoWikiMasi…`, `\resETwoRedditF1…`, `\resETwoMcnemarAC`, `\resETwoMcnemarBD` | `scores_*.json`, wyniki McNemara |
| `\resEThreeKappa`, `\resEThreeSensitivity…` (S1, S2, pewne), `\resEThreeSpecificity…`, `\resEThreeFOne…`, `\resEThreeBTwoP`, `\resEThreeFisherP` | `scores_S1.json`, `scores_S2.json`, wyniki dodatkowe |
| `\resEFourUnitsHOne…`, `\resEFourUnitsHTwo…`, `\resEFourDeffHOne`, `\resEFourGatePrimary…` | `power_plan.csv`, `power_plan_values.json`, `power_gate_plan.json` |
| makra v1 (bez zmian) | `report/numbers.tex` |

| Rysunek lub tabela | Status |
|---|---|
| Rys. 1: potok (E1–E4 zaznaczone) | do zrobienia (TikZ albo diagram) |
| Tab.: przebiegi A–D | skrypt 28 |
| Rys.: F1 i MASI z przedziałami (A–D i instrumenty) | skrypt 28 |
| Tab.: stanowisko S1, S2, pewne | skrypt 28 |
| Rys.: macierz pomyłek etykiet pewnych | skrypt 28 |
| Rys.: moc a N | skrypt 28 (`power_plan.csv`) |
| Tab.: wymagania liczebności; drabiny; sprzeczności | skrypt 28 |
| Tabele i rysunki v1 (test, H1, H2, odporność) | istniejące (skrypt 18) |

`scripts/24_check_preprint.py` sprawdza nowy plik (dodać parametr ścieżki), a `--zip` tworzy paczkę do Overleafa.

## 8. Kroki i harmonogram do 06.11

| Dzień | Krok | Kto (rola) | Wynik |
|---|---|---|---|
| 03.11 | 1. Decyzja: preprint z wynikami E1–E4 i S0, a v2 jako projekt; wybór tytułu | zespół | decyzja |
| 03.11 | 2. Skrypt 26: przedziały, etykiety pewne, McNemar, Fisher; skrypt 28: makra, tabele i rysunki E1–E4; testy | inżynier pipelinu | `numbers_v2.tex`, tabele, rysunki |
| 03.11 | 3. Szkielet `report/preprint_v2.tex`: Abstract, sekcje 1–4, ramki `\punkty` z tego planu | inżynier pipelinu | plik |
| 04.11 | 4. Methodology 2.1–2.9 (nowe 2.5, 2.6, 2.8, 2.9) | inżynier pipelinu i analityk | sekcja 2 |
| 04.11 | 5. Experiment and Results 3.1–3.7, z zastrzeżeniami z rozdz. 1 | inżynier analityk | sekcja 3 |
| 05.11 | 6. Introduction z przeglądem literatury; sprawdzenie DOI i `\bibitem` | lead badawczy | sekcja 1 i bibliografia |
| 05.11 | 7. Rys. 1 i przegląd wszystkich rysunków i podpisów | inżynier pipelinu | rysunki |
| 06.11 | 8. Conclusion, potem Abstract (liczby z makr) | lead badawczy | sekcja 4 i Abstract |
| 06.11 | 9. Lista kontrolna (rozdz. 9), Overleaf, oddanie | zespół | PDF |

## 9. Lista kontrolna przed oddaniem

- [ ] Abstract i dokładnie cztery sekcje; bibliografia poza sekcjami.
- [ ] Każda liczba z makra; skrypt 24 nie zgłasza braków.
- [ ] Wyniki E1–E4 mają przedziały; testy (McNemar, Fisher, B2) mają p i oznaczenie „exploratory”.
- [ ] Przy poprawie zgodności po codebooku 2.3 jest dopisek „in-sample”; przy B2, że przechodzi tylko punktowo.
- [ ] Odniesienie stanowiska opisane jako zależne od AI; brak sprawdzenia przez człowieka ujawniony.
- [ ] Ilustracja bramki oznaczona; żadnych twierdzeń o wynikach v2.
- [ ] Ujawnienie AI w 2.4, 2.5 i 4.4; tekst szkicowany przez AI przepisany przez zespół albo zadeklarowany (Pangram).
- [ ] Literatura sprawdzona; rysunki i tabele po angielsku; PDF się kompiluje; brak zdublowanych etykiet.

## 10. Ryzyka

| Ryzyko | Co robimy |
|---|---|
| Przedstawienie poprawy po 2.3 jako dowodu trafności | dopisek „in-sample” i McNemar w tekście |
| B2 jako „spełniona” bez zastrzeżenia | czułość z przedziałem i test „> 0,8” |
| Liczby z roboczego skryptu zamiast z pakietu | skrypt 26 lub 28 musi je liczyć; skrypt 24 sprawdza makra |
| Brak czasu | najpierw sekcja 3 i pakiet (dzień 1–2), Introduction i Conclusion później |
| Ilustracja bramki odebrana jako wynik | podpis „illustrative, planning values” i zdanie w tekście |
