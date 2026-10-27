# Preregistracja: hipotezy H1 i H2

*Wersja 1.0, 24.10.2026.* Ten dokument, sekcja `hypotheses` w `config.yaml`, `codebook/domains.yaml` i kod analizy (`src/digital_media_analysis/hypotheses.py`, `src/digital_media_analysis/wikipedia_refs.py`, `scripts/09_test_hypotheses.py`) zatwierdzamy commitem **przed** pierwszym uruchomieniem `scripts/09_test_hypotheses.py --confirmatory`. Skrypt odmawia uruchomienia potwierdzającego, gdy te pliki nie są zacommitowane. Każdą późniejszą zmianę zapisujemy w sekcji „Zmiany przed analizą potwierdzającą” z datą i powodem.

## Co było wiadomo przed analizą

- **Instrumenty** (walidacja na gold, zbiór testowy uruchomiony raz 24.10.2026, commit `33ff729`; `docs/plan_walidacji.md`):
  - na Reddicie GLiNER (`gliner_v1`) wykrywa powołanie z F1 0,96, `media` z F1 0,66, a `social_blog` z F1 0,70;
  - `scientific` i `institutional` mają w gold za mało przypadków, by je ocenić;
  - na Wikipedii żaden instrument nie jest wiarygodny.
- **Przypisy Wikipedii** (rozpoznanie wykonalności przy planowaniu, a potem lista domen do przeglądu z `scripts/08b_export_domain_review.py`):
  - moduł `wikipedia_refs` liczy w latach 2020–2026 1341 dodanych linków z 222 domen;
  - ok. 79% przypada na stronę COVID-19, a liczba linków spada z ok. 740 w 2020 r. do kilkunastu–kilkudziesięciu rocznie w latach 2024–2026;
  - kategorie domen w okresie łącznie: `institutional` 460, `media` 407, `scientific` 278, `other` 166, `encyclopedia` 10, `social_blog` 10 (pscp.tv 6, twitter.com 2, monbiot.com 1, video.google.com 1), niesklasyfikowane archiwa 10;
  - podziału tych liczb na lata nie liczyliśmy.
- **Rama Reddita:** znana jest liczba postów na subreddit i rok w wylosowanych dniach (`data/raw/reddit_frame/fetch_log.json`). Udział r/conspiracy w ramie rośnie od 2008 r.
- **Czego nie liczyliśmy:** przed tym dokumentem nie policzono żadnych rocznych udziałów ani trendów wskaźników H1 i H2.

## H1: w latach 2005–2018 w przestrzeni online maleje zaufanie do konsensusu naukowego

**Dane:**
- **Rama:** posty z ramy Reddita (`make reddit-frame`), bez usuniętych.
- **Subreddity:** z `hypotheses.h1.subreddits` (r/reddit.com, r/science, r/skeptic, r/conspiracy); polskie subreddity nie dotyczą nauki.
- **Okres główny:** 2005–2018.
- **Próba analityczna:** `scripts/08_label_h1_sample.py`, losowanie proste do 150 postów z każdego subredditu i roku 2005–2020, ziarno 20261024. Waga posta to `day_weight` × (posty subredditu i roku w ramie) / (posty wylosowane).

**Wskaźniki:**

| | Wskaźnik | Jednostki | Instrument | Oczekiwany kierunek |
|---|---|---|---|---|
| **H1-A, główny** | udział postów `challenges` | posty dotyczące nauki (`consensus_stance` ≠ `not_applicable`) | `stance_v1` | wzrost |
| H1-A, poboczny | udział postów `supports` | jak wyżej | `stance_v1` | spadek |
| H1-B, poboczny | udział postów powołujących się na `scientific` lub `institutional` | posty z powołaniem | `gliner_v1` | spadek |
| H1-B, poboczny | udział postów powołujących się na `social_blog`, `unknown` lub `personal` | posty z powołaniem | `gliner_v1` | wzrost |

**Warunki trafności (zapisane z góry):**
- **H1-A:** testujemy tylko wtedy, gdy `stance_v1`, strojony na `dev` i uruchomiony raz na `test` (`scripts/07b_validate_stance.py`), osiąga na teście F1 ≥ 0,5 dla `challenges` i κ ≥ 0,4. Inaczej raportujemy, że H1-A nie da się zmierzyć tym instrumentem.
  - Zgodność annotatorów co do stanowiska mierzymy na rundzie `pilot2` (30 postów kodowanych przez obie osoby).
  - Jeśli H1-A nie spełni warunku, testem potwierdzającym H1 staje się wskaźnik źródeł konsensusu z H1-B.
