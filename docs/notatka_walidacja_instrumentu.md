# Notatka: modele ekstrakcji odniesień i walidacja instrumentu

Podstawa: `notebooks/Wikipedia_EDA.ipynb` i `notebooks/Reditt_EDA.ipynb` w wersji z commita `bd46695` (kopia w folderze `Angielski_B2+`). Tam, gdzie notatka wychodzi poza te notatniki (codebook, gold standard, zgodność annotatorów), opiera się na bieżącej wersji repozytorium: `rules_v1.py`, `docs/plan_walidacji.md` i rozszerzonych sekcjach notatników w `AnalizaMediow`. Przykłady w sekcjach 2 i 3 to rzeczywiste wyniki `rules_v1.py` uruchomionego na lokalnej kopii danych.

## 1. Czym są „modele” w notatnikach

Oba „modele hybrydowe” to **ekstraktory regułowe**: wyrażenia regularne i słowniki słów kluczowych. Nie ma w nich uczenia maszynowego, nie są trenowane na danych, a ich działanie jest w pełni deterministyczne. „Hybrydowość” oznacza tylko połączenie trzech sygnałów:

1. wzorców technicznych (URL, domena, skrót Wikipedii),
2. słowników nazw serwisów i instytucji przypisanych do kategorii,
3. językowych sygnałów powołania („według”, „źródło”, „badania”…).

Pole `confidence` to **stała przypisana do gałęzi reguły**, a nie prawdopodobieństwo. Oba notatniki zastrzegają to wprost.

Oba algorytmy przechodzą te same etapy: **wybór tekstu → wykrycie wzmianek wzorcami → przypisanie kategorii → sygnał „powołania bez źródła”, gdy nic nie znaleziono → usunięcie duplikatów → zliczenia**. Różnią się szczegółami każdego etapu.

## 2. Wikipedia: algorytm krok po kroku

Kod: komórka „Model klasyfikacji źródeł i sposobu powołania” w `Wikipedia_EDA.ipynb`; identyczna kopia w `extract_wikipedia_references` i `classify_wikipedia_source` w `rules_v1.py`.

### Krok 0. Wybór tekstu

Z każdej rewizji brane jest pole `comment`, czyli **opis zmiany**, który redaktor wpisuje przy zapisie. To nie jest komentarz z dyskusji. Puste opisy są pomijane, więc analizowanych jest 2047 z 2222 rewizji (92,1%). Treść artykułu (`new_content`) nie jest analizowana.

### Krok 1. Szukanie adresów URL

Wzorzec `https?://[^\s\]})>,]+` oznacza: „http” albo „https”, potem „://”, a potem wszystkie znaki aż do spacji, `]`, `}`, `)`, `>` lub przecinka.

- Z końca znalezionego adresu obcinane są znaki `.,;:!?"`.
- Domena to część po `://` (`urlsplit(...).netloc`), zapisana małymi literami i bez `www.`.

Przykład: `objawy według WHO … (https://www.who.int/emergencies/…/coronavirus-disease-covid-19)` → adres kończy się przed `)`, domena = `who.int`.

Wymagane jest `://`, więc opis `Bot: http → https` nie daje żadnego trafienia.

### Krok 2. Szukanie skrótów Wikipedii

Wzorzec `\[\[(WP|WPT|WT):(tytuł)(|etykieta)?\]\]` (wielkość liter bez znaczenia):

- tytuł to znaki aż do `]` albo `|`; część po `|` (tekst linku) jest pomijana;
- wynik jest zapisywany jako `PRZESTRZEŃ:tytuł`, np. `[[WP:MARTWE|poprawa martwych linków]]` → `WP:MARTWE`;
- każdy skrót **dostaje sztuczną domenę `wikipedia.org`**. Ma to duże znaczenie w kroku 4.

Wzorzec nie łapie innych linków wewnętrznych, np. `[[Pomoc:Słowniczek#W|wikizacja]]` czy `[[commons:…]]`. W danych jest 59 opisów z `[[Pomoc:`, które nie dają żadnej wzmianki.

