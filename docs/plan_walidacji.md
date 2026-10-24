# Plan: codebook, gold standard i walidacja instrumentu

**Cel.** Spełnić wymagania bloku 3 z zasad AMC („Codebook i gold standard; walidacja instrumentu”; rola inżyniera pipelinu) i kryterium preprintu „sprawdzenie wiarygodności instrumentu AI na danych odniesienia”. Każdy etap daje materiał na jeden z czterech slajdów: Codebook, Gold Standard, Walidacja Błędu, Analiza Instrumentów.

**Instrument.** Ekstraktor odniesień do źródeł oparty na wyrażeniach regularnych i słownikach, który do 16.10.2026 był wklejony w `notebooks/Reditt_EDA.ipynb` i `notebooks/Wikipedia_EDA.ipynb`. Od teraz to zamrożony instrument v1 w `src/digital_media_analysis/instruments/rules_v1.py`.

## Stan na 18.10.2026

- **Zrobione:** codebook v2.0 (kategorie i angielskie kody ze slajdu „Codebook”), próba 500 postów z Reddita (lata 2005–2020) i 500 opisów zmian z Wikipedii (lata 2020–2026), możliwie po równo z każdego roku i tylko ze źródeł z `config.yaml` (Reddit 32 pilot / 148 dev / 320 test, Wikipedia 21 / 152 / 327), oba pliki CSV z pełnymi danymi próby, arkusze pilotażu, import etykiet, κ i α z bootstrapem. 90 testów przechodzi.
- **Brak:** etykiet ludzkich (`pilot_A.xlsx` i `pilot_B.xlsx` są puste), modułu walidacji, instrumentów v2 i AI.
- **Ścieżka krytyczna to ręczna annotacja.** Slajdy 2–4 nie będą miały liczb, dopóki ludzie nie zakodują pilotażu i próby głównej. Resztę da się robić równolegle (zob. [Kolejność prac](#kolejność-prac)).

## Diagnoza (przed zmianami)

| # | Problem | Dowód z danych | Slajd |
|---|---|---|---|
| 1 | Dwa niezgodne schematy kategorii, więc platform nie da się porównać | Reddit: 7 kategorii + `link/domena` + `sygnał powołania`; Wikipedia: 6 + 3 pomocnicze, inne nazwy | Codebook |
| 2 | Kategorie to same listy słów, bez definicji, wykluczeń i jednostki analizy | słowniki `REFERENCE_PATTERNS` / `SOURCE_CATEGORIES` | Codebook |
| 3 | Dopasowanie podciągów bez granic słów i bez kontekstu | „gus” w „bogusiem” i „Ferguson”, „znajomy” w „szukamy znajomych”, „mieszkam na wsi”, „lekarz” w opisie wizyty, „badanie” w rekrutacji do ankiety | Walidacja |
| 4 | Reddit: v1 czyta tylko `text`, a każdy link uznaje za źródło | 124 z 275 postów ma w `url` link, którego v1 nie widzi; 13 z 97 linków v1 to zdjęcia i ankiety | Walidacja |
| 5 | Wikipedia: skróty zasad liczone jako źródła, a kategoria brana z całego komentarza | 274 z 485 wzmianek v1 to skróty `WP:…`; część z nich trafia do `media` lub `nauka`, bo w komentarzu padło inne słowo | Walidacja |
| 6 | Wikipedia: znacznik typu edycji liczony jako powołanie | 88 wzmianek „powołanie bez wskazanego źródła” pochodzi ze znacznika „źródła/przypisy” | Codebook, Walidacja |
| 7 | Wikipedia: pominięty sygnał w treści rewizji | 378 rewizji zmienia liczbę `<ref>` w artykule, ale tylko 61 z nich ma znacznik „źródła/przypisy” | Analiza instrumentów |
| 8 | `confidence` to stałe (1,0 / 0,9 / 0,85 / 0,8 / 0,55), a notebook raportuje ich średnią jak metrykę | kod v1 | Walidacja |
| 9 | Brak gold standardu i jakichkolwiek metryk jakości | – | Gold, Walidacja |
| 10 | Tabela kategorii Wikipedii liczy „komentarze” jako unikalne `revision_number` z wszystkich stron, co zaniża wynik | `źródła encyklopedyczne`: 136 w tabeli, 156 po poprawnym liczeniu (strona + rewizja); błąd nadal jest w komórce 25 `Wikipedia_EDA.ipynb` | Walidacja (do naprawy w etapie 3) |
| 11 | Techniczne: po przeniesieniu do `notebooks/` notebooki nie startowały, nazwy stron były zakodowane w URL, regexy zduplikowane, a `ipykernel` niezadeklarowany (`uv sync` go usuwał) | – | naprawione w etapie 0 |

## Etap 0: wspólny kod (zrobione)

- `src/digital_media_analysis/paths.py`: ścieżki projektu niezależne od katalogu roboczego.
- `src/digital_media_analysis/instruments/rules_v1.py`: v1 przeniesiony 1:1. Na pełnych danych daje identyczne ramki co kod z notebooków (sprawdzone `assert_frame_equal`). `tests/test_rules_v1.py` przypina jego zachowanie, łącznie ze znanymi błędami.
- `instruments/labels.py`: zwija wzmianki do etykiet dokumentu w kodach codebooka (format arkusza annotacji). Mapowania v1 na kody codebooka są w `rules_v1.py`.
- `pyproject.toml`: grupa `dev` (ipykernel, nbconvert, pytest) i jawna zależność `pandas`. `Makefile`: `codebook`, `test`, `notebooks`.

## Etap 1: codebook (slajd 1)

Cel: pokazać, że codebook jest rzetelny, a nie tylko spisany.

**Zrobione: v2.0.**

- `codebook/codebook.yaml` to jedno źródło prawdy: konstrukt, jednostki analizy, 3 zmienne (`source_types`, `cites_source` wyliczane z `source_types` i `edit_about_sources`), 9 kategorii ze slajdu „Codebook” z angielskimi kodami (`scientific`, `institutional`, `media`, `personal`, `social_blog`, `encyclopedia`, `other`, `unknown`, `none`) z definicją, kryteriami włączenia i wykluczenia oraz przykładami pozytywnymi i negatywnymi z danych, 13 reguł rozstrzygania, kolumny arkusza annotacji i historia zmian. Walidację (m.in. angielskie kody i obecność `none`) zapewnia `src/digital_media_analysis/codebook.py`.
- v2.0 (18.10.2026) zastąpiło v1.0 z 10 polskimi kodami przed pilotażem, więc żadne etykiety nie wymagają przekodowania. Mapowanie v1.0 → v2.0 jest w `changelog` codebooka.
- `codebook/codebook.md` to instrukcja dla annotatorów generowana przez `make codebook`. Test pilnuje, żeby była aktualna.
- W obu notebookach są sekcje „Codebook v2.0” oraz „Instrument v1 w kategoriach codebooka” (mapowanie, pokrycie kategorii i konflikty v1 z regułami R3, R9 i R10).

**Do zrobienia: pilotaż i v2.1.**

- Pilotaż: dwie osoby kodują niezależnie 53 jednostki (32 z Reddita, 21 z Wikipedii), potem `make import-labels` i `make agreement`. Następnie sesja uzgadniania, codebook v2.1 i wpis w `changelog`.
- Reguła decyzyjna, ustalona przed pilotażem: jeśli α dla `cites_source` < 0,667, robimy drugą rundę pilotażu na świeżych jednostkach spoza próby głównej (Reddit ma ich jeszcze około 62 tys., co najmniej 650 w każdym roku; Wikipedia około 950, ale lata 2023, 2025 i 2026 weszły do próby w całości, więc druga runda ich nie obejmie). Rundę losuje `make pilot-round REDDIT=… WIKIPEDIA=…` (`scripts/02b_add_pilot_round.py`, `gold.draw_pilot_round`): świeże jednostki spoza próby, rozłożone równo na lata, w Wikipedii 1/3 `cue`. Trafiają do manifestu z fazą `pilot` i podziałem `pilot2`, `pilot3`… Runda `pilot2` (30 postów i 30 opisów) jest już wylosowana.
- Notatniki: sekcję „Codebook v2.0” rozszerzyć o „Zmiany v2.0 → v2.1” (z `changelog`) i tabelę α z pilotażu dla każdej zmiennej.
- Na slajd: konstrukt i jednostki; dwa schematy v1 zastąpione jednym codebookiem; dwie reguły graniczne z przykładami (R3: linki do zdjęć i ankiet, R9: skróty `WP:`); co zmienił pilotaż.

## Etap 2: gold standard (slajd 2)

Cel: etykiety referencyjne i pierwsza estymata zjawiska niezależna od instrumentu.

**Zrobione: losowanie i arkusze pilotażu.**

- Każda platforma ma własny okres badania (`study_periods` w `config.yaml`), bo służy innej hipotezie. Reddit, lata 2005–2020: w przestrzeni online maleje zaufanie do konsensusu naukowego. Wikipedia, od 1.01.2020 do 13.10.2026 (2026 to rok niepełny): użytkownicy częściej odwołują się do alternatywnych źródeł wiedzy (blogi, influencerzy, „eksperci niezależni”).
- Źródła danych: wszystkie skrypty pobierają i losują tylko subreddity z `reddit_subreddits` i strony z `wikipedia_pages` w `config.yaml`. Loadery (`gold.load_reddit_frame`, `gold.load_wikipedia_frame`) pomijają dane spoza configu z ostrzeżeniem, a brak pliku strony z configu jest błędem.
- Rama Reddita: `reddit_subreddits` to sześć polskich subredditów (PolskaPolityka, gry, rower, warszawa, lodz, Szczecin) i cztery angielskie: r/reddit.com (tylko 2005 r., jedyne źródło przed subredditami tematycznymi), r/science (od 2006 r.), r/skeptic i r/conspiracy (od 2008 r.). Polskie subreddity mają posty dopiero od 2012 r. (r/PolskaPolityka od 2020 r.), w latach 2012–2019 łącznie 21–112 rocznie. `make reddit-frame` (`scripts/01b_fetch_reddit_frame.py`) pobiera do `data/raw/reddit_frame/` dla każdego subredditu i roku wszystkie posty z jednego losowego dnia każdego miesiąca (ziarno 20261017, te same dni dla wszystkich subredditów). Subreddit, który w wylosowanych dniach roku ma mniej niż 100 postów, jest pobierany za ten rok w całości: wszystkie polskie subreddity, r/science w 2006 r., r/skeptic w latach 2008–2010 i r/conspiracy w 2008 r. Kolumna `day_weight` (dni w miesiącu na wylosowany dzień, 1 przy pobraniu całego roku) skaluje posty do całego miesiąca, a wagi próby ją uwzględniają. Pobrano 75 581 postów; po odrzuceniu usuniętych rama ma 62 636 (od 685 w 2005 r. do 6217 w 2020 r.), co odpowiada szacunkowo od 2,5 tys. postów w 2006 r. do 187 tys. w 2017 r. (`estimated_posts_per_year` w `sample_design.json`). Posty usunięte przez moderację, filtry lub autora nie wchodzą do ramy. EDA nadal analizuje najnowsze posty z `data/raw/reddit/`.
- Rama Wikipedii: rewizje z niepustym opisem zmiany z okresu badania, 1453 opisy (od 53 w 2025 r. do 762 w 2020 r.).
- `src/digital_media_analysis/gold.py` (`make gold-sample`): losowanie ze ziarnem 20261016 w trzech krokach, z osobnym strumieniem losowym dla każdej platformy (zmiana ramy jednej platformy nie przelosowuje drugiej). Każda platforma dostaje 500 jednostek (pilotaż, dev i test razem), rozdzielonych między lata tak równo, jak pozwalają dane, więc oszacowania dla poszczególnych lat mają podobną precyzję. Rok mniejszy od równego udziału wchodzi w całości, a resztę dzielą równo pozostałe lata; jednostki, które nie dzielą się równo, dostają lata z największą ramą (`year_targets`).
  1. Pilotaż. Reddit: 2 posty na rok. Wikipedia: 3 opisy na rok (1 `cue`, 2 `other`). Pilotaż nie wchodzi do ramy próby głównej.
  2. Próba główna: reszta przydziału roku z pozostałych jednostek. Reddit: warstwa = rok. Wikipedia: warstwa = rok × sygnał. Sygnał to cecha powierzchniowa niezależna od instrumentu: `link`, `cue` (słowa o źródłach, przypisach, danych) albo `other`. W każdym roku `link` wchodzi w całości, `cue` do jednej trzeciej próby głównej roku (przy jednej czwartej w ramie), a `other` dopełnia rok (`split_year`).
  3. Podział wewnątrz warstw: 1/3 do `dev`, reszta do `test`. Waga N_h / n_h liczona osobno dla każdego podziału.
- Wynik: Reddit 32 pilot / 148 dev / 320 test, po 31 lub 32 posty na rok. Wikipedia 21 pilot / 152 dev / 327 test: lata 2023, 2025 i 2026 w całości (72, 53 i 59 opisów), pozostałe po 79; w próbie jest wszystkie 10 opisów z linkiem z tego okresu i 12–26 `cue` na rok.
- `annotations/sample_manifest.csv` (w repo) zawiera identyfikatory, rok, warstwy, kolejność i wagi, bez tekstu. `annotations/sample_design.json` zawiera parametry, odcisk danych (liczba jednostek i SHA-256), przydział każdego roku i lata wzięte w całości. Ponowne losowanie wymaga `--force`, żeby nie podmienić próby w trakcie annotacji.
- `src/digital_media_analysis/sample_export.py` (`make sample-csv`, `scripts/06_export_sample_csv.py`): łączy manifest z pełnymi danymi i zapisuje `data_samples/reddit_sample.csv` oraz `data_samples/wikipedia_sample.csv` (w gicie, żeby cały zespół pracował na jednej kopii próby). Każdy plik ma 500 wierszy próby i 30 wierszy rundy `pilot2`, wszystkie kolumny surowych danych i kolumny losowania (`year`, `phase`, `split`, `order`, `stratum`, `signal`, `N_h`, `n_h`, `weight`). Reddit: 12 kolumn z `data/raw/reddit_frame/` (z `day_weight`). Wikipedia: strona, adres strony, numer rewizji, czas, opis zmiany i pełny tekst artykułu po zmianie (`new_content`, mediana około 90 tys. znaków, plik około 51 MB) z długością w `content_chars`. Excel ucina komórki dłuższe niż 32 767 znaków (371 z 500 wierszy), więc plik Wikipedii czytamy w pandas. Jedna rewizja (`Lekarz#152`) ma pusty tekst, bo wyczyściła stronę (wandalizm cofnięty w następnej edycji). Skrypt sprawdza odcisk danych z `sample_design.json` i liczbę wierszy.
- `src/digital_media_analysis/annotation_sheets.py` (`make pilot-sheets ANNOTATORS="JP IS"`): jeden plik XLSX na osobę w `annotations/sheets/` (poza gitem, bo zawiera tekst). Zawiera zakładkę z instrukcją, kodami i kolumnami z codebooka oraz zakładki Reddit i Wikipedia. Arkusz jest ślepy (bez wyników instrumentu) i ma listy 0/1 oraz podpowiedź z kodami kategorii. Annotator wypełnia `source_types` (`none`, gdy nie ma powołania), a nie `cites_source`. `read_workbook` czyta wypełniony plik, wylicza `cites_source` i zgłasza błędy: nieznane kody (także dawne polskie), puste `source_types`, `none` razem z innymi kodami.
- Sekcja „Gold standard: próba do annotacji” w obu notebookach pokazuje liczności na rok, skład subredditów i stron w kolejnych latach, warstwy, wagi i porównanie z populacją (materiał na slajd).
- **Uwaga:** `data/` jest poza gitem, a manifest wskazuje jednostki z lokalnej kopii danych: Wikipedia z 13.10.2026, Reddit (`data/raw/reddit_frame/`) z 18.10.2026. Archiwum Reddita może się zmieniać (usunięcia), więc osoba z inną kopią może nie wygenerować arkuszy ani plików CSV (`attach_units` i `check_snapshot` to wykryją). Inżynier danych powinien udostępnić zespołowi tę kopię danych. Do pracy na samej próbie (bez ponownego eksportu) wystarczą pliki z `data_samples/`.

**Zrobione: import etykiet i liczenie zgodności.**

- `make import-labels` (`src/digital_media_analysis/annotations.py`) czyta `annotations/sheets/<faza>_<osoba>.xlsx` i sprawdza:
  - etykiety: nieznane kody, puste pola, `none` razem z innymi kodami;
  - zgodność z manifestem: brakujące, nadmiarowe i powtórzone jednostki, zła osoba w kolumnie `annotator`.

  Etykiety bez tekstu, z wersją codebooka zapisaną w arkuszu, trafiają do `annotations/labels/<faza>/<osoba>.csv` (w repo). Arkusz z błędami nie jest zapisywany.
- `make agreement` (`src/digital_media_analysis/agreement.py`) liczy:
  - κ Cohena (dla dwóch osób) i α Krippendorffa: nominalną dla zmiennych 0/1 i z odległością MASI dla całego zbioru `source_types`;
  - zgodność per kategoria;
  - 95% przedziały bootstrap (2000 losowań jednostek ze zwracaniem).

  Wynik zapisuje do `annotations/agreement/`: tabelę zgodności, listę niezgodności, podsumowanie osób i wykres α z przedziałami. Implementację α sprawdza przykład referencyjny Krippendorffa (α = 0,743), a κ porównanie ze sklearn.
- Progi oceny (Krippendorff 2004): α ≥ 0,8 oznacza zgodność rzetelną, 0,667–0,8 tylko wstępne wnioski, poniżej 0,667 trzeba poprawić codebook i kodować ponownie. Zmienne i kategorie, które obie osoby razem zaznaczyły w mniej niż 5 jednostkach, są raportowane bez oceny („za mało przypadków”). Doskonała zgodność na 1–2 przypadkach nic nie mówi.
- W obu notebookach sekcja „Zgodność annotatorów w pilotażu” pokazuje te same wyniki, a niezgodności z tekstem z lokalnych danych są materiałem na sesję uzgadniania.
- Sprawdzone end-to-end na symulowanych etykietach poza repo. Prawdziwych etykiet jeszcze nie ma.

**Do zrobienia:**

- Pilotaż i codebook v2.1 (etap 1). W pilotażu większość kategorii będzie miała za mało przypadków, więc pilotaż ocenia głównie `cites_source`, `edit_about_sources` i α MASI dla całego zbioru typów. Zgodność per kategoria rozstrzyga dopiero próba główna.
- Annotacja próby głównej: 947 jednostek (468 z Reddita, 479 z Wikipedii; razem z pilotażem 1000 na osobę) koduje każda z dwóch osób (`scripts/03_export_annotation_sheets.py --phase gold`, czyli dev i test wymieszane). Arbiter rozstrzyga niezgodności.
- **Stan na 23.10.2026: próba główna jest dzielona między osoby.**
  - IS zakodował pilotaż (Reddit 32 z 32, Wikipedia 20 z 21) i pierwsze jednostki gold: Reddit wiersze 2–69 (67 jednostek), Wikipedia wiersze 2–137 (134 jednostki).
  - JP dostał `gold_JP.xlsx` z kolejnymi jednostkami gold: Reddit wiersze 70–159 (90), Wikipedia wiersze 138–297 (160). To eksport `--after annotations/sheets/gold_IS.xlsx --reddit 90 --wikipedia 160`.
  - JP dostał też `pilot_JP.xlsx`: najpierw te same 53 jednostki pilotażu co IS (do zgodności), potem drugą rundę `pilot2` (30 postów z 16 lat, 30 opisów z lat 2020–2022 i 2024, w tym 8 `cue`). Żeby `pilot2` dał zgodność, IS musi zakodować te same jednostki; do tego czasu pilotaż IS importujemy z `--partial`.
  - W gold każda jednostka ma jedną osobę, więc zgodność liczymy tylko na pilotażu, a etykieta gold to etykieta tej osoby. Import idzie z `--partial`.
  - **Etykiety wstępne AI w plikach JP (23.10.2026).** Na prośbę JP oba arkusze JP (`pilot_JP`: 113 jednostek, `gold_JP`: 250) wypełnił model AI (Claude), kodując według codebooka v2.0 bez wglądu w etykiety IS. Każdy wiersz ma w `notes` dopisek „etykieta wstępna AI (Claude) – do weryfikacji”, a przypadki graniczne `uncertain = 1` z uzasadnieniem. JP musi przejrzeć i poprawić każdy wiersz przed importem. W raporcie trzeba to ujawnić: zgodność IS–JP w pilotażu to zgodność IS z etykietami wspomaganymi przez AI, a jeśli JP zostawi etykiety bez zmian, część gold pochodzi od AI i nie nadaje się do oceny instrumentu AI (I3).
  - Wagi z manifestu zakładają zakodowanie całej próby gold. Do metryk trzeba je przeliczyć dla jednostek faktycznie zakodowanych w każdej warstwie.
  - Do poprawienia przez IS przed importem: puste wiersze `pilot_IS` Wikipedia 8 (`COVID-19#137`), `gold_IS` Reddit 37 (`84pt0`), `gold_IS` Wikipedia 89–90 (`COVID-19#425`, `COVID-19#635`: jest `edit_about_sources`, brak `source_types`) oraz kod `blog` zamiast `social_blog` w `gold_IS` Reddit 18 (`8qs04`).
- Brakujący kod: scalenie dwóch annotacji i decyzji arbitra w etykietę ostateczną (`annotations/labels/gold/adjudicated.csv`). Dziś `agreement.disagreements` tylko listuje niezgodności, a `annotations.py` nie ma kroku uzgadniania.
- Notatniki, nowa sekcja „Gold standard: etykiety uzgodnione”:
  - α i κ na próbie głównej. To „sufit ludzki”, do którego porównujemy instrumenty w etapie 4.
  - Ważone (N_h / n_h) udziały jednostek z powołaniem i typów źródeł, z przedziałami. To pierwszy wynik merytoryczny, który nie zależy od żadnego instrumentu.
- Rzadkie kategorie: metryki instrumentów dla kategorii raportujemy tylko przy co najmniej 10 pozytywach w zbiorze testowym (próg dla zgodności ludzi zostaje 5). Resztę oznaczamy „za mało przypadków” albo łączymy.
- Na slajd: schemat losowania (warstwy: rok na Reddicie, rok × sygnał na Wikipedii), liczności na rok, α z przedziałami na tle progów 0,667 i 0,8, 2–3 niezgodności i sposób ich rozstrzygnięcia.

## Etap 3: walidacja błędu (slajd 3)

Cel: ile v1 się myli, dlaczego i czy to zmienia wnioski z EDA.

- Kod (zrobione 24.10.2026): `src/digital_media_analysis/validation.py`, `scripts/07_validate_instruments.py`, `make tune` i `make validate`. Etykieta referencyjna to etykiety gold IS i JP (`annotations.gold_reference`; jednostki z rozbieżnymi etykietami czekałyby na arbitra). Wagi to N_h podzielone przez liczbę jednostek zakodowanych w warstwie i podziale, a przedziały to bootstrap w warstwach. Wyniki są osobno dla platformy, podziału i części IS i JP. Testy na syntetycznych etykietach.
- Metryki: precyzja, czułość i F1 dla `cites_source` i `edit_about_sources`, dla każdej kategorii (jedna przeciw reszcie), Jaccard dla całego zbioru typów, macro-F1, macierz pomyłek.
- **Ważenie wagami próby.** Warstwy `link` i `cue` są nadreprezentowane, więc nieważona precyzja na Wikipedii będzie zawyżona względem populacji. Równy przydział lat nadreprezentuje też lata z małą liczbą jednostek: na Reddicie wczesne lata (w 2006 r. wszystkie posty mają łącznie około 2,5 tys., w 2017 r. około 187 tys.), na Wikipedii wszystkie lata poza 2020. Na Reddicie waga zawiera też `day_weight`. Metryki liczymy z wagami, a bootstrap losuje jednostki w obrębie warstw.
- **v1 oceniamy na dev i test razem**, z wagami przeliczonymi dla połączonej próby. v1 nigdy nie był strojony, więc to uczciwe i daje około dwa razy więcej jednostek, co przydaje się przy błędzie różnicowym. Zbiór testowy pozostaje nietknięty dla v2 i instrumentu AI (etap 4).
- Analiza błędów: każda pomyłka v1 na dev dostaje przyczynę z zamkniętej listy: podciąg, brak kontekstu, link niebędący źródłem, skrót `WP:`, znacznik edycji, wyciek kontekstu komentarza, brak w słowniku, pominięte pole `url`, inne. Zapis w `annotations/errors/v1_dev.csv`, druga osoba sprawdza około 20% przypisań. Wynik pokazujemy na wykresie Pareto.
- Błąd różnicowy: odsetek fałszywych trafień i pominięć per rok, subreddit i strona, z przedziałami. Jeśli się różnią, porównania grup lub trend w czasie są obciążone. Na rok przypada 20 postów testowych z Reddita i 35–52 opisy z Wikipedii, więc wynik raczej pozwoli „nie wykluczyć różnic” niż je wykazać. Lepiej porównywać okresy, np. 2005–2012 i 2013–2020 na Reddicie.
- Kalibracja `confidence`: empiryczna precyzja dokumentu w grupach o stałych wartościach 1,0 / 0,9 / 0,85 / 0,8 / 0,55.
- Propagacja błędu, czyli rozbudowa eksperymentów z EDA. Tabele „na jakie źródła powołują się użytkownicy” (Reddit) i „kategorie źródeł w komentarzach” (Wikipedia) dostają trzy kolumny obok siebie: zliczenie v1 (jak dziś), częstość skorygowaną metodą Rogana–Gladena z przedziałem i estymatę z gold. Przy okazji naprawiamy błąd #10.
- Na slajd: tabela metryk z przedziałami, macierz pomyłek `cites_source`, Pareto przyczyn, błąd różnicowy, porównanie liczb z v1 i skorygowanych.

## Etap 4: analiza instrumentów (slajd 4)

Cel: wybrać instrument do bloku 4 albo uczciwie stwierdzić, że czegoś nie da się zmierzyć automatycznie.

| | Instrument | Co mierzy | Potrzebuje etykiet do budowy? |
|---|---|---|---|
| I1 | v1 jako punkt odniesienia | wszystko | nie |
| I2 | reguły v2 (`rules_v2.py`): granice słów, pole `url`, wykluczenia R2, R3, R8 i R9, R10 jako osobna zmienna `edit_about_sources`, kontekst samej wzmianki zamiast całego komentarza, słownik domen przypisanych do kategorii | wszystko | tak, tylko dev |
| I3 | instrument AI: LLM z promptem generowanym z `codebook.yaml` (żeby nie rozjechał się z codebookiem), przykłady z dev, odpowiedź JSON w kolumnach arkusza annotacji, temperatura 0, zapisana wersja modelu i promptu, odpowiedzi w cache | wszystko | tak, tylko dev |
| I4 | zmiana liczby `<ref>` i `{{Cytuj …}}` między kolejnymi rewizjami | `edit_about_sources` (Wikipedia) | nie |

- **Zrobione 24.10.2026: instrumenty z gotowymi modelami językowymi**, uruchamiane lokalnie (`uv sync --group ml`):
  - `zeroshot_v1`: wielojęzyczny model NLI `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` (MIT), jedna hipoteza na kategorię i jedna na `edit_about_sources`; wynik to prawdopodobieństwo entailment z trzech klas.
  - `gliner_v1`: `urchade/gliner_multi-v2.1` (Apache-2.0) wydobywa wzmianki o źródłach (redakcje, czasopisma, instytucje, serwisy), mapowane na kategorie; link bez rozpoznanego typu to `other` (R7); nie mierzy `edit_about_sources`.
  - Oba czytają jednostkę jak codebook: na Reddicie tytuł, treść i link posta (bez własnych zdjęć, R3), na Wikipedii opis zmiany bez prefiksu sekcji (R9). Modele są przypięte do commitów z Hugging Face.
  - Strojenie tylko na `dev` (225 jednostek: Reddit 78, Wikipedia 147): język hipotez i próg wybrane według średniej ważonego MASI i F1 `cites_source`. Samo MASI premiowało oznaczanie całej Wikipedii jako `none`. Wybór: zero-shot Reddit po angielsku 0,75, Wikipedia po polsku 0,80, `edit_about_sources` 0,15; GLiNER Reddit 0,20, Wikipedia 0,85.
  - **Wyniki na `dev`** (ważone, 95% przedziały bootstrap):

    | | v1 | zero-shot | GLiNER |
    |---|---|---|---|
    | Reddit, F1 `cites_source` | 0,00 | 0,94 [0,90; 0,97] | 0,94 [0,91; 0,98] |
    | Reddit, MASI | 0,07 | 0,43 [0,34; 0,52] | 0,50 [0,39; 0,60] |
    | Reddit, F1 `media` / `social_blog` | 0,00 / 0,00 | 0,49 / 0,61 | 0,71 / 0,80 |
    | Wikipedia, F1 `cites_source` | 0,22 [0,12; 0,35] | 0,31 [0,09; 0,50] | 0,12 [0,06; 0,24] |
    | Wikipedia, F1 `edit_about_sources` | nie mierzy | 0,27 [0,17; 0,37] | nie mierzy |
    | Wikipedia, MASI | 0,77 | 0,66 | 0,88 |

  - Wnioski z `dev`: v1 nie widzi linku posta, więc na Reddicie (442 z 500 postów to linki) nie znajduje prawie nic. Oba modele dobrze wykrywają powołanie na Reddicie, a GLiNER lepiej rozpoznaje typ. Na Wikipedii żaden instrument nie jest dobry: powołań jest mało (23 z 147), a wysokie MASI GLiNER-a wynika głównie z trafnych `none`. Wyniki na Wikipedii zależą od annotatora (GLiNER: F1 `cites_source` 0,00 na części IS i 0,38 na JP), co potwierdza, że etykiety IS i JP różnią się systematycznie. Żadna kategoria Wikipedii nie ma na `dev` co najmniej 10 przypadków, więc macro-F1 jest tam nieokreślone.
  - Test (`make validate SPLIT=test FROZEN=1`) uruchamiamy raz, po zamrożeniu instrumentów commitem; skrypt odmawia, gdy kod instrumentów lub walidacji nie jest zacommitowany.
- Procedura: I2 i I3 zamrażamy commitem **przed** otwarciem zbioru testowego. Test uruchamiamy raz.
- Porównanie na teście: ważone macro-F1 z przedziałem; κ(instrument, gold) na tle κ(człowiek, człowiek); test McNemara I2 vs I3 dla `cites_source`; koszt i czas; powtarzalność I3 (dwa przebiegi i κ między nimi).
- Odporność wniosków: przeliczamy tabele z EDA każdym instrumentem i sprawdzamy, czy ranking kategorii (τ Kendalla) i kierunek różnic między subredditami i stronami się utrzymują.
- Reguła wyboru, zapisana z góry: najprostszy instrument, którego κ z gold nie jest wyraźnie niższe od κ między annotatorami; przy remisie tańszy i deterministyczny. Jeśli dla danej kategorii nie przechodzi żaden instrument, to wynik negatywny, który zasady kursu wprost uznają.
- Na slajd: tabela I1–I4, wykres κ instrumentów na tle pasma zgodności ludzi, odporność rankingu, decyzja, którym instrumentem liczymy pełne dane w bloku 4.

## Kolejność prac

1. **Teraz, równolegle z pilotażem (bez etykiet):** pilotaż (dwie osoby kodują); `validation.py` z testami; poprawka błędu #10; I4; szkielet I3 (prompt z codebooka, cache, parser JSON).
2. **Po pilotażu:** codebook v2.1, potem arkusze próby głównej. Plan analizy (progi, reguła wyboru instrumentu) commitujemy, zanim ktokolwiek zobaczy wyniki na teście. To dobra obrona w turnieju red teamingu (M2).
3. **Po etykietach dev:** analiza błędów v1, budowa I2, przykłady few-shot dla I3.
4. **Po etykietach test:** zamrożenie I2 i I3, jedno uruchomienie na teście, liczby na slajdy 3–4.
5. **Blok 4:** wybrany instrument na pełnych danych, z częstościami skorygowanymi o błąd.

## Mapa slajdów

| Slajd | Co pokazać | Skąd |
|---|---|---|
| Codebook | konstrukt, jednostki, 3 zmienne, 9 kategorii ze slajdu, kluczowe reguły; przed i po (2 schematy → 1); konflikty v1 z regułami: 274 skróty `WP:`, 88 znaczników, 124 niewidziane linki; zmiany v2.0 → v2.1 po pilotażu | `codebook/codebook.md`, sekcje „Codebook v2.0” i „Instrument v1 w kategoriach codebooka” w obu notebookach, etap 1 |
| Gold Standard | schemat losowania, liczności, κ i α z przedziałami, przykłady niezgodności i ich rozstrzygnięcie, ważone udziały z gold | etap 2 |
| Walidacja Błędu | ważone metryki v1 z przedziałami, macierz pomyłek, Pareto przyczyn błędów, błąd różnicowy, liczby z v1 obok skorygowanych | etap 3 |
| Analiza Instrumentów | tabela I1–I4, κ instrumentów na tle κ ludzi, odporność wniosku, wybór instrumentu | etap 4 |

## Decyzje do podjęcia

- Instrument AI: LLM przez API czy model lokalny, np. polski Bielik. Model lokalny nie wysyła danych na zewnątrz, co upraszcza część o RODO. Koszt API do sprawdzenia w aktualnym cenniku. W obu przypadkach użycie AI ujawniamy w preprincie.
- Kto annotuje (dwie osoby i arbiter) i kiedy robimy pilotaż. Arkusze nazywają się dziś `pilot_A` i `pilot_B`, więc trzeba je wyeksportować ponownie z inicjałami (`make pilot-sheets ANNOTATORS="JP IS"`) albo przemianować.
- Skład próby Reddita zmienia się w czasie i to jest główne zagrożenie dla hipotezy o spadku zaufania: w 2005 r. to ogólny r/reddit.com, w latach 2006–2007 tylko r/science, a potem rośnie udział r/conspiracy (5 z 31 postów w 2008 r., 22 z 32 w 2017 r., 21 z 32 w 2020 r.). Spadek zaufania w próbie może więc wynikać po prostu ze wzrostu r/conspiracy. Polskie subreddity dają tylko 11 z 500 postów (od 2013 r., najwięcej r/PolskaPolityka w 2020 r.), bo przed 2020 r. mają po kilkadziesiąt postów rocznie wobec tysięcy w subredditach angielskich. Do decyzji: czy raportujemy trend łącznie z wagami, czy osobno dla każdego subredditu (r/science i r/conspiracy mają posty w latach 2008–2020). Dodatkowo posty są głównie po angielsku, a Wikipedia po polsku, więc codebook i instrument muszą działać w obu językach. Losowania to nie zmienia, bo subreddit jest zapisany przy każdym poście.