- **H1-B, wskaźnik konsensusu:** przed analizą potwierdzającą przechodzi audyt (`--audit-annotators` w skrypcie 08, do 30 postów z każdej warstwy przewidzianej kategorii). Jeśli czułość + swoistość − 1 ≤ 0,2, wskaźnik raportujemy tylko opisowo.

**Model:**
- ważona regresja logistyczna: wynik ~ rok (od początku okresu) + efekty stałe subredditu;
- wagi przeskalowane do średniej 1;
- błędy standardowe grupowane po wylosowanym dniu;
- miarą efektu jest iloraz szans na rok z 95% przedziałem;
- test jednostronny w oczekiwanym kierunku, α = 0,05.

H1 uznajemy za potwierdzoną, gdy wskaźnik główny ma p < 0,05 w oczekiwanym kierunku. Wskaźniki poboczne raportujemy bez poprawki na wielokrotne testowanie i opisujemy jako poboczne.

**Analizy wrażliwości:**
- tylko r/science (2006–2018);
- tylko r/conspiracy (2008–2018);
- okres 2005–2020;
- dla H1-B roczne udziały skorygowane o błąd instrumentu metodą Rogana–Gladena, z czułością i swoistością z gold (`test`) i audytu.

**Zagrożenia:**
- Efekty stałe usuwają zmianę składu między subredditami, ale nie zmianę populacji w obrębie subredditu.
- Niezróżnicowany błąd pomiaru osłabia trendy, więc test jest raczej zachowawczy.
- Rok 2005 to wyłącznie ogólny r/reddit.com.
- Źródła (H1-B) są tylko pośrednią miarą zaufania.

## H2: w latach 2020–2026 użytkownicy częściej odwołują się do alternatywnych źródeł wiedzy

**Dane:**
- linki dodane do przypisów (`<ref>`) w rewizjach z lat 2020–2026 ośmiu stron z `wikipedia_pages` (`src/digital_media_analysis/wikipedia_refs.py`);
- link liczy się jako dodany, gdy występuje częściej niż w poprzedniej rewizji;
- linki archiwalne rozwijamy do adresu oryginału;
- jednostką analizy jest dodany link.

**Wskaźnik:** udział linków do domen alternatywnych (kategoria `social_blog` w `codebook/domains.yaml`: media społecznościowe, serwisy wideo, blogi i newslettery), z oczekiwanym wzrostem.

**Warunek trafności:** przed analizą potwierdzającą ktoś przegląda ręcznie wszystkie domeny (`scripts/08b_export_domain_review.py`, plik `annotations/hypotheses/domain_review.csv`), a rozbieżności poprawiamy w `codebook/domains.yaml`.

**Model:**
- ważona regresja logistyczna: wynik ~ rok + efekty stałe strony;
- błędy grupowane po rewizji;
- test jednostronny, α = 0,05.

**Analizy wrażliwości:** bez strony COVID-19; bez roku 2020; tylko linki z domen sklasyfikowanych.

**Moc i interpretacja:** przy 10 linkach alternatywnych na ok. 1340 test ma bardzo małą moc. Wynik „brak wykrywalnego wzrostu” z szerokim przedziałem jest pełnoprawnym wynikiem; nie zmieniamy definicji wskaźnika po zobaczeniu danych.

**Wskaźnik opisowy (bez testu):** roczny udział opisów zmian z powołaniem na `social_blog`, `unknown` lub `personal` w ręcznym gold Wikipedii. Instrumenty na Wikipedii są niewiarygodne, więc nie etykietujemy nimi całej ramy.

**Ograniczenia:**
- Kategoria domeny nie rozpoznaje „ekspertów niezależnych” publikujących na zwykłych stronach.
- 2026 to rok niepełny.
- Osiem stron wybranych tematycznie nie reprezentuje całej Wikipedii.

## Kolejność prac

1. Commit tego dokumentu, `config.yaml`, `codebook/domains.yaml` i kodu analizy.
2. Przegląd domen (H2) oraz audyt kategorii H1-B.
3. Kodowanie stanowiska:
   - `pilot2` przez obie osoby, z pomiarem zgodności;
   - posty gold przez obie osoby, każda swoje;
   - import przez `scripts/04b_import_stance_labels.py`.
4. Strojenie `stance_v1` na `dev`, `TUNED = True`, commit, jeden przebieg na `test`.
5. `scripts/08_label_h1_sample.py`, potem `scripts/09_test_hypotheses.py --confirmatory`.

