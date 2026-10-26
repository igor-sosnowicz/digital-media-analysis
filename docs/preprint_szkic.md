# Szkic preprintu (v1): sekcje, budżet stron, tezy i dowody

Plan 7–8 stron (limit kursu to 8), oparty na wynikach v1, z miejscem na wynik H1-A. Szkielet LaTeX z wstawionymi tabelami i rysunkami jest w [`report/preprint.tex`](../report/preprint.tex). Liczby i makra są w [`podsumowanie_wynikow.md`](podsumowanie_wynikow.md).

**Tekst piszą członkowie zespołu, każdy swoją sekcję według roli.** Kurs sprawdza publikacje detektorem tekstu generowanego (Pangram) i ocenia wkład indywidualnie. Poniżej są tylko tezy do uzasadnienia i dowody, bez gotowych zdań.

## Zasady pisania

- Każda liczba w tekście to makro z `report/numbers.tex`. Po przeliczeniu wyników wystarczy `make preprint-package` i ponowna kompilacja.
- Rozróżniamy analizy preregistrowane od eksploracyjnych, przy każdej analizie.
- Wynik negatywny jest pełnoprawnym wynikiem (zasady kursu, 4.3). Nie łagodzimy go i nie wyolbrzymiamy.
- Korelacja w czasie to nie przyczynowość; piszemy to wprost w dyskusji.
- Ujawnienie użycia AI musi być zgodne z tym, co faktycznie robił asystent (sekcja 7).

## Budżet stron i treść sekcji

| # | Sekcja | Strony | Kto pisze | Rysunki i tabele |
|---|---|---|---|---|
| – | Tytuł, autorzy, streszczenie (do 200 słów), słowa kluczowe | 0,3 | lead badawczy | – |
| 1 | Wprowadzenie | 0,6 | lead badawczy | – |
| 2 | Dane i próba | 0,8 | inżynier danych | Tab. 1 |
| 3 | Pomiar: codebook i gold standard | 0,9 | inżynier pipelinu | Rys. 1 |
| 4 | Walidacja instrumentów AI (źródła i stanowisko) | 1,3 | inżynier pipelinu | Rys. 2, Tab. 2, Tab. 3 (stanowisko) |
| 5 | Wyniki: H1-A, H1-B, H2 | 1,9 | inżynier analityk | Rys. 3 (H1-A i H1-B), Rys. 4, Tab. 4 (H1), Tab. 5 (H2) |
| 6 | Dyskusja i ograniczenia | 0,7 | lead i analityk | – |
| 7 | Odtwarzalność, data statement, użycie AI | 0,3 | inżynier danych i wszyscy | – |
| – | Bibliografia | 0,4 | – | – |
| | **Razem** | **7,2** | | 4 rysunki, 5 tabel |

Rysunki zajmują około 1,8 strony, tabele około 1,4. Jeśli zabraknie miejsca, najpierw usuwamy z Tab. 4 kolumny r/science i r/conspiracy (zostają w tekście jako makra), a Rys. 1 zastępujemy jednym zdaniem z liczbami.

**Liczby H1-A** są w makrach `\resHoneA...`. Do czasu przebiegu potoku H1-A ([`h1a_kroki.md`](h1a_kroki.md)) każde z nich wyświetla kursywą „[czeka na H1-A]”, a panel H1-A na Rys. 3 pokazuje napis zastępczy. Po potoku `make preprint-package` wpisuje wyniki bez zmian w tekście. Stan pokazuje makro `\resHoneAStatus`.

### Streszczenie (0,3 s.)
Tezy:
- pytanie o dwie hipotezy na dwóch platformach;
- dane: dwie losowe próby warstwowe po 500 jednostek i gold standard;
- instrumenty AI zwalidowane na gold z jednym przebiegiem testu;
- odpowiedź: H1 nierozstrzygnięta i niewspierana przez wskaźniki źródeł; H2 formalnie potwierdzona, lecz jako artefakt pomiaru;
- instrument AI działa tylko dla wykrywania powołań na Reddicie.

### 1. Wprowadzenie (0,6 s.)
Tezy:
1. Zjawisko: zaufanie do konsensusu naukowego i sięganie po źródła alternatywne w przestrzeni online.
2. Hipotezy H1 i H2 dokładnie tak, jak w preregistracji (`docs/hipotezy.md`, commit `440b5fb`).
3. Problem metodologiczny: zjawisko trzeba mierzyć automatycznie, więc kluczowe jest, czy instrument AI mierzy to, co opisuje codebook.
4. Wkład:
   - walidacja instrumentów na gold;
   - preregistrowany test;
   - sprawdzenie pomiaru, które zmienia wniosek z H2;
   - plan v2.

Cytowania: literatura o zaufaniu do nauki i dezinformacji, którą trzeba dobrać (lead); Krippendorff 2004.