### Krok 3. Rozgałęzienie: jest wzmianka czy nie?

- **Są URL-e lub skróty:** każda wzmianka przechodzi do kroku 4.
- **Nie ma żadnej:** opis jest przeszukiwany listą słów-sygnałów `SOURCE_CUES`. Regex z granicami słów `\b` sprawdza: według, źródło, źródła, badania, badanie, raport, dane, artykuł, publikacja, jak podaje, podaje, link, cytuję, opublikowano.
  - Sygnał jest: powstaje jedna wzmianka „niesprecyzowane źródło” i również trafia do kroku 4, z pustym odniesieniem i pustą domeną.
  - Sygnału nie ma: opis nie daje nic, np. `drobne redakcyjne, int.`.

Granice słów działają tak: „link” pasuje w „poprawiam link”, ale nie w „linka”. „publikacja” nie pasuje do „publikacji”.

### Krok 4. Klasyfikacja `classify_source(reference, domain, comment)`

1. Skleja **odniesienie + domenę + cały opis zmiany** w jeden tekst, zapisany małymi literami (`casefold`).
2. Przechodzi kategorie **w ustalonej kolejności** i zwraca pierwszą, której dowolny termin występuje w tym tekście jako **podciąg**, bez granic słów:

   | Kolejność | Kategoria | Przykładowe terminy |
   |---|---|---|
   | 1 | instytucje publiczne | gov.pl, who.int, ecdc.europa.eu, nfz, gis, gus, urząd |
   | 2 | nauka i edukacja | doi.org, pubmed, pwn.pl, academia.edu, uniwersytet, instytut |
   | 3 | media | gazeta, tvn, onet, wp.pl, bbc, reuters, guardian |
   | 4 | organizacje społeczne i środowiskowe | wwf, greenpeace, fundacja, ngo |
   | 5 | źródła encyklopedyczne | wikipedia.org, wikimedia.org, wikiwand |
   | 6 | źródła osobiste | widziałem, pamiętam, użytkownik |

   Trafienie daje `confidence = 0,90`.
3. Nic nie pasuje, ale jest domena: „inna domena zewnętrzna”, **0,80**.
4. Nie ma domeny, ale jest sygnał: „powołanie bez wskazanego źródła”, **0,55**.
5. W pozostałych przypadkach: „odniesienie techniczne Wikipedii”, **0,95**.

Przebieg na prawdziwych opisach zmian:

| Opis zmiany | Wzmianka | Co zadecydowało | Wynik |
|---|---|---|---|
| `[[WP:SK]], drobne techniczne` | `WP:SK` | sztuczna domena `wikipedia.org` | źródła encyklopedyczne, 0,90 |
| `objawy według WHO … (https://www.who.int/…)` | URL | `who.int` | instytucje publiczne, 0,90 |
| `[[WP:MARTWE\|poprawa martwych linków]] (Reuters)` | `WP:MARTWE` | „reuters” w opisie; media są sprawdzane przed encyklopediami | **media**, 0,90 |
| `[[WP:REFNIEUŻYTE]]: … przypisie "debbc"` | `WP:REFNIEUŻYTE` | „bbc” jako podciąg nazwy przypisu „debbc” | **media**, 0,90 |
| `drobne redakcyjne, źródła/przypisy` | brak, sygnał „źródła” | znacznik typu edycji | powołanie bez wskazanego źródła, 0,55 |
| `MalarzBOT: WPCHECK#64: poprawiam link…` | brak, sygnał „link” | opis zmiany wykonanej przez bota | powołanie bez wskazanego źródła, 0,55 |

Z tej konstrukcji wynikają cztery rzeczy:

- **Skróty `WP:` stają się „źródłami encyklopedycznymi”**, bo ich sztuczna domena `wikipedia.org` jest w słowniku kategorii 5.
- **Gałąź 0,95 nigdy się nie wykonuje.** Każdy URL ma domenę, każdy skrót ma `wikipedia.org`, a ścieżka bez wzmianki wymaga sygnału. Dlatego „odniesienie techniczne” nie pojawia się w wynikach.
- **Kategorię wzmianki może ustalić dowolne słowo z opisu**, a nie sama wzmianka, bo do dopasowania wchodzi cały opis. Terminy bez granic słów (np. „gis”, „gus”, „ngo”, „bbc”) mogą trafiać w środek innych wyrazów.
- **Ścieżka bez wzmianki też może dostać konkretną kategorię**, jeśli w opisie pada słowo ze słownika. Na 200 takich wzmianek 3 trafiły do innej kategorii niż „powołanie bez wskazanego źródła”.

### Krok 5. Kolumna `cue`

Przy każdej wzmiance zapisywane jest pierwsze słowo-sygnał z całego opisu, także przy URL-ach (przy WHO jest to „według”). Kolumna służy tylko do podglądu i nie wpływa na kategorię wzmianki z URL-em lub skrótem.

Rozkład sygnałów w ścieżce bez wzmianki: „źródła” 120, „link” 38, „źródło” 12, „dane” 11, „według” 6, „badania” 5, „artykuł” 5, „badanie” 2, „raport” 1. Większość pochodzi ze znacznika „źródła/przypisy” (według diagnozy w `plan_walidacji.md` 88 wzmianek) i z komunikatów botów o linkach.

### Krok 6. Duplikaty i zliczenia

Wiersze są unikalne po (strona, rewizja, odniesienie, kategoria). `[[WP:SK]]+[[WP:SK/mSI]]+[[WP:SK/Bn]]` to 3 różne odniesienia, a ten sam skrót powtórzony w opisie liczy się raz.

Wynik: 370 opisów z odniesieniem, 485 wzmianek, 39 unikalnych odniesień, średnia `confidence` 0,76.

| Kategoria | Wystąpienia |
|---|---:|
| źródła encyklopedyczne | 271 |
| powołanie bez wskazanego źródła | 197 |
| instytucje publiczne | 6 |
| media | 4 |
| nauka i edukacja | 4 |
| organizacje społeczne i środowiskowe | 2 |
| inna domena zewnętrzna | 1 |

**Wersja bazowa** z wcześniejszej komórki („Odniesienia i źródła przywoływane w komentarzach”) wykonuje tylko kroki 1–2. Typ wzmianki to `external_url` albo `wikipedia_wp`, bez kategorii, sygnałów i deduplikacji. Daje 170 opisów i 285 wzmianek: 274 skróty `WP:` (28 unikalnych) i 11 URL-i w 8 domenach (m.in. aids.gov.pl, ecdc.europa.eu, sjp.pwn.pl, who.int, wwf.pl). Skróty `WPT:` i `WT:` nie wystąpiły ani razu. Wzrost z 170 do 370 opisów w modelu to głównie ścieżka sygnału z kroku 3.

## 3. Reddit: algorytm krok po kroku

Kod: komórka „Odniesienia do źródeł w treści wpisów i komentarzy” w `Reditt_EDA.ipynb`; identyczna kopia w `extract_reddit_mentions` i `extract_reddit_references` w `rules_v1.py`.

### Krok 0. Wybór tekstu

Kod bierze pierwszą istniejącą kolumnę z listy `comment` → `comment_text` → `body` → `text`; gdy żadnej nie ma, `title`. Eksport Reddita nie zawiera komentarzy, jest w nim tylko `text`, więc analizowana jest **wyłącznie treść posta**.

- Tytuł i pole `url` są pomijane. Post o tytule „Badanie (…)” jest oceniany tylko po treści.
- Niepustą treść ma 187 z 275 postów; pozostałe nie mogą dać żadnej wzmianki.

### Krok 1. Normalizacja

Brak tekstu zamieniany jest na `""`. Do słowników używana jest kopia zapisana małymi literami (`casefold`). Wzorzec URL działa na oryginale, ale bez rozróżniania wielkości liter.

### Krok 2. Linki i domeny

Wzorzec ma dwie alternatywy:

- **(a) pełny adres:** `https?://` i znaki aż do spacji, `]`, `)`, `<`, `>` lub cudzysłowu;
- **(b) „goła” domena:** opcjonalne `www.`, potem litery, cyfry, kropki i myślniki, końcówka `.pl/.com/.org/.net/.eu/.gov` i opcjonalna ścieżka.

Domena to tekst po usunięciu `http(s)://` aż do pierwszego `/`, zapisany małymi literami. **Prefiks `www.` zostaje**, więc `www.youtube.com` i `youtube.com` liczą się jako różne źródła. Każde trafienie daje wzmiankę **„link/domena”** z `confidence = 1,0`. Domen nie przypisuje się do kategorii źródeł.

Przykłady:

- `[https://www.bananki.pl/ps4/](https://www.bananki.pl/ps4/)`: link w Markdownie daje **2 identyczne trafienia**, które scala dopiero krok 5.
- Alternatywa (b) łapie nazwy w tekście, np. `WP.pl`, `SE.pl`, `WPROST.pl`, ale też **adres e-mail**. W poście z naborem testerów aplikacji z adresu `…@gmail.com` powstaje źródło `gmail.com`.
- Każdy link jest „źródłem”, także zdjęcia (`preview.redd.it`) i formularze ankiet (`forms.gle`, `forms.cloud.microsoft`).

### Krok 3. Słowniki kategorii

Słowniki obejmują 7 kategorii: media informacyjne, źródła oficjalne, nauka i medycyna, platformy i media społecznościowe, encyklopedie i bazy wiedzy, źródła komercyjne, źródła osobiste i społecznościowe. Dla każdego terminu kod sprawdza `term in lowered`, czyli **podciąg bez granic słów**.

- Każde trafienie to osobna wzmianka z `confidence = 0,85`.
- Jako odniesienie zapisywany jest **sam termin**, np. „znajomy”, a nie fragment tekstu.
- W odróżnieniu od Wikipedii **nie ma kolejności ani wyboru jednej kategorii**: post dostaje wszystkie pasujące.

Przebieg na prawdziwych postach:

| Fragment posta | Trafiony termin | Kategoria |
|---|---|---|
| „Zbieramy/szukamy **znajomy**ch” | znajomy | źródła osobiste i społecznościowe |
| „związana była w owym czasie z Bo**gus**iem” | gus | źródła oficjalne |
| „Malcolm Fer**gus**on” | gus | źródła oficjalne |
| `https://wiadomosci.wp.pl/kolejny-skandal…` | wp.pl wewnątrz adresu | media informacyjne |

Ostatni przykład pokazuje **podwójne liczenie**: ten sam link daje wzmiankę „link/domena” (`wiadomosci.wp.pl`) z kroku 2 i wzmiankę „media” (`wp.pl`) z kroku 3. Dotyczy to wszystkich 10 postów z wp.pl.

Diagnoza w `plan_walidacji.md` wskazuje podobne fałszywe trafienia: „mieszkam” w „mieszkam na wsi”, „lekarz” w opisie wizyty, „badanie” w rekrutacji do ankiety.

### Krok 4. Sygnał powołania

Kod sprawdza, czy w tekście występuje któreś słowo-sygnał jako podciąg: według, źródło, czytałem, przeczytałam, badania pokazują, jak podaje, podano, link, artykuł… **Tylko gdy kroki 2–3 nic nie znalazły**, a sygnał jest, powstaje wzmianka „niesprecyzowane źródło” w kategorii „sygnał powołania” z `confidence = 0,55`. Dzieje się tak w 5 postach.

Przykład: post z prośbą o wypełnienie ankiety do pracy dyplomowej zawiera słowo „link”, więc dostaje „sygnał powołania”, choć autor nie powołuje się na żadne źródło. Słowniki z kroku 3 są szerokie (np. „badania” jest już w kategorii nauka), więc ta ścieżka uruchamia się rzadko.

### Krok 5. Duplikaty

Wiersze są unikalne po (post, odniesienie, kategoria):