Zmiany w `codebook/domains.yaml` po przeglądzie domen i progi `stance_v1` po strojeniu to przewidziane zmiany przed analizą potwierdzającą. Commitujemy je przed nią i zapisujemy poniżej.

## Zmiany przed analizą potwierdzającą

**24.10.2026, przed pierwszym przebiegiem potwierdzającym.** Na prośbę zespołu przebieg potwierdzający uruchamiamy, zanim ludzie wykonają kodowanie zaplanowane w punktach 2–4 kolejności prac. Skutki, zapisane przed zobaczeniem wyników:

1. **Przegląd domen (H2):** listę domen sklasyfikował asystent AI przygotowujący instrument; nie przejrzał jej człowiek. Wynik H2 jest potwierdzający z tym zastrzeżeniem. Przegląd ręczny (`domain_review.csv`) pozostaje do zrobienia; jeśli zmieni kategorię domen alternatywnych, powtarzamy H2 i raportujemy obie wersje.
2. **Audyt kategorii (H1-B):** nie wykonano, więc warunku trafności nie da się sprawdzić. Zgodnie z regułą traktujemy go jako niespełniony: wskaźnik źródeł konsensusu raportujemy tylko opisowo. Korekta Rogana–Gladena korzysta wyłącznie z gold (`test`), gdzie przypadków `scientific` i `institutional` jest bardzo mało.
3. **H1-A:** brak ludzkich etykiet stanowiska, więc `stance_v1` nie jest nastrojony ani zwalidowany i H1-A czeka. H1 nie ma na razie testu potwierdzającego: zastępczy wskaźnik konsensusu z H1-B wymaga audytu (punkt 2). Oba wskaźniki H1-B raportujemy jako poboczne. Test H1-A wykonamy po kodowaniu stanowiska, bez zmian w tym dokumencie poza strojeniem progów.

**25.10.2026, przed kodowaniem audytu.** Doprecyzowanie, jak liczymy błąd instrumentu w H1-B. Zapisane, zanim ktokolwiek zakodował arkusze `audit_IS.xlsx` i `audit_JP.xlsx`, więc przed zobaczeniem wyników audytu. Kod analizy z preregistracji (`hypotheses.py`, skrypt `09`) się nie zmienia; audyt liczy nowy skrypt `scripts/07c_audit_metrics.py` (`make audit-metrics`), który korzysta z funkcji `error_rates` i `rogan_gladen` z `hypotheses.py`.

1. **Etykieta referencyjna audytu:** zgodna etykieta obu osób, a przy niezgodności decyzja arbitra (`scripts/05b_adjudicate.py --phase audit`). Posty bez rozstrzygnięcia nie wchodzą do obliczeń.
2. **Wagi audytu:** post ma wagę 1 / prawdopodobieństwo włączenia z warstwy przewidzianej kategorii (`h1_audit_sample.csv`), więc czułość i swoistość dotyczą całej próby analitycznej H1.
3. **Wskaźniki:** tak jak w skrypcie `09`, czyli „ma kategorię konsensusu” i „ma kategorię alternatywną” wśród wszystkich audytowanych postów.
4. **Łączenie z gold:** czułość i swoistość liczymy osobno z audytu, z części Reddita zbioru `test` (wagi próby) i łącznie. W wersji łącznej wagi każdego źródła skalujemy tak, by sumowały się do liczby jego postów, więc oba źródła ważą tyle, ile mają postów. Przedziały to bootstrap w warstwach każdego źródła.
5. **Warunek trafności** („czułość + swoistość − 1 ≤ 0,2 oznacza tylko opis”) sprawdzamy na wersji łącznej. Jeśli audyt da mniej niż 10 postów z kategorią konsensusu w etykiecie referencyjnej, raportujemy też wersję z samego audytu i uznajemy warunek za niespełniony.
6. **Korekta Rogana–Gladena** rocznych udziałów H1-B (`audit_corrected_yearly.csv`) używa wersji łącznej; wersję z samego audytu podajemy obok. Przedziały skorygowanych udziałów uwzględniają tylko błąd losowy udziału obserwowanego, nie niepewność czułości i swoistości.

**25.10.2026, sekcja `hypotheses_v2` w `config.yaml`.** Do `config.yaml` doszła sekcja rozszerzonego testu (preregistracja v2, [`hipotezy_v2.md`](hipotezy_v2.md)). Ustawienia v1 (`hypotheses`, `reddit_subreddits`, `wikipedia_pages`) się nie zmieniły, więc wyniki v1 i ich interpretacja zostają takie same. Plik jest na liście preregistracji v1, więc skrypt `09 --confirmatory` odmówi uruchomienia, dopóki zmiana nie zostanie zacommitowana.