### 2. Dane i próba (0,8 s.)
Tezy:
1. Źródła i okresy z `config.yaml`:
   - Reddit: 10 subredditów, lata 2005–2020;
   - Wikipedia: 8 stron, od 2020 r. do października 2026 r.
2. Rama Reddita to dni losowane w każdym miesiącu z wagą dnia; mały subreddit wchodzi za rok w całości. Rama Wikipedii to rewizje z opisem zmiany.
3. Losowanie warstwowe po latach (na Wikipedii rok × sygnał), wagi N_h/n_h, podział na pilotaż, `dev` i `test`, ziarno losowania.
4. **Data statement:**
   - regulaminy platform;
   - archiwum Arctic Shift;
   - licencja CC BY-SA Wikipedii;
   - RODO: brak nazw użytkowników w analizie (do sprawdzenia: teksty w `data_samples/`);
   - usunięte posty poza ramą.

Dowody: Tab. 1, `\resRedditFrame`, `\resWikipediaFrame`, liczności z Tab. 1.

### 3. Pomiar: codebook i gold standard (0,9 s.)
Tezy:
1. Konstrukt (funkcja źródła) i jednostki analizy.
2. Trzy zmienne i 9 kategorii. Najważniejsze reguły: R2, R3, R9 i R10, z przykładem z danych.
3. Annotacja w ciemno, instrukcje krok po kroku, podział gold między osoby.
4. Zgodność w pilotażu jest niska:
   - Reddit `cites_source`: paradoks rozpowszechnienia, `\resPilotRedditCitesAlpha` przy `\resPilotRedditCitesAgreement`;
   - typy źródeł: `\resPilotRedditMasiAlpha`;
   - wniosek: potrzebna druga runda, a spory (`\resPilotDisputes`) idą do arbitra.
5. Etykiety JP powstały z etykiet wstępnych AI zatwierdzonych przez JP. Trzeba to ujawnić, bo ma znaczenie dla walidacji instrumentów AI.
6. Udziały z samego gold to pierwsza estymata niezależna od instrumentu, np. `\resGoldShareRedditMedia`.

Dowody: Rys. 1. Cytowania: Krippendorff 2004, Passonneau 2006, Feinstein i Cicchetti 1990.

### 4. Walidacja instrumentów AI (1,2 s.)
Tezy:
1. Trzy zamrożone instrumenty:
   - v1: reguły z EDA;
   - zero-shot NLI;
   - GLiNER.
   
   Wszystkie działają lokalnie, a modele są przypięte do konkretnych wersji.
2. Procedura: strojenie na `dev`, zamrożenie commitem, jeden przebieg testu. Metryki ważone wagami próby, z bootstrapem w warstwach.
3. **Reddit:**
   - GLiNER: `\resTestGlinerRedditCitesF`, czułość `\resTestGlinerRedditCitesRecall`;
   - typy źródeł umiarkowanie: `\resTestGlinerRedditMasi`;
   - McNemar: GLiNER lepszy od zero-shot (`\resMcnemarRedditZeroshotGlinerP`) i od v1;
   - v1 nie czyta linku posta (`\resErrorsVoneUrlShare` błędów).
4. **Wikipedia:** wynik negatywny, najlepszy F1 to `\resTestGlinerWikipediaCitesF`.
5. **Zależność od annotatora:** MASI `\resTestGlinerRedditMasiIS` na części IS i `\resTestGlinerRedditMasiJP` na części JP.
6. **Błąd różnicowy:** brak różnic między okresami, ale przy małej mocy.
7. **Wybór do H1-B:** GLiNER na Reddicie. Reguły v2 i I4 tylko jako wynik z `dev` albo dalsze prace.

8. **Instrument stanowiska (H1-A):** zgodność dwóch osób na `pilot2` (`\resHoneAPilotKappa`, n = `\resHoneAPilotUnits`); strojenie na `dev` (`\resHoneADevPosts` postów, progi `\resHoneAThresholds`); jeden test (`\resHoneATestPosts` postów): F1 `challenges` `\resHoneATestChallengesF`, κ `\resHoneATestKappa`; warunek trafności `\resHoneAGate`.

Dowody: Rys. 2, Tab. 2, Tab. 3 (stanowisko). Cytowania: Laurer i in. 2024, Zaratiana i in. 2024, Cohen 1960, McNemar 1947, Kendall 1938.

