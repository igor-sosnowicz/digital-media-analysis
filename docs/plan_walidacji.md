# Plan: codebook, gold standard i walidacja instrumentu

**Cel.** Spełnić wymagania bloku 3 z zasad AMC („Codebook i gold standard; walidacja instrumentu”; rola inżyniera pipelinu) i kryterium preprintu „sprawdzenie wiarygodności instrumentu AI na danych odniesienia”. Każdy etap daje materiał na jeden z czterech slajdów: Codebook, Gold Standard, Walidacja Błędu, Analiza Instrumentów.

**Instrument.** Ekstraktor odniesień do źródeł oparty na wyrażeniach regularnych i słownikach, który do 16.10.2026 był wklejony w `notebooks/Reditt_EDA.ipynb` i `notebooks/Wikipedia_EDA.ipynb`. Od teraz to zamrożony instrument v1 w `src/digital_media_analysis/instruments/rules_v1.py`.

## Stan na 25.10.2026

- **Zrobione:**
  - codebook v2.1, próba gold (Reddit 500, Wikipedia 500, plus runda `pilot2`), pliki CSV próby, arkusze;
  - etykiety: gold IS (200) i JP (250), pilotaż IS (52) i JP (113), zgodność w pilotażu;
  - instrumenty v1, zero-shot i GLiNER zwalidowane i raz przetestowane (commit `33ff729`), reguły v2 i I4 zbudowane i ocenione na `dev`;
  - kod uzgadniania (arbiter), dopisywania jednostek do arkuszy, metryk audytu, analizy błędów, błędu różnicowego i porównania instrumentów;
  - hipotezy H1 i H2: preregistracja, przebieg potwierdzający, odporność H2 (zob. etap 5).