**25.10.2026, wykonanie warunku trafności H1-A (bez zmiany planu).** Warunek z tego dokumentu (F1 dla `challenges` ≥ 0,5 i κ ≥ 0,4 na teście) sprawdza teraz skrypt `07b_validate_stance.py` i zapisuje wynik w `annotations/validation/stance_test_run.json`. Skrypt `08_label_h1_sample.py` etykietuje próbę H1 stanowiskiem tylko wtedy, gdy warunek jest spełniony, więc `09` nie policzy H1-A na instrumencie, który go nie przeszedł; kod `09` się nie zmienia. Poprawiony został też odczyt etykiet źródeł (`annotations.load_labels`): pomija pliki stanowiska `stance_*.csv` z tego samego katalogu. Bez tego import stanowiska zmieniłby dane wejściowe korekty Rogana–Gladena w `09`. Wyniki dotychczasowych przebiegów się nie zmieniają.

**26.10.2026, plan B: odniesienie stanowiska budowane automatycznie, z kontrolą ludzi (przed jakąkolwiek etykietą i testem).** Zespół postanowił zautomatyzować generowanie i weryfikację etykiet referencyjnych. Wpis powstaje, zanim ktokolwiek zobaczył wyniki `stance_v1` na danych z etykietami ludzi: 0 z 217 wierszy arkuszy stanowiska jest zweryfikowanych, a progi `stance_v1` są nienastrojone (`TUNED = False`). Wcześniejsze wstępne etykiety asystenta AI z tej samej sesji (`annotations/ai_suggestions/`) nie wchodzą do odniesienia; zostają jako materiał porównawczy. Procedura: [`plan_b_automatyzacja.md`](plan_b_automatyzacja.md). Instrument H1-A się nie zmienia: nadal `stance_v1`.

1. **Dwóch annotatorów LLM, niezależnie.** A1: Claude (`claude-opus-5-5`) przez API, A2: lokalny otwarty model innej rodziny (`Qwen/Qwen2.5-3B-Instruct`). Oba dostają ten sam opis z codebooka (`src/digital_media_analysis/llm_annotation.py`, `system_prompt`), bez przykładów z danych i bez wyników `stance_v1`. Odpowiedź: etykieta, pewność, uzasadnienie. Modele, skróty promptów i surowe odpowiedzi są zapisywane.
2. **Reguły kontrolne** bez modelu (`rule_flags`): R3, R9, R10, R13 dla źródeł.
3. **Przyjęcie automatyczne:** etykieta A1 = A2, obie pewności co najmniej `medium`, brak sprzeciwu reguł, etykieta nie jest rzadka (`challenges` dla stanowiska; `inne` dla przyczyn błędów; `social_blog` i `unknown` dla domen). Pozostałe wiersze trafiają do człowieka, który je sprawdza (`verified = 1`).
4. **Próba kontrolna:** losowe 15% wierszy przyjętych automatycznie (ziarno 20261026) też sprawdza człowiek. Każdy wiersz ma prawdopodobieństwo przeglądu `p_review` (1 dla kolejki, 0,15 dla przyjętych).
5. **Próba wzbogacona (stanowisko).** Posty r/conspiracy z próby analitycznej H1 spoza manifestu gold, w trzech warstwach: temat konsensusu według `topics_v1` (wszystkie posty), termin naukowy (`stance.SCIENCE_TERMS`, 150 postów), reszta (60 postów); ziarno 20261026, `scripts/03e_enriched_stance_sample.py`. Waga posta to 1 / prawdopodobieństwo włączenia. Połowa każdej warstwy to `dev`, połowa `test`. Dobór nie korzysta z `stance_v1` ani z etykiet LLM.
6. **Łączenie z gold:** w każdej części (`dev`, `test`) wagi gold (N_h / zakodowane) i próby wzbogaconej skalujemy tak, by sumowały się do liczby postów danego źródła (jak w audycie, wpis z 25.10.2026, pkt 4).
7. **Strojenie** progów `stance_v1` na wszystkich wierszach `dev` (przyjętych automatycznie i sprawdzonych przez ludzi).
8. **Warunek trafności H1-A** (F1 dla `challenges` ≥ 0,5 i κ ≥ 0,4, jeden przebieg na `test`) rozstrzygamy na wierszach sprawdzonych przez człowieka, z wagą (waga posta) / `p_review`. Ta sama miara na wszystkich wierszach to analiza wrażliwości; jeśli prowadzi do innej decyzji, raportujemy obie.
9. **Zgodność:** zamiast zgodności dwóch osób raportujemy zgodność A1 z A2 (κ Cohena) i odsetek sugestii zachowanych przez ludzi na próbie kontrolnej, z przedziałem bootstrap (`scripts/21_llm_quality.py`).
10. **Zadania Fazy B** (audyt H1-B, przyczyny błędów, przegląd domen) przechodzą tę samą procedurę. Etykieta referencyjna audytu to etykieta przyjęta automatycznie albo decyzja człowieka z kolejki; jedna osoba wystarcza. Przegląd domen H2 nie zastępuje człowieka: każda domena, której kategoria by się zmieniła, trafia do kolejki.
11. Skrypt annotacji (`19`) odmawia uruchomienia, dopóki ten wpis i kod annotacji nie są zacommitowane.