### 5. Wyniki: H1 i H2 (1,6 s.)
**H1** (około 1,1 s.):
1. **H1-A (test główny)** na `\resHoneARelevantPosts` postach o nauce:
   - trend `challenges`: `\resHoneAChallengesOr`, p = `\resHoneAChallengesP`; `supports`: `\resHoneASupportsOr`, p = `\resHoneASupportsP`;
   - udział `challenges`: `\resHoneAChallengesShareEarly` w latach 2005–2009 i `\resHoneAChallengesShareLate` w latach 2014–2018;
   - wrażliwości (2005–2020, r/science, r/conspiracy) w Tab. 4.

   Werdykt według wyniku:
   - warunek trafności niespełniony: „H1-A niemierzalne instrumentem `stance_v1`” (wynik negatywny co do pomiaru);
   - warunek spełniony i p < 0,05 w kierunku wzrostu: potwierdzona; w dyskusji: postawy czy skład subredditów;
   - warunek spełniony, bez istotnego wzrostu: wynik negatywny.
2. H1-B na `\resHoneBCiting` postach z powołaniem (GLiNER):
   - źródła konsensusu: `\resHoneBConsensusOr`, p = `\resHoneBConsensusP`;
   - źródła alternatywne: `\resHoneBAlternativeOr`, p = `\resHoneBAlternativeP`.
3. Surowe udziały zmieniają się w kierunku hipotezy, ale to zmiana składu:
   - udział r/conspiracy rośnie z `\resHoneConspiracyShareTwothousandeight` do `\resHoneConspiracyShareTwothousandeighteen`;
   - dekompozycja (eksploracyjna): źródła alternatywne +`\resHoneBAlternativeShiftTotal`, z czego skład to `\resHoneBAlternativeShiftComposition`.
4. Analizy wrażliwości (2005–2020, r/science, r/conspiracy) dają to samo. Wskaźnik konsensusu jest tylko opisowy (brak audytu).

**H2** (około 0,8 s.):
1. Test z preregistracji: `\resHtwoOr`, p = `\resHtwoP`, przy `\resHtwoAlternativeLinks` linkach alternatywnych na `\resHtwoLinks`.
2. Analizy wrażliwości są nieistotne: bez COVID-19 p = `\resHtwoWithoutCovidP`; permutacja p = `\resHtwoPermutationP`.
3. **Sprawdzenie pomiaru:** `\resHtwoOfficialLinks` z 10 linków to oficjalne konta WHO i GIS, a jeden link WHO dodano `\resHtwoWhoRepeats` razy. Według właściciela konta zostają 2 linki, a test dokładny daje p = `\resHtwoExactP`.
4. **Werdykt:** formalne potwierdzenie to artefakt, dane nie wspierają H2, a moc jest niska.

Dowody: Rys. 3, Rys. 4, Tab. 4 (H1), Tab. 5 (H2). Cytowania: Firth 1993.

### 6. Dyskusja i ograniczenia (0,7 s.)
Tezy:
1. Co wiemy, a czego nie:
   - H1: brak dowodu spadku w obrębie społeczności, ale bez testu stanowiska nie wiemy, czy zaufanie się zmienia;
   - H2: 8 stron to za mało, by rozstrzygnąć.
2. Lekcja metodologiczna: kategoria domeny nie odróżnia instytucji od influencera, a rewerty wielokrotnie liczą ten sam link.
3. Ograniczenia:
   - niska zgodność ludzi;
   - etykiety wspomagane przez AI;
   - błędy instrumentu;
   - korelacja a przyczynowość;
   - efekty stałe nie usuwają zmian w obrębie subredditu;
   - 8 stron Wikipedii wybranych tematycznie.
4. Dalsze prace: preregistracja v2 (`docs/hipotezy_v2.md`) z analizą mocy:
   - H1: 0,96 przy 100 jednostkach na komórkę;
   - H2: około 40–50 tys. pierwszych dodań linków.

### 7. Odtwarzalność, data statement i użycie AI (0,3 s.)
Tezy:
1. Repozytorium i commit, polecenia `make` (`pipeline`, `gold-sample`, `validate`, `hypotheses`, `report-tables`, `preprint-package`), preregistracje z commitami.
2. Data statement: odwołanie do sekcji 2 i do opisu danych w repozytorium.
3. **Użycie AI (zgodnie z faktami):**
   - asystent AI (Claude Code) pisał kod i testy;
   - przygotował etykiety wstępne JP, które JP zatwierdził;
   - sklasyfikował listę domen H2;
   - zaproponował przyczyny błędów (niepotwierdzone);
   - przygotował pakiet wyników i szkic struktury;
   - instrumenty w badaniu to lokalne modele otwarte;
   - tekst preprintu napisali autorzy.

## Przed oddaniem

1. `make report-tables` i `make preprint-package`; kompilacja na Overleafie; liczba stron ≤ 7.
2. Kontrola spójności: każda liczba w tekście to makro albo zgadza się z plikiem wyników (mogę ją uruchomić).
3. Lista przewidywanych zarzutów na turniej red teamingu (M2) z odpowiedziami (mogę przygotować).
4. Opcjonalnie przed pisaniem: kodowanie `pilot2` przez IS, decyzje arbitra i jednorazowy test reguł v2 i I4 wzmocnią sekcje 3 i 4.