- dwa identyczne linki `www.bananki.pl` z Markdownu scalają się w jeden;
- `wp.pl` jako „link/domena” i `wp.pl` jako „media” **zostają oba**, bo mają różne kategorie.

### Krok 6. Zliczenia

Kod buduje trzy tabele: kategorie (liczba wzmianek, unikalne źródła, średnia `confidence`), źródła (liczba wzmianek, liczba postów, średni score posta) oraz przykłady po jednym na kategorię.

Wynik: 197 wzmianek w 99 z 275 postów.

| Kategoria | Wzmianki | Unikalne |
|---|---:|---:|
| link/domena | 97 | 63 |
| media informacyjne | 25 | 9 |
| źródła osobiste i społecznościowe | 22 | 7 |
| nauka i medycyna | 15 | 3 |
| źródła oficjalne | 12 | 6 |
| źródła komercyjne | 10 | 2 |
| platformy i media społecznościowe | 10 | 4 |
| sygnał powołania | 5 | 1 |
| encyklopedie i bazy wiedzy | 1 | 1 |

## 4. Porównanie obu ekstraktorów

| Cecha | Wikipedia | Reddit |
|---|---|---|
| Jednostka | opis zmiany (edit summary) | treść posta (`text`) |
| Wzorce techniczne | URL, skróty `[[WP/WPT/WT:…]]` | URL i „gołe” domeny |
| Odniesienie zapisane jako | URL albo skrót | domena albo sam termin ze słownika |
| Klasyfikacja domen | tak, przez słownik | nie, osobna kategoria „link/domena” |
| Kategorii na wzmiankę | jedna (pierwsza pasująca, kolejność = priorytet) | każda pasująca |
| Kontekst dopasowania | cały opis zmiany (wyciek kontekstu) | cały post |
| Granice słów | sygnały tak, terminy kategorii nie | nigdzie |
| Ścieżka sygnału uruchamia się | gdy nie ma URL-a ani skrótu | gdy nie ma linku ani terminu ze słownika |
| Sygnał bez źródła | „powołanie bez wskazanego źródła” (0,55) | „sygnał powołania” (0,55) |
| `confidence` | 0,95 (nieosiągalne) / 0,90 / 0,80 / 0,55 | 1,0 / 0,85 / 0,55 |
| Liczba kategorii | 6 + 3 pomocnicze | 7 + 2 pomocnicze |

Schematy kategorii są różne (np. „nauka i edukacja” i „nauka i medycyna”), więc wyników z obu platform nie da się bezpośrednio porównać.

## 5. Jak została wykonana walidacja instrumentu

### 5.1 Co faktycznie jest w notatnikach (stan `bd46695`)

W tej wersji notatników **nie ma walidacji instrumentu w ścisłym sensie**, czyli porównania z etykietami referencyjnymi i miar błędu. Kontrola ogranicza się do:

1. **Kontroli jakości danych wejściowych:** braki, puste treści (6 rewizji), obecność pola `comment` we wszystkich rewizjach, odsetek opisów (92,1%, od 89,8% do 96% w zależności od strony); na Reddicie brakujące daty, tytuły i kolumny.
2. **Statystyk pokrycia:** ile jednostek ma odniesienie, ile jest wystąpień i unikalnych źródeł, rozkład kategorii i domen.
3. **Porównania wersji bazowej z modelem (Wikipedia):** 170 → 370 opisów z odniesieniem, 285 → 485 wystąpień.
4. **Inspekcji jakościowej (trafności fasadowej):** tabele pierwszych 20 wzmianek oraz tabela przykładów, po jednym na kategorię (o najwyższej `confidence`), do ręcznego przejrzenia.
5. **Zastrzeżeń interpretacyjnych:** `confidence` to heurystyka, nie każda wzmianka nazwy jest cytowaniem, na Reddicie analizowane są posty, a nie komentarze, a `comment` na Wikipedii to opis zmiany.