**26.10.2026, plan C zamiast planu B: reguły codebooka i ludzie, bez modeli językowych (przed jakąkolwiek etykietą i testem).** Zespół zrezygnował z annotatorów LLM, bo nie chce korzystać ani z zewnętrznego API, ani z lokalnych modeli językowych. Ten wpis zastępuje punkty 1–4, 9 i 10 wpisu o planie B; punkty 5–8 (próba wzbogacona, łączenie z gold, strojenie, warunek trafności rozstrzygany na wierszach sprawdzonych przez ludzi z wagą / `p_review`) obowiązują dalej. Nadal 0 z 217 wierszy arkuszy stanowiska jest zweryfikowanych, a `stance_v1` jest nienastrojony. Procedura: [`plan_c_reguly.md`](plan_c_reguly.md).

1. **Etykiety z reguł** (`src/digital_media_analysis/rule_annotation.py`) dostaje tylko jednostka, którą reguła codebooka rozstrzyga bez oceny:
   - stanowisko: post spoza r/science i r/skeptic bez terminu naukowego (`stance.SCIENCE_TERMS`) i bez tematu konsensusu (`topics_v1`) → `not_applicable` (R14);
   - źródła na Reddicie: brak słów wprowadzających źródło (`SOURCE_CUES`) oraz sam własny obraz lub film bez treści → `none` (R3), albo sam tytuł bez linku i treści → `none` (R13);
   - opisy zmian w Wikipedii: rewert lub komunikat bota bez słów o źródłach → `none`, `edit_about_sources = 0` (R9); same znaczniki edycji lub sam prefiks sekcji → `none`, z `edit_about_sources = 1` tylko przy znaczniku „źródła/przypisy” (R9, R10);
   - przyczyny błędów: „pominięte pole url” (v1, post z linkiem), „znacznik edycji”, „skrót WP:” w przypadkach jednoznacznych;
   - domeny H2: domena spoza priorytetu przeglądu (mniej niż 5 linków i kategoria inna niż `social_blog`, `unclassified`, `unknown`) zachowuje kategorię.
2. **Wszystko inne kodują ludzie, na ślepo** (bez podpowiedzi), jedna osoba na jednostkę, z `verified = 1`.
3. **Kontrola reguł:** losowe 15% etykiet z reguł (ziarno 20261026) trafia do ludzi na ślepo; `p_review` = 0,15. Precyzję każdej reguły raportujemy z przedziałem bootstrap (`scripts/21_llm_quality.py`).
4. **Zgodność ludzi:** 30 postów pilotażu stanowiska (`pilot2`) kodują obie osoby, bez podpowiedzi i bez reguł; to niezależna miara zgodności dla H1-A.
5. **Ujawnienie:** regułę stanowiska zawęziliśmy do subredditów nienaukowych po porównaniu jej pierwszej wersji z wstępnymi etykietami asystenta AI z tej sesji na postach gold (`dev` i `test`): pierwsza wersja oznaczała jako `not_applicable` także posty z r/science o nauce. Porównanie dotyczyło tylko reguły budowania odniesienia, nie instrumentu `stance_v1`; precyzję reguły mierzy próba kontrolna.
6. Skrypt `22_rule_queue.py` odmawia uruchomienia, dopóki ten wpis i kod reguł nie są zacommitowane. Kod planu B (`llm_annotation.py`, skrypty 19 i 20) zostaje w repozytorium nieużywany.

