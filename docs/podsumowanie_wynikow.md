# Podsumowanie wyników do preprintu (v1)

Materiał roboczy dla osób piszących preprint. **To nie jest tekst do wklejenia:** fakty są w punktach, z liczbą, makrem, źródłem i zastrzeżeniem.

- **Liczby:** w tekście preprintu używamy makr z `report/numbers.tex`, np. `\resHtwoOr`. Makra generuje `make preprint-package` (`scripts/18_preprint_package.py`) z plików wyników, więc tekst nadąża za ponownym przeliczeniem.
- **Wartości w tabelach poniżej** to stan z 25.10.2026, po scaleniu z PR #5.
- **Szkic i budżet stron:** [`preprint_szkic.md`](preprint_szkic.md).

## Pytanie i odpowiedź w trzech punktach

1. **H1 (Reddit 2005–2018, spadek zaufania do konsensusu):**
   - test główny (stanowisko, H1-A) się nie odbył, bo brak ludzkich etykiet stanowiska;
   - wskaźniki źródeł (H1-B) nie pokazują trendu w obrębie subredditów;
   - spadek w danych łącznych to zmiana składu próby, czyli rosnący udział r/conspiracy;
   - **werdykt:** nierozstrzygnięta, a dostępne wskaźniki jej nie wspierają.
2. **H2 (Wikipedia 2020–2026, więcej źródeł alternatywnych):**
   - test z preregistracji formalnie potwierdza hipotezę;
   - sprawdzenie pomiaru pokazuje, że to artefakt: 8 z 10 linków to oficjalne konta WHO i GIS, a jeden link przywracano wielokrotnie;
   - **werdykt:** dane nie wspierają H2 i jest za mało zdarzeń, by ją rozstrzygnąć.
3. **Instrument AI:**
   - GLiNER wiarygodnie wykrywa powołania na Reddicie;
   - typ źródła rozpoznaje umiarkowanie;
   - na Wikipedii żaden instrument nie działa (wynik negatywny);
   - zgodność ludzi w pilotażu jest niska, a wyniki instrumentów zależą od annotatora.

## Dane i próba

| Fakt | Makra (wartość) | Źródło |
|---|---|---|
| Rama Reddita: posty z 1 losowego dnia miesiąca, 10 subredditów, 2005–2020 | `\resRedditFrame` (62 636) | `annotations/sample_design.json` |
| Rama Wikipedii: rewizje 8 stron z opisem zmiany, 2020–2026 | `\resWikipediaFrame` (1453) | jw. |
| Próba Reddita: pilotaż / dev / test | `\resRedditPilot`, `\resRedditDev`, `\resRedditTest` (32 / 148 / 320) | `annotations/sample_manifest.csv` |
| Próba Wikipedii: pilotaż / dev / test | `\resWikipediaPilot`, `\resWikipediaDev`, `\resWikipediaTest` (21 / 152 / 327) | jw. |
| Druga runda pilotażu, spoza próby | `\resRedditPilotTwo`, `\resWikipediaPilotTwo` (30 / 30) | jw. |
| Gold zakodowany: Reddit dev / test | `\resRedditCodedDev`, `\resRedditCodedTest` (78 / 78) | `annotations/labels/gold/` |
| Gold zakodowany: Wikipedia dev / test | `\resWikipediaCodedDev`, `\resWikipediaCodedTest` (147 / 147) | jw. |
| Powołania w teście: Reddit / Wikipedia | `\resRedditTestCiting`, `\resWikipediaTestCiting` (68 z 78 / 20 z 147) | jw. |
| Etykiety gold według osoby | `\resGoldLabelsIS`, `\resGoldLabelsJP` (200 / 250) | jw. |

**Zastrzeżenia:**
- Gold jest podzielony między osoby, więc każda jednostka ma jedną etykietę, a zgodność mierzymy tylko na pilotażu.
- Polskie subreddity dają tylko 11 z 500 postów.
- Osiem stron Wikipedii to strony wybrane tematycznie, a nie próba losowa.
- **Data statement:** `data_samples/*.csv` w repozytorium zawierają pełny tekst postów i opisów zmian. Inżynier danych musi to opisać (regulaminy platform, RODO, licencja CC BY-SA Wikipedii).

## Codebook i gold standard