Zabrakło: gold standardu, metryk (precyzja, czułość, F1), zgodności annotatorów i kalibracji `confidence`. Średnia `confidence` 0,76 to średnia ze stałych, więc nie mierzy jakości. Przy okazji: w tabeli kategorii Wikipedii kolumna „komentarze” liczy unikalne `revision_number` bez strony, co zaniża wynik (np. 136 zamiast 156 dla źródeł encyklopedycznych).

### 5.2 Walidacja przygotowana w repozytorium (blok 3)

**Krok 1. Zamrożenie instrumentu.** Kod z obu notatników przeniesiono 1:1 do `src/digital_media_analysis/instruments/rules_v1.py` jako punkt odniesienia v1. Identyczność wyników sprawdzono `assert_frame_equal` na pełnych danych, a `tests/test_rules_v1.py` przypina zachowanie v1 razem ze znanymi błędami. Poprawki trafiają do kolejnych wersji, a nie do v1.

**Krok 2. Codebook v1.0** (`codebook/codebook.yaml`, `codebook.md`). Zastępuje dwa schematy jednym:

- 3 zmienne: `cites_source`, `source_types`, `edit_about_sources`;
- 10 kategorii z definicją, kryteriami włączenia i wykluczenia;
- 12 reguł rozstrzygania.

Kategorie v1 są mapowane na kody codebooka (`REDDIT_CATEGORY_MAP`, `WIKIPEDIA_CATEGORY_MAP`), a wzmianki zwijane do etykiet dokumentu (`instruments/labels.py`).

**Krok 3. Rozbieżności v1 z codebookiem, widoczne bez annotacji:**

- Wikipedia: 274 z 485 wzmianek to skróty `WP:` liczone jako źródło, choć według reguły R9 nie są źródłem; 88 wzmianek to sam znacznik „źródła/przypisy”, który według R10 należy do `edit_about_sources`, a nie do powołania;
- Reddit: 13 z 97 linków to zdjęcia lub ankiety (R3); 124 z 275 postów ma link w polu `url`, którego v1 nie widzi.

**Krok 4. Próba gold standard** (`gold.py`, ziarno 20261016):

- Reddit: warstwy = subreddity; 24 pilot / 47 dev / 99 test;
- Wikipedia: warstwy = sygnał (`link`, `cue`, `other`) × strona; 30 pilot / 75 dev / 174 test;
- wagi N_h / n_h korygują nadpróbkowanie;
- manifest bez tekstu w repo, odcisk danych SHA-256 w `sample_design.json`.

**Krok 5. Ślepa annotacja:** arkusze XLSX bez wyników instrumentu, z walidacją kodów (`annotation_sheets.py`) i importem etykiet (`annotations.py`).

**Krok 6. Zgodność annotatorów** (`agreement.py`):

- κ Cohena i α Krippendorffa: nominalna dla zmiennych 0/1, z odległością MASI dla zbioru typów;
- 95% przedziały bootstrap (2000 losowań);
- progi: α ≥ 0,8 oznacza zgodność rzetelną, 0,667–0,8 tylko wstępne wnioski;
- kategorie z mniej niż 5 przypadkami są raportowane bez oceny.

**Stan na 16.10.2026:** arkusze pilotażu (`pilot_A.xlsx`, `pilot_B.xlsx`) są puste, więc **nie ma jeszcze żadnych liczb o jakości instrumentu**. Sekcje zgodności w notatnikach wypisują „Brak etykiet pilotażu od dwóch osób”.

### 5.3 Co pozostaje do zrobienia (etapy 3–4 planu)

- Ważone precyzja, czułość i F1 v1 względem gold (dev + test), macierz pomyłek, Jaccard dla typów.
- Analiza przyczyn błędów (podciąg, skrót `WP:`, znacznik edycji, wyciek kontekstu, pominięte `url`…) i błąd różnicowy między subredditami i stronami.
- Kalibracja `confidence` (empiryczna precyzja dla każdej stałej).
- Korekta częstości metodą Rogana–Gladena.
- Porównanie z regułami v2 i instrumentem AI na zbiorze testowym.