- **Testy:** 189 przechodzi.
- **Czeka na ludzi:** arbiter dla 20 spornych jednostek pilotażu, `pilot2` u IS, kodowanie stanowiska, audyt, przegląd domen, potwierdzenie przyczyn błędów. Szczegóły w [Kolejność prac](#kolejność-prac).

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
| 10 | Tabela kategorii Wikipedii liczy „komentarze” jako unikalne `revision_number` z wszystkich stron, co zaniża wynik | `źródła encyklopedyczne`: 136 w tabeli, 156 po poprawnym liczeniu (strona + rewizja); naprawione 25.10.2026 w komórce 25 `Wikipedia_EDA.ipynb` | Walidacja (naprawione) |
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

  Etykiety bez tekstu, z wersją codebooka zapisaną w arkuszu, trafiają do `annotations/labels/<faza>/<osoba>.csv` (w repo). Wiersze z błędnymi etykietami są pomijane i wypisywane, więc pojedynczy błąd nie zatrzymuje importu. Błędy całego arkusza (nagłówki, jednostki spoza fazy, powtórzenia, brakujące jednostki bez `--partial`, inna osoba w kolumnie `annotator`) zatrzymują import, a arkusz nie jest zapisywany (od scalenia z PR #5, 25.10.2026).
- `make agreement` (`src/digital_media_analysis/agreement.py`) liczy:
  - κ Cohena (dla dwóch osób) i α Krippendorffa: nominalną dla zmiennych 0/1 i z odległością MASI dla całego zbioru `source_types`;
  - zgodność per kategoria;
  - 95% przedziały bootstrap (2000 losowań jednostek ze zwracaniem).

  Wynik zapisuje do `annotations/agreement/`: tabelę zgodności, listę niezgodności, podsumowanie osób i wykres α z przedziałami. Implementację α sprawdza przykład referencyjny Krippendorffa (α = 0,743), a κ porównanie ze sklearn.
- Progi oceny (Krippendorff 2004): α ≥ 0,8 oznacza zgodność rzetelną, 0,667–0,8 tylko wstępne wnioski, poniżej 0,667 trzeba poprawić codebook i kodować ponownie. Zmienne i kategorie, które obie osoby razem zaznaczyły w mniej niż 5 jednostkach, są raportowane bez oceny („za mało przypadków”). Doskonała zgodność na 1–2 przypadkach nic nie mówi.
- W obu notebookach sekcja „Zgodność annotatorów w pilotażu” pokazuje te same wyniki, a niezgodności z tekstem z lokalnych danych są materiałem na sesję uzgadniania.
- Sprawdzone end-to-end na symulowanych etykietach poza repo. Prawdziwych etykiet jeszcze nie ma.

**Wynik pilotażu (25.10.2026, `annotations/agreement/pilot_*`).** Obie osoby kodowały 32 posty i 21 opisów (pierwsza runda):

| | jednostki | zgodność | α [95% CI] | ocena |
|---|---|---|---|---|
| Reddit, `cites_source` | 32 | 0,91 | −0,03 [−0,09; 0,00] | niewystarczające |
| Reddit, `source_types` (MASI) | 32 | 0,50 | 0,34 [0,11; 0,54] | niewystarczające |
| Wikipedia, `cites_source` | 21 | 0,86 | −0,05 [−0,14; 0,00] | za mało przypadków |
| Wikipedia, `edit_about_sources` | 21 | 0,90 | 0,70 [−0,03; 1,00] | tylko wstępne wnioski |

- Na Reddicie IS uznał wszystkie 32 posty za powołujące się na źródło, a JP 29. Przy takim rozpowszechnieniu α i κ są bliskie zera mimo 91% zgodności (paradoks rozpowszechnienia). Zgodności co do samego powołania na tej próbie nie da się więc ocenić.
- Typy źródeł na Reddicie to główny problem: α (MASI) 0,34.
- Na Wikipedii powołanie zaznaczył IS w 3 opisach, a JP w żadnym.
- Etykiety JP powstały z etykiet wstępnych AI, które JP zatwierdził, więc to zgodność IS z etykietami wspomaganymi przez AI.
- Według reguły decyzyjnej (α `cites_source` < 0,667) potrzebna jest druga runda. Runda `pilot2` jest gotowa: JP ją zakodował, a IS potrzebuje dopisania jej do swojego arkusza (`make append-sheets`).

**Do zrobienia:**

- Pilotaż i codebook v2.1 (etap 1). W pilotażu większość kategorii będzie miała za mało przypadków, więc pilotaż ocenia głównie `cites_source`, `edit_about_sources` i α MASI dla całego zbioru typów. Zgodność per kategoria rozstrzyga dopiero próba główna.
- Annotacja próby głównej: 947 jednostek (468 z Reddita, 479 z Wikipedii; razem z pilotażem 1000 na osobę) koduje każda z dwóch osób (`scripts/03_export_annotation_sheets.py --phase gold`, czyli dev i test wymieszane). Arbiter rozstrzyga niezgodności.
- **Stan na 23.10.2026: próba główna jest dzielona między osoby.**
  - IS zakodował pilotaż (Reddit 32 z 32, Wikipedia 20 z 21) i pierwsze jednostki gold: Reddit wiersze 2–69 (67 jednostek), Wikipedia wiersze 2–137 (134 jednostki).
  - JP dostał `gold_JP.xlsx` z kolejnymi jednostkami gold: Reddit wiersze 70–159 (90), Wikipedia wiersze 138–297 (160). To eksport `--after annotations/sheets/gold_IS.xlsx --reddit 90 --wikipedia 160`.
  - JP dostał też `pilot_JP.xlsx`: najpierw te same 53 jednostki pilotażu co IS (do zgodności), potem drugą rundę `pilot2` (30 postów z 16 lat, 30 opisów z lat 2020–2022 i 2024, w tym 8 `cue`). Żeby `pilot2` dał zgodność, IS musi zakodować te same jednostki; do tego czasu pilotaż IS importujemy z `--partial`.
  - W gold każda jednostka ma jedną osobę, więc zgodność liczymy tylko na pilotażu, a etykieta gold to etykieta tej osoby. Import idzie z `--partial`.
  - **Etykiety wstępne AI w plikach JP (23.10.2026).** Na prośbę JP oba arkusze JP (`pilot_JP`: 113 jednostek, `gold_JP`: 250) wypełnił model AI (Claude), kodując według codebooka v2.0 bez wglądu w etykiety IS. Każdy wiersz miał w `notes` dopisek „etykieta wstępna AI (Claude) – do weryfikacji”, a przypadki graniczne `uncertain = 1` z uzasadnieniem. JP przejrzał wszystkie wiersze, zatwierdził etykiety, a dopiski usunięto z arkuszy (23.10.2026). W raporcie trzeba to ujawnić: zgodność IS–JP w pilotażu to zgodność IS z etykietami wspomaganymi przez AI, a jeśli JP zostawi etykiety bez zmian, część gold pochodzi od AI i nie nadaje się do oceny instrumentu AI (I3).
  - Wagi z manifestu zakładają zakodowanie całej próby gold. Do metryk trzeba je przeliczyć dla jednostek faktycznie zakodowanych w każdej warstwie.
  - Do poprawienia przez IS przed importem: puste wiersze `pilot_IS` Wikipedia 8 (`COVID-19#137`), `gold_IS` Reddit 37 (`84pt0`), `gold_IS` Wikipedia 89–90 (`COVID-19#425`, `COVID-19#635`: jest `edit_about_sources`, brak `source_types`) oraz kod `blog` zamiast `social_blog` w `gold_IS` Reddit 18 (`8qs04`).
- **Uzgadnianie (kod zrobiony 25.10.2026):** `src/digital_media_analysis/adjudication.py` i `scripts/05b_adjudicate.py` (`make adjudication-sheet PHASE=… ARBITER=…`, potem `make import-adjudication`).
  - Arkusz arbitra `annotations/sheets/adjudication_<faza>.xlsx` ma sporne jednostki, a obok żółtych kolumn etykiety i notatki obu osób. Arbiter nie koduje w ciemno i może wybrać etykietę inną niż obie.
  - Decyzje trafiają bez tekstu do `annotations/adjudication/<faza>.csv`. `annotations.gold_reference` używa ich dla rozstrzygniętych jednostek, więc walidacja (skrypty 07, 11, 12) korzysta z etykiet ostatecznych. Działa też dla audytu (`--phase audit`).
  - W pilotażu czeka 20 spornych jednostek (16 z Reddita, 4 z Wikipedii); arbitra trzeba jeszcze wyznaczyć.
- **Dopisywanie jednostek do arkusza (25.10.2026):** `make append-sheets PHASE=pilot ANNOTATORS=IS` (`03 --append`) dodaje pod ostatnim wierszem jednostki fazy, których arkusz nie ma, bez ruszania istniejących etykiet. Sprawdzone na kopii `pilot_IS.xlsx`: przybywa 30 postów i 30 opisów `pilot2`, a 52 etykiety zostają bez zmian. Samego `pilot_IS.xlsx` nie zmienialiśmy.
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
- **Analiza błędów (kod zrobiony 25.10.2026):** `src/digital_media_analysis/errors.py`, `scripts/11_error_analysis.py` (`make errors`).
  - Każdy błąd instrumentu na `dev` dostaje przyczynę z zamkniętej listy: podciąg, brak kontekstu, link niebędący źródłem, skrót `WP:`, znacznik edycji, wyciek kontekstu komentarza, brak w słowniku, pominięte pole `url`, inne.
  - Przyczynę proponuje heurystyka z cech powierzchniowych jednostki. Człowiek potwierdza ją albo poprawia w `annotations/sheets/errors_dev.xlsx` (z tekstem), a `make errors IMPORT=1` wczytuje decyzje do `annotations/errors/dev_errors.csv` (bez tekstu). Druga osoba sprawdza około 20% przypisań.
  - Błędy wykrycia (`cites_source`, `edit_about_sources`) liczymy osobno od błędów typu, które liczymy tylko tam, gdzie gold i instrument widzą powołanie. Dzięki temu pominięte powołanie jest jednym błędem, a nie kilkoma.
  - Pareto z przyczyn proponowanych, jeszcze niepotwierdzonych (`annotations/errors/dev_pareto.png`):

    | Instrument | Błędy na `dev` | Najczęstsze przyczyny |
    |---|---|---|
    | v1 | 127 | pominięte pole `url` 71 (56%), brak w słowniku 22, skrót `WP:` 18, znacznik edycji 8 |
    | GLiNER | 88 | brak w słowniku 47, brak kontekstu 40 |
    | reguły v2 | 97 | brak w słowniku 59, brak kontekstu 35 |
    | I4 (`refs_v1`) | 33 | inne: instrument czyta zmianę przypisów w artykule, a codebook deklarację w opisie |

  - Wniosek: ponad połowa błędów v1 to post z linkiem, którego v1 nie czyta (błąd #4). Skróty `WP:` i znaczniki edycji (błędy #5 i #6) są drugą grupą. W regułach v2 te przyczyny prawie znikają.
- **Do zrobienia:** potwierdzenie przyczyn przez człowieka.
- **Błąd różnicowy (zrobione 25.10.2026, `annotations/errors/differential_test.csv`):** odsetek fałszywych trafień (wśród jednostek bez powołania w gold) i pominięć (wśród jednostek z powołaniem) dla połówek okresu (Reddit 2005–2012 i 2013–2020, Wikipedia 2020–2022 i 2023–2026) oraz dla subredditów i stron, na zbiorze testowym. Przedziały to bootstrap w warstwach, a test permutacyjny sprawdza, czy liczby błędów różnią się między grupami.
  - Między połówkami okresu żaden instrument nie ma istotnie różnych błędów `cites_source`. Najbliżej jest GLiNER na Reddicie (fałszywe trafienia, p = 0,056).
  - Między grupami: v1 na Reddicie pomija powołania w różnym stopniu zależnie od subredditu (p = 0,02), a na Wikipedii daje najwięcej fałszywych trafień na stronie Kwas askorbinowy (p = 0,02). GLiNER na Reddicie ma różne odsetki fałszywych trafień w subredditach (p = 0,006), ale zbiór testowy ma tylko kilkanaście postów bez powołania, więc to wynik na pojedynczych przypadkach.
  - Wniosek: test nie wykazuje błędu zależnego od czasu, ale przy tej liczbie jednostek pozwala raczej „nie wykluczyć różnic” niż je wykluczyć. Trend H1-B z efektami stałymi subredditu nie zależy od różnic poziomu błędu między subredditami, ale zależałby od ich zmiany w czasie.
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
  - **Wyniki na zbiorze testowym (24.10.2026).** Test uruchomiony raz (`make validate SPLIT=test FROZEN=1`) na instrumentach zamrożonych commitem `33ff729`; ustawienia i commit są zapisane w `annotations/validation/test_run.json`. Test ma 225 jednostek: Reddit 78 (68 z powołaniem), Wikipedia 147 (20 z powołaniem). Metryki są ważone, z 95% przedziałami bootstrap:

    | | v1 | zero-shot | GLiNER |
    |---|---|---|---|
    | Reddit, F1 `cites_source` | 0,10 [0,00; 0,20] | 0,90 [0,83; 0,95] | 0,96 [0,92; 0,99] |
    | Reddit, κ `cites_source` | −0,02 | 0,15 | 0,54 |
    | Reddit, MASI | 0,18 [0,09; 0,27] | 0,32 [0,22; 0,42] | 0,46 [0,35; 0,57] |
    | Reddit, macro-F1 (`media`, `social_blog`) | 0,08 | 0,42 [0,26; 0,54] | 0,68 [0,43; 0,78] |
    | Reddit, F1 `media` / `social_blog` | 0,00 / 0,16 | 0,34 / 0,49 | 0,66 / 0,70 |
    | Wikipedia, F1 `cites_source` | 0,09 [0,03; 0,19] | 0,17 [0,05; 0,31] | 0,26 [0,06; 0,51] |
    | Wikipedia, F1 `edit_about_sources` | nie mierzy | 0,37 [0,26; 0,48] | nie mierzy |
    | Wikipedia, MASI | 0,70 | 0,61 | 0,85 |

  - Wnioski z testu:
    - **Reddit:** najlepszy jest GLiNER, stabilny między `dev` a `test` (F1 `cites_source` 0,94 → 0,96, MASI 0,50 → 0,46). Znajduje wszystkie powołania (czułość 1,00, precyzja 0,93). Zero-shot wypada na teście gorzej niż na `dev` (MASI 0,43 → 0,32, macro-F1 0,55 → 0,42). κ dla `cites_source` jest umiarkowane mimo wysokiego F1, bo powołanie ma 87% postów. v1 nie widzi linku posta, więc praktycznie nie działa.
    - **Wikipedia:** żaden instrument nie jest wiarygodny. F1 `cites_source` wynosi najwyżej 0,26 przy szerokim przedziale (tylko 20 powołań), a wysokie MASI wynika z trafnych `none`. Zero-shot dla `edit_about_sources` ma F1 0,37: znajduje prawie wszystkie edycje dotyczące przypisów (czułość 0,88), ale z wieloma fałszywymi trafieniami (precyzja 0,24). Według reguły wyboru to wynik negatywny dla typów źródeł na Wikipedii przy tych instrumentach. Kolejny krok to reguły v2 (I2) dla R9 i R10 (skróty `WP:`, znacznik „źródła/przypisy”) albo więcej etykiet gold.
    - **Zależność od annotatora:** instrumenty zgadzają się wyraźnie bardziej z częścią JP. GLiNER na Reddicie ma MASI 0,29 na części IS i 0,61 na JP; na Wikipedii F1 `cites_source` 0,11 na IS i 0,56 na JP. To zgodne z systematycznymi różnicami etykiet IS i JP oraz z tym, że etykiety JP powstały z etykiet wstępnych AI (zob. etap 2). Wyniki trzeba raportować dla obu części, a podwójne zakodowanie części gold pozwoliłoby rozstrzygnąć, które etykiety są bliższe codebookowi.
    - **Propozycja do bloku 4:** GLiNER (`gliner_v1`) na Reddicie dla `cites_source` oraz kategorii `media` i `social_blog`. Na Wikipedii typów źródeł nie liczymy automatycznie, dopóki nie powstanie lepszy instrument.
- **Reguły v2 i I4 (zbudowane 25.10.2026, tylko `dev`):**
  - `rules_v2` (`instruments/rules_v2.py`) wprowadza reguły z codebooka zamiast słów kluczowych v1:
    - całe słowa;
    - link posta i jego domena (`codebook/domains.yaml` i lista częstych domen Reddita, potem wzorce blogów i serwisów informacyjnych, a nieznana domena to `other`, R7);
    - bez skrótów `WP:` i rewertów (R9);
    - znacznik „źródła/przypisy” tylko jako `edit_about_sources` (R10);
    - kategoria z nazwy tuż po sygnale powołania („wg”, „na podstawie”, „according to”), a sam sygnał to `unknown` (R5);
    - bez opinii i próśb o źródło (R8).
  - `refs_v1` (I4, `instruments/refs_v1.py`) daje `edit_about_sources` = 1, gdy rewizja dodała albo usunęła choć jeden przypis (treść `<ref>` lub szablon `{{Cytuj}}`) względem poprzedniej rewizji strony. Próg 1 wybrany na `dev` z siatki 1, 2, 3, 5, 10.
  - Wyniki na `dev`, ważone (reguły budowane na tym zbiorze, więc to górna granica):

    | | v1 | zero-shot | GLiNER | reguły v2 | I4 |
    |---|---|---|---|---|---|
    | Reddit, F1 `cites_source` | 0,00 | 0,94 | 0,94 | 0,95 [0,92; 0,98] | – |
    | Reddit, MASI | 0,07 | 0,43 | 0,50 | 0,60 [0,50; 0,69] | – |
    | Reddit, macro-F1 | 0,00 | 0,55 | 0,76 | 0,74 | – |
    | Wikipedia, F1 `cites_source` | 0,22 | 0,31 | 0,12 | 0,31 [0,10; 0,59] | – |
    | Wikipedia, F1 `edit_about_sources` | – | 0,27 | – | 0,80 | 0,57 |
    | Wikipedia, MASI | 0,77 | 0,66 | 0,88 | 0,89 | – |

  - Reguły v2 dają na Reddicie lepsze MASI niż GLiNER, bo domena linku dobrze wyznacza typ źródła. Na Wikipedii wyraźnie lepiej mierzą `edit_about_sources` niż zero-shot. I4 ma czułość 0,82 przy precyzji 0,44: wiele edycji zmienia przypisy bez słowa w opisie, a codebook mierzy deklarację.
  - Oba instrumenty czekają na commit zamrażający i jeden przebieg testu: `make validate SPLIT=test FROZEN=1 INSTRUMENTS="rules_v2 refs_v1"`. Skrypt 07 nie pozwala drugi raz uruchomić testu dla instrumentu, który już go przeszedł, a dopisuje nowe wiersze do istniejących tabel.
- Procedura: I2 i I3 zamrażamy commitem **przed** otwarciem zbioru testowego. Test uruchamiamy raz.
- **Porównanie na teście (zrobione 25.10.2026, `make compare`, pliki `annotations/validation/comparison_*.csv`)** z zapisanych predykcji, bez ponownego uruchamiania testu:
  - **κ dla `cites_source`:** GLiNER 0,54 [0,20; 0,82] na Reddicie i 0,27 [0,12; 0,45] na Wikipedii, zero-shot 0,15 i −0,01, v1 około 0. κ annotatorów w pilotażu wynosi 0,00 na obu platformach, ale przy 91% i 85% zgodności (paradoks rozpowszechnienia). Ten próg nie jest więc dobrym punktem odniesienia. Dla `edit_about_sources`: annotatorzy 0,69, zero-shot 0,13.
  - **McNemar dla `cites_source`:** na Reddicie GLiNER ma rację tam, gdzie zero-shot się myli, w 7 jednostkach, a odwrotnie w żadnej (p = 0,016); wobec v1 66 do 6 (p < 0,001). Na Wikipedii GLiNER wobec zero-shot 39 do 5, wobec v1 31 do 5 (oba p < 0,001).
  - **Ranking kategorii (τ Kendalla względem gold, ważone udziały na teście):** Reddit GLiNER 0,55 (p = 0,06), zero-shot 0,22, v1 −0,09; Wikipedia GLiNER 0,18, v1 0,12, zero-shot −0,54. Żaden instrument nie wskazuje tej samej najczęstszej kategorii co gold. Na Reddicie gold ma `media` (0,36), a GLiNER `social_blog` (0,46). Wniosek o tym, na co powołują się użytkownicy, zależy więc od instrumentu.
  - **Udziały z samego gold** (`annotations/validation/gold_shares.csv`, `dev` i `test` razem, ważone): Reddit: powołanie 0,88 [0,81; 0,93], `media` 0,41 [0,33; 0,49], `social_blog` 0,33 [0,25; 0,41], pozostałe kategorie po 0,05 lub mniej. Wikipedia: powołanie 0,13 [0,09; 0,19], najczęściej `personal` 0,05, `encyclopedia` 0,03, `institutional` 0,02.
  - Reguły v2 i I4 dojdą do tych tabel po swoim jednorazowym teście.
- Koszt, czas i powtarzalność: modele lokalne są deterministyczne (te same wyniki z cache), więc powtarzalność jest pełna; instrumentu LLM przez API (I3) nie budowaliśmy.
- Reguła wyboru, zapisana z góry: najprostszy instrument, którego κ z gold nie jest wyraźnie niższe od κ między annotatorami; przy remisie tańszy i deterministyczny. Jeśli dla danej kategorii nie przechodzi żaden instrument, to wynik negatywny, który zasady kursu wprost uznają.
- Na slajd: tabela I1–I4, wykres κ instrumentów na tle pasma zgodności ludzi, odporność rankingu, decyzja, którym instrumentem liczymy pełne dane w bloku 4.

## Etap 5: weryfikacja hipotez (blok 4)

Preregistracja: [`docs/hipotezy.md`](hipotezy.md); ustawienia w sekcji `hypotheses` w `config.yaml`. Stan na 24.10.2026:

- **Gotowe (kod i testy):**
  - codebook v2.1 ze zmienną `consensus_stance` (R14) i przebiegiem stanowiska (`stance.py`, skrypty `03b` i `04b`);
  - instrument `stance_v1` (zero-shot NLI, jeszcze niestrojony) i jego walidacja (`07b`);
  - próba analityczna H1 z etykietami (`08`);
  - przypisy Wikipedii ze słownikiem domen (`wikipedia_refs.py`, `codebook/domains.yaml`, lista do przeglądu `08b`);
  - analiza (`hypotheses.py`, skrypt `09`): ważona regresja logistyczna z efektami stałymi i jawnie liczonymi błędami grupowanymi, sprawdzonymi względem `statsmodels`.
- **Arkusze dla ludzi:**
  - `stance_pilot_IS/JP.xlsx`: 30 postów `pilot2`, obie osoby, do zgodności;
  - `stance_gold_IS.xlsx` (67 postów) i `stance_gold_JP.xlsx` (90 postów): posty, które każda osoba kodowała już w gold;
  - `audit_IS/JP.xlsx`: audyt rzadkich kategorii z próby H1;
  - `annotations/hypotheses/domain_review.csv`: przegląd 222 domen.
- **Czeka:**
  - commit preregistracji;
  - kodowanie stanowiska i audyt;
  - strojenie `stance_v1` na `dev` i jednorazowy test;
  - uruchomienie potwierdzające `make hypotheses CONFIRMATORY=1`.

  Wyników hipotez jeszcze nie liczyliśmy.
- **Przebieg potwierdzający 24.10.2026** (preregistracja `440b5fb`; odstępstwa: brak przeglądu domen przez człowieka, brak audytu, H1-A odłożone). Szczegóły w [`docs/wyniki_hipotez.md`](wyniki_hipotez.md).
  - **H1-A:** czeka na etykiety stanowiska.
  - **H1-B:** brak trendu w obrębie subredditów (źródła konsensusu OR 1,03 na rok, p = 0,93; źródła alternatywne OR 0,99, p = 0,85). Surowe zmiany udziałów wynikają ze zmiany składu (rosnący r/conspiracy).
  - **H2:** test główny OR 1,47 na rok [1,09; 1,99], p = 0,006, ale tylko 10 linków alternatywnych. Eksploracyjne sprawdzenie pomiaru (`scripts/10_h2_robustness.py`) pokazało, że 8 z nich to oficjalne wpisy WHO (Periscope) i GIS (Twitter) policzone wielokrotnie. Po przypisaniu ich do instytucji zostają 2 linki alternatywne (test dokładny p = 0,21). Formalne potwierdzenie jest artefaktem klasyfikacji po domenie i dane nie wspierają H2.

## Etap 6: rozszerzony test hipotez (v2)

Test v1 nie rozstrzygnął żadnej hipotezy (zob. etap 5). Druga preregistracja, [`docs/hipotezy_v2.md`](hipotezy_v2.md), jest projektem do zatwierdzenia przez zespół. Stan na 25.10.2026:

- **Kod gotowy, z testami na danych syntetycznych i przebiegiem całego potoku 14 → 15 → 16 na danych sztucznych:**
  - ramy (`h1_frame.py`, `wikipedia_frame.py`, `wikipedia_history.py`) i skrypty pobierające `00b`, `00c`, `01c`;
  - instrumenty `topics_v1`, `stance_v2`, `distrust_v1`, klasyfikacja właścicieli kont (`owners.py`) i lista „perennial sources” (`rsp.py`);
  - modele (`inference.py`): TOST, logit z błędami grupowanymi, korekta błędu pomiaru w funkcji wiarygodności, logit warunkowy po autorze, ujemny dwumianowy, różnica w różnicach, przerwany szereg czasowy, przetrwanie, dekompozycja;
  - krzywa specyfikacji (`multiverse.py`), moc (`power.py`), zgodność z GSS (`external.py`), wykresy (`charts.py`), codebook 2.2 ze zmienną `consensus_topic` (R15).
- **Moc:** H1 przy udziale bazowym 0,15 i 100 jednostkach na komórkę ma 0,96 mocy wykrycia SESOI i 0,95 mocy wykazania braku trendu. H2 potrzebuje około 40–50 tys. pierwszych dodań linków (`annotations/hypotheses_v2/power_*.csv`).
- **Czeka:**
  - zatwierdzenie i commit preregistracji v2;
  - pobranie danych (zgoda zespołu);
  - kodowanie walidacji H1 i właścicieli kont H2;
  - strojenie i jednorazowa ocena `stance_v2`;
  - przebieg potwierdzający.

## Kolejność prac

Stan na 25.10.2026.

1. **Zrobione bez nowych etykiet:** walidacja trzech instrumentów z jednym testem, reguły v2 i I4 na `dev`, analiza błędów z proponowanymi przyczynami, błąd różnicowy, porównanie instrumentów, udziały z gold, kod uzgadniania, dopisywania arkuszy i audytu, poprawka błędu #10.
2. **Następny krok w kodzie (wymaga zgody na commit):** commit zamrażający `rules_v2` i `refs_v1`, potem jednorazowo `make validate SPLIT=test FROZEN=1 INSTRUMENTS="rules_v2 refs_v1"` i `make compare`.
3. **Praca ludzi:**
   - arbiter dla 20 spornych jednostek pilotażu (`make adjudication-sheet`), potem codebook v2.2, jeśli spory pokażą luki;
   - IS: dopisanie `pilot2` (`make append-sheets PHASE=pilot ANNOTATORS=IS`) i kodowanie, potem `make import-labels PARTIAL=1` i `make agreement`;
   - kodowanie stanowiska (`stance_*`), audyt (`audit_*`), przegląd domen (`domain_review.csv`);
   - potwierdzenie przyczyn błędów w `errors_dev.xlsx` (druga osoba sprawdza około 20%).
4. **Po etykietach:** `make agreement` dla `pilot2`, `make audit-metrics`, strojenie i test `stance_v1`, `make label-h1`, `make hypotheses CONFIRMATORY=1`.
5. **Blok 4:** wybrany instrument na pełnych danych, z udziałami skorygowanymi o błąd.

## Mapa slajdów

| Slajd | Co pokazać | Skąd |
|---|---|---|
| Codebook | konstrukt, jednostki, zmienne, 9 kategorii ze slajdu, kluczowe reguły (R3, R9, R10); przed i po (2 schematy v1 → 1 codebook); konflikty v1 z regułami: 274 skróty `WP:`, 88 znaczników, 124 niewidziane linki; zmiany v2.0 → v2.1 | `codebook/codebook.md`, sekcje „Codebook v2.0” i „Instrument v1 w kategoriach codebooka” w obu notatnikach, etap 1 |
| Gold Standard | schemat losowania i liczności; zgodność w pilotażu (tabela α i paradoks rozpowszechnienia przy `cites_source`); spory i ich rozstrzygnięcie przez arbitra; ważone udziały z samego gold | etap 2; `annotations/agreement/pilot_alpha.png`, `pilot_disagreements.csv`; `annotations/validation/gold_shares.csv`; sekcje „Gold standard” w notatnikach |
| Walidacja Błędu | ważone metryki z przedziałami (`dev` i `test`), macierz pomyłek, Pareto przyczyn błędów, błąd różnicowy, zależność od annotatora | etap 3; `annotations/validation/test_metrics.csv`, `test_confusion.csv`; `annotations/errors/dev_pareto.png`, `differential_test.csv` |
| Analiza Instrumentów | tabela instrumentów (v1, zero-shot, GLiNER, reguły v2, I4); κ instrumentów na tle κ ludzi; McNemar; τ Kendalla rankingu kategorii; wybór instrumentu do bloku 4 | etap 4; `annotations/validation/comparison_kappa.csv`, `comparison_mcnemar.csv`, `comparison_rankings.csv` |

## Decyzje do podjęcia

- Instrument AI: LLM przez API czy model lokalny, np. polski Bielik. Model lokalny nie wysyła danych na zewnątrz, co upraszcza część o RODO. Koszt API do sprawdzenia w aktualnym cenniku. W obu przypadkach użycie AI ujawniamy w preprincie.
- Kto jest arbitrem (`make adjudication-sheet PHASE=pilot ARBITER=…`). Czekają spory z pilotażu (20 jednostek), a po kodowaniu także z audytu.
- Skład próby Reddita zmienia się w czasie i to jest główne zagrożenie dla hipotezy o spadku zaufania: w 2005 r. to ogólny r/reddit.com, w latach 2006–2007 tylko r/science, a potem rośnie udział r/conspiracy (5 z 31 postów w 2008 r., 22 z 32 w 2017 r., 21 z 32 w 2020 r.). Spadek zaufania w próbie może więc wynikać po prostu ze wzrostu r/conspiracy. Polskie subreddity dają tylko 11 z 500 postów (od 2013 r., najwięcej r/PolskaPolityka w 2020 r.), bo przed 2020 r. mają po kilkadziesiąt postów rocznie wobec tysięcy w subredditach angielskich. Do decyzji: czy raportujemy trend łącznie z wagami, czy osobno dla każdego subredditu (r/science i r/conspiracy mają posty w latach 2008–2020). Dodatkowo posty są głównie po angielsku, a Wikipedia po polsku, więc codebook i instrument muszą działać w obu językach. Losowania to nie zmienia, bo subreddit jest zapisany przy każdym poście.