| Fakt | Makra (wartość) | Źródło |
|---|---|---|
| Pilotaż (2 osoby): Reddit, 32 posty | `\resPilotRedditUnits` | `annotations/agreement/pilot_agreement.csv` |
| Pilotaż (2 osoby): Wikipedia, 21 opisów | `\resPilotWikipediaUnits` | jw. |
| Reddit `cites_source`: α ≈ 0 przy 91% zgodności surowej | `\resPilotRedditCitesAlpha`, `\resPilotRedditCitesAgreement` | jw. |
| IS uznał wszystkie posty pilotażu za powołujące się na źródło | `\resPilotRedditISCitingShare` (100%) | `pilot_annotators.csv` |
| Reddit, typy źródeł (MASI) | `\resPilotRedditMasiAlpha` (0,34 [0,11; 0,54]) | `pilot_agreement.csv` |
| Wikipedia `edit_about_sources` | `\resPilotWikipediaEditAlpha` (0,70 [−0,02; 1,00]) | jw. |
| Wikipedia `cites_source` i typy źródeł: za mało przypadków | `\resPilotWikipediaCitesAlpha`, `\resPilotWikipediaMasiAlpha` | jw. |
| Spory czekające na arbitra | `\resPilotDisputes` (20) | `adjudication.disputed` |
| Udziały z samego gold: Reddit, powołanie / media / social_blog | `\resGoldShareRedditCitesSource`, `\resGoldShareRedditMedia`, `\resGoldShareRedditSocialBlog` (0,88 / 0,41 / 0,33) | `annotations/validation/gold_shares.csv` |
| Udziały z samego gold: Wikipedia, powołanie | `\resGoldShareWikipediaCitesSource` (0,13) | jw. |

**Zastrzeżenia:**
- **Paradoks rozpowszechnienia:** przy cesze obecnej niemal zawsze α i κ są bliskie zera mimo wysokiej zgodności surowej. To trzeba wyjaśnić, a nie ukrywać.
- Etykiety JP powstały z etykiet wstępnych asystenta AI, które JP zatwierdził. Trzeba to ujawnić.
- Reguła decyzyjna wymaga drugiej rundy pilotażu, a IS jeszcze nie zakodował `pilot2`.

## Walidacja instrumentów (zbiór testowy, jeden przebieg na commicie `33ff729`)

| Fakt | Makra (wartość) | Źródło |
|---|---|---|
| GLiNER, Reddit: F1 `cites_source` | `\resTestGlinerRedditCitesF` (0,96 [0,92; 0,99]) | `annotations/validation/test_metrics.csv` |
| GLiNER, Reddit: precyzja / czułość | `\resTestGlinerRedditCitesPrecision`, `\resTestGlinerRedditCitesRecall` (0,93 / 1,00) | jw. |
| GLiNER, Reddit: κ `cites_source` (niskie przez rozpowszechnienie) | `\resTestGlinerRedditCitesKappa` (0,54) | jw. |
| GLiNER, Reddit: MASI / macro-F1 | `\resTestGlinerRedditMasi`, `\resTestGlinerRedditMacroF` (0,46 / 0,68) | jw. |
| GLiNER, Reddit: F1 `media` / `social_blog` | `\resTestGlinerRedditMediaF`, `\resTestGlinerRedditSocialBlogF` (0,66 / 0,70) | jw. |
| zero-shot, Reddit: F1 `cites_source` / MASI | `\resTestZeroshotRedditCitesF`, `\resTestZeroshotRedditMasi` | jw. |
| v1, Reddit: F1 `cites_source` (nie czyta linku posta) | `\resTestRulesRedditCitesF` (0,10) | jw. |
| Wikipedia: najlepszy F1 `cites_source` (GLiNER) | `\resTestGlinerWikipediaCitesF` (0,26 [0,06; 0,51]) | jw. |
| Wikipedia: F1 `edit_about_sources` (zero-shot) | `\resTestZeroshotWikipediaEditF` (0,37) | jw. |
| Zależność od annotatora: GLiNER, Reddit, MASI IS / JP | `\resTestGlinerRedditMasiIS`, `\resTestGlinerRedditMasiJP` (0,29 / 0,61) | jw. |
| Zależność od annotatora: GLiNER, Wikipedia, F1 IS / JP | `\resTestGlinerWikipediaCitesFIS`, `\resTestGlinerWikipediaCitesFJP` (0,11 / 0,56) | jw. |
| McNemar, Reddit: zero-shot a GLiNER | `\resMcnemarRedditZeroshotGlinerOnlyFirst`, `...OnlySecond`, `...P` (0 / 7, p = 0,016) | `comparison_mcnemar.csv` |
| McNemar, Reddit: v1 a GLiNER | `\resMcnemarRedditVoneGlinerOnlyFirst`, `...OnlySecond` (6 / 66) | jw. |
| τ Kendalla rankingu kategorii, GLiNER, Reddit | `\resTauGlinerReddit` (0,55, p = 0,061) | `comparison_rankings.csv` |
| Reguły v2 i I4 tylko na `dev`: Reddit MASI 0,60 (GLiNER 0,50), Wikipedia F1 edit 0,80 i 0,57 | `\resDevRulesvtwoRedditMasi`, `\resDevGlinerRedditMasi`, `\resDevRulesvtwoWikipediaEditF`, `\resDevRefsWikipediaEditF` | `dev_metrics.csv` |