**27.10.2026, plan C: podpowiedzi AI w wierszach dla ludzi (przed jakąkolwiek weryfikacją i testem).** Na prośbę zespołu wiersze, których nie rozstrzyga reguła (`decided_by = human`), dostają wstępną etykietę asystenta AI (Claude Opus 5.5 w sesji Claude Code, bez osobnego API) do sprawdzenia przez człowieka. Zmienia to punkt 2 wpisu o planie C: kodowanie ludzi **nie jest już ślepe**. Pozostałe punkty obowiązują. Żaden wiersz nie jest jeszcze zweryfikowany, a `stance_v1` jest nienastrojony.

1. **Źródła podpowiedzi** (bez tekstu postów, w `annotations/ai_suggestions/`): etykiety z sesji z 26.10.2026 dla gold stanowiska, audytu, przyczyn błędów i domen oraz nowe etykiety 223 postów próby wzbogaconej (`stance_enriched_claude-opus-5-5.csv`). Wpisuje je skrypt `22b_add_ai_suggestions.py`; reguły i pliki kolejek się nie zmieniają.
2. **Etykieta liczy się dopiero po sprawdzeniu przez człowieka** (`verified = 1`). Podpowiedź zostaje w kolumnie `ai_<zmienna>` obok etykiety ostatecznej, więc raportujemy, ile podpowiedzi ludzie zmienili.
3. **Wiersze kontrolne reguł** też mają podpowiedź AI, nie etykietę reguły. Precyzję reguły liczymy względem etykiety po sprawdzeniu przez człowieka, który nie zna etykiety reguły; jego decyzja może jednak być zakotwiczona w podpowiedzi AI. Opisujemy to jako ograniczenie.
4. **Zgodność ludzi:** pilotaż stanowiska (30 postów, obie osoby) zostaje bez podpowiedzi i bez reguł, więc nadal daje niezależną miarę zgodności.
5. **Warunek trafności H1-A** liczymy jak dotąd na wierszach sprawdzonych przez ludzi. Ich etykiety są etykietami AI zweryfikowanymi przez człowieka; podajemy to w opisie walidacji i w sekcji o użyciu AI.

**27.10.2026, przebieg próbny na etykietach AI (ujawnienie, bez zmiany planu).** Na prośbę zespołu cały potok uruchomiono w osobnej kopii repozytorium (commit `c2cbafe`). Etykiety AI z arkuszy planu C potraktowano tam tak, jakby ludzie je sprawdzili (`verified = 1` wpisane automatycznie, tylko w kopii). Prawdziwy jednorazowy test `stance_v1` nie został użyty, a `stance_v1` w repozytorium jest nadal nienastrojony. Opis i liczby: [`przebieg_probny_2026-10-27.md`](przebieg_probny_2026-10-27.md); pliki wynikowe poza gitem w `data/dryrun_2026-10-27/`.

1. **Co widzieliśmy:**
   - na części testowej (próbnie) `stance_v1` nie spełnił warunku trafności H1-A: F1 dla `challenges` 0,33, κ 0,24;
   - audyt H1-B dał wskaźnikowi konsensusu J = 0,20, czyli tylko opis;
   - H1-B i H2 bez zmian.
2. **Skutek dla prawdziwego przebiegu:** wyniki części testowej (na etykietach AI) są już znane zespołowi. Prawdziwy test po weryfikacji przez ludzi wykonujemy bez zmian w instrumencie, siatce strojenia i progach warunku trafności. Każda zmiana któregoś z nich po tym przebiegu byłaby decyzją podjętą po zobaczeniu wyniku i raportujemy ją wyłącznie jako analizę eksploracyjną.
3. **Poprawki kodu wykryte w przebiegu** (bez wpływu na wyniki liczbowe):
   - `scripts/09_test_hypotheses.py` (plik objęty tą preregistracją) podaje teraz w uwagach, że H1-A nie testowano, gdy `stance_test_run.json` zapisuje niespełniony warunek, zamiast „czeka na etykiety”; obliczenia się nie zmieniają;
   - `scripts/18_preprint_package.py` wpisuje wtedy „nie testowano” w makra i tabelę trendów H1-A;
   - `stance.ai_review` liczy zmiany podpowiedzi tylko w wierszach decydowanych przez ludzi, bez wierszy z reguł.

   Skrypt `09 --confirmatory` odmówi uruchomienia, dopóki te zmiany nie zostaną zacommitowane.

**27.10.2026, weryfikacja przez asystenta AI zamiast ludzi (przed strojeniem i testem).** Na prośbę zespołu wiersze planu C przeznaczone dla ludzi (`decided_by = human`) sprawdził asystent AI, a nie ludzie. Zmienia to punkt 2 wpisu o podpowiedziach AI z 27.10.2026.