**Zastrzeżenia:**
- Na Reddicie 87% postów ma powołanie, więc F1 dla `cites_source` jest wysokie łatwo; dlatego podajemy też κ.
- Reguły v2 i I4 nie przeszły testu, więc w preprincie są tylko jako wynik z `dev` albo jako dalsze prace.
- Żaden instrument nie wskazuje tej samej najczęstszej kategorii co gold. Na Reddicie gold ma `media`, a GLiNER `social_blog`, więc wnioski o rodzaju źródeł zależą od instrumentu.

## Analiza błędów i błąd różnicowy

| Fakt | Makra (wartość) | Źródło |
|---|---|---|
| Błędy v1 na `dev`; najczęstsza przyczyna to pominięte pole `url` | `\resErrorsVoneTotal`, `\resErrorsVoneUrl`, `\resErrorsVoneUrlShare` (127; 71, czyli 56%) | `annotations/errors/dev_pareto.csv` |
| Błędy GLiNER-a i reguł v2 na `dev` | `\resErrorsGlinerTotal`, `\resErrorsRulesvtwoTotal` (88 / 97) | jw. |
| Błąd różnicowy GLiNER-a: okresy / subreddity (fałszywe trafienia) | `\resDifferentialGlinerRedditPeriodFpP`, `\resDifferentialGlinerRedditSubredditFpP` (0,056 / 0,006) | `differential_test.csv` |

**Zastrzeżenia:**
- Przyczyny błędów proponuje heurystyka; nie są jeszcze potwierdzone przez człowieka.
- Wynik dla subredditów opiera się na kilkunastu postach bez powołania.

## H1-B (Reddit, wskaźniki źródeł; GLiNER)

| Fakt | Makra (wartość) | Źródło |
|---|---|---|
| Próba analityczna / posty z powołaniem w latach 2005–2018 | `\resHoneSample`, `\resHoneBCiting` (6240 / 5154) | `annotations/hypotheses/` |
| Źródła konsensusu: OR na rok, p jednostronne | `\resHoneBConsensusOr`, `\resHoneBConsensusP` (1,03 [0,99; 1,06], p = 0,928) | `confirmatory_trends.csv` |
| Źródła alternatywne: OR na rok, p | `\resHoneBAlternativeOr`, `\resHoneBAlternativeP` (0,99 [0,97; 1,01], p = 0,853) | jw. |
| Analizy wrażliwości: 2005–2020, tylko r/science, tylko r/conspiracy | `\resHoneB...TwentyOr`, `...ScienceOr`, `...ConspiracyOr` | jw. |
| Surowy udział źródeł konsensusu: 22% w 2006 r., 10–14% w latach 2016–2018 | `\resHoneBConsensusShareTwothousandsix`, `...LateLow`, `...LateHigh` | `confirmatory_yearly.csv` |
| Surowy udział źródeł alternatywnych: 35% w 2005 r., do 47% | `\resHoneBAlternativeShareTwothousandfive`, `...LateHigh` | jw. |
| Udział r/conspiracy w próbie: 2008 / 2018 | `\resHoneConspiracyShareTwothousandeight`, `...Twothousandeighteen` (2% / 58%) | z próby i etykiet (skrypt 18) |
| **Dekompozycja zmiany (2005–2009 a 2014–2018), konsensus:** łącznie / w obrębie / skład | `\resHoneBConsensusShiftTotal`, `...Within`, `...Composition` (−3,7 / +2,7 / −6,5 pp) | skrypt 18 (eksploracyjnie) |
| **Dekompozycja zmiany, źródła alternatywne:** łącznie / w obrębie / skład | `\resHoneBAlternativeShiftTotal`, `...Within`, `...Composition` (+7,6 / +0,2 / +7,3 pp) | jw. |