1. **Kto i jak sprawdzał:** ten sam asystent AI (Claude Opus 5.5), który przygotował podpowiedzi, przejrzał ponownie wszystkie 876 wierszy: 335 stanowiska, 173 audytu, 268 przyczyn błędów i 102 domeny. Nie zmienił żadnej podpowiedzi. Ta kontrola nie jest niezależna od podpowiedzi i nie zastępuje oceny człowieka.
2. **Oznaczenie:** wiersze dostają `ai_verified = 1` (`scripts/22c_mark_ai_verified.py`). Kolumna `verified` zostaje zarezerwowana dla ludzi, a importy zapisują `verified_by` (`rule`, `ai` albo `human`). Późniejsze sprawdzenie przez człowieka (`verified = 1`) zastępuje ocenę AI bez innych zmian.
3. **Skutki:**
   - odniesienie stanowiska to etykiety reguł i etykiety AI sprawdzone przez AI;
   - „wiersze sprawdzone” w warunku trafności H1-A to wiersze sprawdzone przez AI, z wagą / `p_review` jak dotąd;
   - „precyzja reguł” na próbie kontrolnej mierzy zgodność reguł z oceną AI, nie z oceną ludzi;
   - opisujemy to w preprincie jako główne ograniczenie walidacji.
4. **Pilotaż stanowiska** (zgodność ludzi) nie został zakodowany; brak niezależnej miary zgodności ludzi dla H1-A.
5. **Jednorazowy test `stance_v1` nie został wykonany.** Strojenie na `dev` (zmiana w `instruments/stance_v1.py`) czeka na decyzję zespołu o commicie zamrażającym i teście. Bez zmian zostają instrument, siatka strojenia i progi warunku trafności (wpis o przebiegu próbnym).

**27.10.2026, wariant A wykonany automatycznie: ślepa kontrola AI i porównanie AI z ludźmi (przed losowaniem, kodowaniem, strojeniem zamrażającym i testem).** Zespół poprosił o wykonanie wariantu A („minimum”) automatycznie, skryptami i analizą arkuszy, zamiast kodowania przez ludzi. Kodowania ludzi nie da się wygenerować automatycznie. Dlatego wariant A ma tu trzy części; każda mierzy coś innego i tak ją opisujemy.

1. **Pilotaż stanowiska (zgodność dwóch osób) nie jest wykonany ani zastępowany.** Nie symulujemy dwóch koderów modelem. Puste arkusze pilotażu czekają na ludzi; brak zgodności ludzi dla H1-A zostaje ograniczeniem.
2. **Próby kontrolne** losuje `scripts/25_control_check.py draw` raz, z ziarnem 20261027, przed jakimkolwiek kodowaniem:
   - **stanowisko:** spośród wierszy czterech arkuszy stanowiska przeznaczonych dla ludzi (`decided_by = human`) wszystkie wiersze z etykietą `challenges` w części `test` (warstwa pewna, 42 wiersze) oraz prosta próba losowa pozostałych do łącznie 84 wierszy; waga = N_h / n_h;
   - **audyt:** 30 losowych wierszy arkusza audytu przeznaczonych dla ludzi;
   - **źródła wobec ludzi:** wszystkie 16 postów z Reddita z pilotażu źródeł, którym IS i JP niezależnie nadali identyczne `source_types`, uzupełnione do 30 losowymi postami z Reddita z gold zakodowanymi przez jedną osobę; wszystkie te etykiety powstały przed podpowiedziami AI (commity z 23–25.10.2026).

   Pierwsze losowanie (60 wierszy stanowiska, 30 zgodnych postów pilotażu) okazało się niewykonalne albo niezrównoważone: zgodnych postów jest tylko 16, a 42 z 60 wierszy stanowiska trafiłoby do warstwy pewnej. Zmieniliśmy więc liczebności powyżej i wylosowaliśmy próby ponownie, przed jakimkolwiek kodowaniem. Komunikat błędu pierwszego przebiegu pokazał zbiór etykiet ludzi z pilotażu bez identyfikatorów postów.
3. **Ślepe ponowne kodowanie:** asystent AI (Claude Opus 5.5) koduje te 144 jednostki według codebooka z plików zawierających tylko tekst posta, bez etykiety AI, etykiety reguły i etykiety ludzi, w kolejności losowej. Etykiety trafiają do `annotations/control/ai_blind_claude-opus-5-5.csv`, zanim skrypt porówna je z czymkolwiek (`25_control_check.py score`).
4. **Co mierzymy:**
   - stanowisko i audyt: **stabilność etykiet AI** (ten sam model, drugie kodowanie na ślepo), a nie błąd względem człowieka; κ, odsetek zgodnych etykiet z wagami i przedziałem Wilsona, zachowanie klasy `challenges`;
   - źródła: **błąd AI względem zgodnej oceny dwóch osób** w zadaniu audytu (dokładna zgodność zbioru kategorii, Jaccard, `cites_source`); to jedyne porównanie AI z ludźmi w tym wariancie.
5. **Skutki:** wyniki są opisowe (sekcja walidacji). Nie zmieniają etykiet odniesienia, progów `stance_v1`, siatki strojenia ani warunku trafności H1-A. Wiersze, w których drugie kodowanie się różni, wypisujemy do sprawdzenia przez ludzi. Ta sama próba trafia na ślepo do arkusza `annotations/sheets/control/human_check.xlsx`, a późniejsza decyzja człowieka (`verified = 1`) zastępuje ocenę AI.

**27.10.2026, weryfikacja przez człowieka (przed commitem zamrażającym i testem).** JP oświadczył zespołowi (w sesji Claude Code), że sprawdził wszystkie 878 wierszy planu C przeznaczonych dla ludzi (335 stanowiska, 173 audytu, 268 przyczyn błędów, 102 domeny; wpis o weryfikacji AI podał błędnie sumę 876 przy tych samych składnikach) i że etykiety są poprawne. Na jego prośbę skrypt `22c_mark_ai_verified.py --human JP` wpisał w tych wierszach `verified = 1`; importy zapisują więc `verified_by = human`, a `ai_verified = 1` zostaje jako ślad wcześniejszej kontroli AI.

1. **Niezależność:** JP sprawdzał etykiety z podpowiedzi AI, które już widział, znając wyniki przebiegu próbnego i ślepej kontroli AI. Jego weryfikacja nie jest więc ślepa ani niezależna od AI. Zmienił 0 etykiet.
2. **Zakres:** jedna osoba (JP) sprawdziła także wiersze z arkuszy przypisanych IS. Pilotaż stanowiska (zgodność dwóch osób) nadal nie jest zakodowany.
3. **Bez zmian:** reguły, siatka strojenia, progi warunku trafności H1-A i procedura testu. Strojenie na `dev` powtarzamy na tych samych etykietach przed commitem zamrażającym.

**27.10.2026, zmiany domen po przeglądzie (po pierwszym przebiegu potwierdzającym).** Przegląd domen (102 domeny do sprawdzenia, podpowiedzi AI sprawdzone przez JP; 20 wierszy kontrolnych reguł) zmienił kategorię trzech domen. Przenosimy je do `codebook/domains.yaml`, jak przewiduje ten dokument:

- `archive.is` (9 linków) i `archive.org` (1 link): `unclassified` → `unknown`, bo z domeny archiwum nie widać źródła;
- `rff.org` (1 link): `other` → `institutional` (instytut badawczy Resources for the Future).

Żadna zmiana nie dotyczy `social_blog`, czyli zmiennej H2. Przebieg potwierdzający z commitu `1b17fc0` wykonano jednak przed tą zmianą, więc H2 raportujemy w dwóch wersjach:
- **przed przeglądem:** pliki `confirmatory_*_before_domain_review.*`;
- **po przeglądzie:** pliki `confirmatory_*` z przebiegu po tym commicie.

Wersja po przeglądzie jest główna. Zmiana werdyktu między wersjami oznaczałaby wrażliwość wyniku na klasyfikację domen.

**27.10.2026, sprostowanie wpisu o wariancie A (porównanie AI z ludźmi na źródłach).** Wpis o wariancie A podał, że wszystkie etykiety źródeł w próbie porównawczej powstały przed podpowiedziami AI. To nieprawda dla JP: jego arkusze `pilot_JP` i `gold_JP` wypełnił 23.10.2026 asystent AI, a JP etykiety zatwierdził (`plan_walidacji.md`, etap 2). Próba i ślepe etykiety się nie zmieniają; zmienia się tylko opis wyniku:

- **odniesienie bez pomocy AI** to wyłącznie etykiety IS: 16 postów pilotażu (IS zgodny z JP) i 6 postów gold zakodowanych przez IS; raportujemy je osobno jako porównanie AI z człowiekiem (`sources_is`);
- 16 postów pilotażu wybrano dlatego, że IS zgodził się z etykietą wspomaganą przez AI, więc to łatwiejsze przypadki;
- 8 postów gold JP to porównanie z etykietami wspomaganymi przez AI, nie z niezależnym człowiekiem.