**Zastrzeżenia:**
- Wskaźnik konsensusu jest tylko opisowy, bo nie przeszedł audytu (odstępstwo zapisane w preregistracji).
- Dekompozycja nie była preregistrowana i trzeba to napisać.
- Efekty stałe nie wykluczają zmiany populacji w obrębie subredditu.
- To korelacja w czasie, nie przyczynowość.

## H2 (Wikipedia, linki w przypisach)

| Fakt | Makra (wartość) | Źródło |
|---|---|---|
| Linki dodane w latach 2020–2026 / alternatywne / w modelu z efektami stałymi | `\resHtwoLinks`, `\resHtwoAlternativeLinks`, `\resHtwoModelLinks` (1341 / 10 / 1207) | `confirmatory_trends.csv`, skrypt 18 |
| Test z preregistracji | `\resHtwoOr`, `\resHtwoP` (1,47 [1,09; 1,99], p = 0,006) | jw. |
| Bez strony COVID-19 / bez roku 2020 | `\resHtwoWithoutCovidP`, `\resHtwoWithoutTwentytwentyP` (0,105 / 0,138) | jw. |
| Permutacja lat (eksploracyjna) | `\resHtwoPermutationP` (0,070) | `exploratory_h2_permutation.json` |
| Logit Firtha, wszystkie strony | `\resHtwoFirthOr`, `\resHtwoFirthP` | `exploratory_h2_robustness.csv` |
| Linki oficjalnych kont / powtórzenia linku WHO / linki alternatywne według właściciela | `\resHtwoOfficialLinks`, `\resHtwoWhoRepeats`, `\resHtwoByOwnerLinks` (8 / 6 / 2) | skrypt 18, `codebook/owners.yaml` |
| Tylko pierwsze dodania (4 zdarzenia) / według właściciela (Firth) | `\resHtwoFirstOr`, `\resHtwoOwnerOr`, `\resHtwoOwnerP` | `exploratory_h2_robustness.csv` |
| Według właściciela, test dokładny | `\resHtwoExactP` (0,205) | `exploratory_h2_exact_by_owner.json` |

**Zastrzeżenia:**
- Analizy odporności i sprawdzenie pomiaru nie były preregistrowane.
- Listę domen sklasyfikował asystent AI; nie przejrzał jej człowiek (odstępstwo).
- Przy 2 zdarzeniach rozstrzyga test dokładny, a nie asymptotyczny.

## Rysunki i tabele pakietu

| Element | Plik | Przekaz |
|---|---|---|
| Rys. 1 | `report/figures/preprint_agreement.png` | zgodność annotatorów w pilotażu wobec progów Krippendorffa |
| Rys. 2 | `report/figures/preprint_instruments.png` | metryki trzech instrumentów na teście z przedziałami |
| Rys. 3 | `report/figures/preprint_h1.png` | udziały H1-B w latach i skład próby (zmiana składu) |
| Rys. 4 | `report/figures/preprint_h2.png` | wszystkie 10 linków „alternatywnych” według właściciela konta |
| Tab. 1 | `report/tables/preprint_data.tex` | rama, próba, gold, zgodność |
| Tab. 2 | `report/tables/test_metrics.tex` | metryki na teście |
| Tab. 3 | `report/tables/h1b.tex` | trendy H1-B |
| Tab. 4 | `report/tables/preprint_h2.tex` | H2: preregistracja, odporność, sprawdzenie pomiaru |

## Co dalej (do sekcji o ograniczeniach i dalszych pracach)

- Preregistracja v2 ([`hipotezy_v2.md`](hipotezy_v2.md)) odpowiada na każdą słabość v1:
  - stanowisko wobec konkretnego konsensusu;
  - panel autorów;
  - właściciel konta zamiast domeny;
  - pierwsze dodania linków;
  - test równoważności.
- Analiza mocy pokazuje potrzebną skalę danych. H1: moc 0,96 przy 100 jednostkach na komórkę; H2: około 40–50 tys. pierwszych dodań linków.
- Kod jest gotowy, a danych v2 jeszcze nie pobraliśmy.
