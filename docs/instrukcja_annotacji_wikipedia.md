# Instrukcja annotacji: Wikipedia (`wikipedia_sample.csv`)

*Codebook v2.0 z 18.10.2026.* Ta instrukcja prowadzi krok po kroku przez kodowanie opisów zmian z Wikipedii. Pełne definicje kategorii i reguły R1–R13 są w [`codebook/codebook.md`](../codebook/codebook.md); gdy instrukcja i codebook się różnią, rozstrzyga codebook. Posty z Reddita kodujemy według osobnej instrukcji: [`instrukcja_annotacji_reddit.md`](instrukcja_annotacji_reddit.md).

## W skrócie

1. Kodujesz w arkuszu `annotations/sheets/<faza>_<inicjały>.xlsx`, w zakładce **Wikipedia**. Nie wpisujesz etykiet do pliku CSV.
2. Jednostka to wyłącznie **opis zmiany** (pole `comment`) jednej rewizji. Nie kodujesz treści artykułu ani nie zaglądasz do historii strony.
3. W każdym wierszu wpisujesz dwie etykiety:
   - `source_types`: kody źródeł rozdzielone średnikiem albo `none`, gdy opis nie powołuje się na źródło;
   - `edit_about_sources`: 1, gdy opis deklaruje pracę nad źródłami lub przypisami, w przeciwnym razie 0.
4. Przy wątpliwościach ustawiasz `uncertain = 1` i krótko opisujesz problem w `notes`.
5. Kodujesz samodzielnie, do końca arkusza, a potem oddajesz plik koordynatorowi.

## 1. Plik `wikipedia_sample.csv` a arkusz annotacji

`data_samples/wikipedia_sample.csv` zawiera 500 opisów zmian wylosowanych do gold standardu. Pochodzą z rewizji z lat 2020–2026 ośmiu stron wymienionych w `config.yaml` (`wikipedia_pages`), np. COVID-19, Szczepionka, Lekarz. To plik referencyjny z pełnymi danymi. Etykiety wpisujemy w arkuszu XLSX, który koordynator generuje z tej samej próby. Zakładka Wikipedia zawiera opisy jednej fazy:

- **pilotaż:** 51 opisów (`phase = pilot`), na kalibrację codebooka: najpierw 21 z pierwszej rundy (`split = pilot`), potem 30 z drugiej (`split = pilot2`, lata 2020–2022 i 2024, bo pozostałe lata weszły do próby w całości). Druga runda pochodzi spoza 500 opisów próby, więc plik CSV ma 530 wierszy;
- **próba główna:** 479 opisów (`phase = gold`). Opisy `dev` i `test` są wymieszane, więc nie wiadomo, które są testowe.

Dlaczego arkusz, a nie CSV:

- arkusz jest ślepy, czyli bez kolumn losowania;
- ma ustaloną losową kolejność, listy 0/1 i podpowiedź z kodami;
- import (`make import-labels`) sprawdza go automatycznie.

Kolumna `signal` w CSV mówi, czy opis zawiera link albo słowa o źródłach. Gdyby annotator ją widział, sugerowałaby mu odpowiedź.

**Uwaga:** pliku `wikipedia_sample.csv` nie otwieraj i nie zapisuj w Excelu. Ma około 51 MB, a Excel ucina komórki dłuższe niż 32 767 znaków; dotyczy to pełnego tekstu artykułu w 371 z 500 wierszy. Zapisanie pliku z Excela by go uszkodziło. Do analiz czytamy go w pandas.

| Kolumna w CSV | Kolumna w arkuszu | Czy używasz przy kodowaniu? |
|---|---|---|
| `unit_id` (`strona#numer_rewizji`, np. `COVID-19#1520`) | `unit_id` | identyfikator; nie zmieniaj go |
| `page` | `strona` | tylko jako kontekst |
| `comment` | `opis zmiany` | **tak: to jedyny kodowany tekst** |
| `new_content` | (brak) | **nie:** to pełny tekst artykułu po zmianie, a nie jednostka analizy |
| `url`, `revision_number`, `introduced`, `content_chars` | (brak) | nie |
| `year`, `phase`, `split`, `order`, `stratum`, `signal`, `N_h`, `n_h`, `weight` | (brak) | nie: to kolumny losowania |

Czego się spodziewać w tej próbie:

- opisy są krótkie (mediana 49 znaków), prawie wszystkie po polsku;
- większość to wpisy techniczne, które nie są powołaniem: 146 z 500 ma automatyczny prefiks sekcji `/* … */`, 71 to rewerty, 58 zawiera skróty `[[WP:…]]`, a 52 to „drobne redakcyjne/techniczne”;
- znacznik „źródła/przypisy” ma 27 opisów, a link URL tylko 10;
- najczęstsza poprawna etykieta to więc `none`, często z `edit_about_sources = 0`.

## 2. Przygotowanie

**Koordynator** (osoba z lokalną kopią danych w `data/`):

1. Generuje arkusze pilotażu: `make pilot-sheets ANNOTATORS="JP IS"`. Bez `make`: `uv run scripts/03_export_annotation_sheets.py --phase pilot --annotators JP IS`. Powstają pliki `annotations/sheets/pilot_JP.xlsx` i `pilot_IS.xlsx`; jeden plik zawiera zakładki Reddit i Wikipedia.
2. Przekazuje każdej osobie jej plik poza gitem, np. na dysku zespołu. Arkusze są w `.gitignore` i nie trafiają do repozytorium.
3. Po pilotażu i poprawkach codebooka (v2.1) generuje arkusze próby głównej: `uv run scripts/03_export_annotation_sheets.py --phase gold --annotators JP IS`.
4. Gdy próbę główną dzielicie między osoby, eksportuje tylko kolejne jednostki za ostatnim wierszem zakodowanym przez kogoś innego, np. `uv run scripts/03_export_annotation_sheets.py --phase gold --annotators JP --after annotations/sheets/gold_IS.xlsx --reddit 60 --wikipedia 130`. Arkusz ma te same zakładki i kolumny, ale tylko wybrane wiersze. Zgodność liczymy wtedy tylko na pilotażu, który obie osoby kodują w całości.

**Annotator:**

1. Czyta w całości `codebook/codebook.md`, zwłaszcza reguły R9 i R10, a potem tę instrukcję.
2. Otwiera swój plik w Excelu albo w LibreOffice Calc. Nie konwertuje go do Arkuszy Google, bo giną listy rozwijane i zapisana w pliku wersja codebooka.
3. Trzyma pod ręką zakładkę „Instrukcja” z tabelą kodów.

## 3. Kolumny do wypełnienia (zakładka Wikipedia)

Wypełniasz żółte kolumny:

| Kolumna | Co wpisać | Wymagana? |
|---|---|---|
| `source_types` | kody z listy poniżej rozdzielone średnikiem, np. `institutional;media`; `none`, gdy nie ma powołania | tak, w każdym wierszu |
| `edit_about_sources` | `0` lub `1` (lista rozwijana) | tak, w każdym wierszu |
| `uncertain` | `0` lub `1` (lista rozwijana); puste pole liczy się jako 0 | nie |
| `notes` | krótki opis wątpliwości, numer reguły, proponowana zmiana codebooka | tak, gdy `uncertain = 1` |
| `annotator` | (wpisane już inicjały) | nie zmieniaj |

Dozwolone kody: `scientific`, `institutional`, `media`, `personal`, `social_blog`, `encyclopedia`, `other`, `unknown`, `none`. Kolejność kodów, wielkość liter i spacje nie mają znaczenia, a przecinek też działa jako separator.

W zakładce nie ma kolumny `cites_source`, bo wyliczamy ją z `source_types`: 0 przy `none`, 1 przy każdym innym kodzie (R13).

## 4. Procedura dla jednego opisu zmiany

**Krok 1. Przeczytaj opis zmiany.** Bierzesz pod uwagę tylko tekst z kolumny `opis zmiany`. Nazwa strony służy jako kontekst.

**Krok 2. Pomiń automatyczny prefiks sekcji.** Fragment `/* Nazwa sekcji */` na początku dodaje edytor; mówi tylko, którą sekcję edytowano (R9). Nie liczy się nawet `/* Przypisy */` albo `/* Bibliografia */`. Opis, który składa się z samego prefiksu, to `none` i `edit_about_sources = 0`.

**Krok 3. Pomiń elementy techniczne (R9):**

- skróty zasad i narzędzi: `[[WP:SK]]`, `[[WP:NPOV]]`, `[[WP:1000]]`, `[[Pomoc:…]]`;
- odnośniki do użytkowników i stron specjalnych: `[[Special:Contributions/…]]`, `[[User talk:…]]`;
- opisy redakcyjne: „drobne redakcyjne”, „drobne techniczne”, „int.”, „kat.”, „lit.”, „ort.”, „styl”, „techn”;
- komunikaty botów;
- rewerty: „Wycofano edycję użytkownika…”, „Anulowanie wersji…”;
- linki wewnętrzne i interwiki („Dodano link wewnętrzny do…”, „poprawiam linki interwiki”).

**Krok 4. Zdecyduj o `edit_about_sources`** (punkt 5). To zmienna niezależna od `source_types`. Opis może deklarować pracę nad przypisami i jednocześnie nie wskazywać żadnego źródła.

**Krok 5. Znajdź powołania na źródło i nadaj im kategorie** według ściągawki w punkcie 6:

- linki URL: decyduje domena;
- nazwy źródeł lub ich typów: „wg WHO”, „Przypis z EPWN”, „wg Dz.U.”, „raport GUS”, „źródło uniwersyteckie”;
- ogólniki: „wg źródła”, „w literaturze”, „badania pokazują”.

Kategorię wyznacza wydawca lub kanał (R4). Gdy opis wymienia też źródło pierwotne, zaznaczasz obie kategorie. Ogólnik to `unknown` tylko wtedy, gdy ten sam fragment nie wskazuje konkretnego źródła (R5).

**Krok 6. Odrzuć to, co nie jest powołaniem:**

- instytucja albo osoba jako temat zmiany: „Uniwersytet X został przemianowany na…” (R2);
- własna opinia: „wg mnie zbędne” (R8);
- prośba o źródło: „źródło?”, „brak źródła” (R8);
- sam znacznik „źródła/przypisy” (R10: wpływa tylko na `edit_about_sources`).

**Krok 7. Wpisz kody.** Każdy znaleziony kod wpisujesz raz (R1). Jeśli nie zostało żadne powołanie, wpisujesz `none` bez innych kodów (R13). Połączenie `source_types = none` i `edit_about_sources = 1` jest poprawne i częste.

**Krok 8. Oceń pewność.** Jeśli się wahasz, wybierasz najlepsze etykiety, ustawiasz `uncertain = 1` i piszesz w `notes`, czego dotyczy wątpliwość (punkt 9).

Nie oceniamy wiarygodności źródła ani trafności edycji (R6).

## 5. `edit_about_sources`: praca nad źródłami i przypisami

**1**, gdy opis deklaruje dodanie, usunięcie, wymianę albo poprawę źródeł lub przypisów, np.:

- znacznik „źródła/przypisy”, także na końcu dłuższego opisu;
- „dodano przypis”, „dodanie źródła”, „uźródłowienie”, „Przypis z EPWN”;
- „poprawa przypisów”, „aktualizacja źródeł”, „usunięcie martwego linku w przypisie”.

**0** we wszystkich pozostałych przypadkach, w tym:

- sam prefiks sekcji `/* Przypisy */` bez słów o pracy nad przypisami (R9);
- dodanie linku wewnętrznego albo kategorii;
- zmiany treści, stylu i formatowania bez wzmianki o źródłach.

`edit_about_sources = 1` nie oznacza powołania. Kategorię źródła zamiast `none` wpisujesz tylko wtedy, gdy opis identyfikuje źródło albo jego typ: „dodano przypis do raportu WHO” to `institutional`, a samo „źródła/przypisy” to `none` (R10).

## 6. Kategorie na Wikipedii: ściągawka

| Kod | Kiedy | Przykłady w opisach zmian |
|---|---|---|
| `scientific` | konkretna publikacja naukowa | link `doi.org`, `pubmed`, `nature.com/articles/…`; „publikacja w The Lancet”, „źródło uniwersyteckie”, „podręcznik akademicki” |
| `institutional` | instytucja naukowa, statystyczna albo zdrowia publicznego jako źródło | `who.int`, `ecdc.europa.eu`, `aids.gov.pl`, `stat.gov.pl`; „wg WHO”, „dane GUS”, „zalecenia GIS”, „wg PZH”, uczelnia lub instytut jako źródło |
| `media` | redakcje informacyjne i magazyny | link do portalu lub gazety; „wg PAP”, „jak podaje TVN24” |
| `personal` | własne doświadczenie albo relacja konkretnej osoby jako dowód | „z własnego doświadczenia”, „jako lekarz wiem, że…” (rzadkie) |
| `social_blog` | media społecznościowe, platformy i blogi | link do YouTube, X/Twitter, Facebooka, bloga |
| `encyclopedia` | encyklopedie, słowniki i bazy wiedzy | link do Wikipedii w innym języku, Britanniki, `sjp.pwn.pl`; „Przypis z EPWN”, „wg SJP”. **Nie** skróty `[[WP:…]]` ani linki wewnętrzne `[[Artykuł]]` |
| `other` | zidentyfikowane źródło spoza powyższych: urzędy i administracja, prawo, firmy, NGO, inne strony | „wg Dz.U.”, ustawa, rozporządzenie, ministerstwo, `gov.pl`, strona fundacji (np. WWF), strona producenta |
| `unknown` | odwołanie bez wskazania źródła | „wg źródła”, „według źródeł”, „w literaturze”, „badania pokazują” |
| `none` | brak jakiegokolwiek powołania | opisy techniczne, rewerty, boty, sam prefiks sekcji, sam znacznik „źródła/przypisy” |

## 7. Typowe sytuacje

| Opis zmiany (schemat) | `source_types` | `edit_about_sources` | Reguła |
|---|---|---|---|
| `[[WP:SK]], drobne techniczne` | `none` | 0 | R9 |
| sam prefiks `/* Przypisy */` | `none` | 0 | R9 |
| `/* Skutki */ styl` | `none` | 0 | R9 |
| `drobne redakcyjne, źródła/przypisy` | `none` | 1 | R10 |
| `Wycofano edycję użytkownika … (dyskusja)` | `none` | 0 | R9 |
| `poprawiam linki interwiki` albo `Dodano link wewnętrzny do…` | `none` | 0 | R9 |
| `Przypis z EPWN` | `encyclopedia` | 1 | |
| `wg Dz.U. 2022 poz. … choroba nie kwalifikuje się…` | `other` | 0 | akt prawny |
| `/* Kontrowersje */ sugerowane w literaturze rozwiązanie…, źródła/przypisy` | `unknown` | 1 | R5, R10 |
| `dodano przypis do raportu WHO` | `institutional` | 1 | R10 |
| `wg źródła jeszcze kapusta` | `unknown` | 0 | R5 |
| `Uniwersytet X został przemianowany na…` (sama informacja) | `none` | 0 | R2 |
| `wg mnie to zbędne` | `none` | 0 | R8 |
| `according to the CDC` (opis po angielsku) | `institutional` | 0 | R11 |

## 8. Przykłady rozwiązane

1. **`[[WP:SK]], drobne techniczne`**: `none`, 0. `[[WP:SK]]` to skrypt porządkujący kod strony, a nie źródło; „drobne techniczne” to opis redakcyjny (R9).
2. **`/* Przypisy */`**: `none`, 0. To tylko automatyczna informacja o edytowanej sekcji. Nie wiemy, czy zmiana dotyczyła przypisów, bo autor tego nie zadeklarował (R9).
3. **`drobne redakcyjne, źródła/przypisy`**: `none`, 1. Znacznik deklaruje pracę nad przypisami, ale nie wskazuje żadnego źródła (R10).
4. **`Przypis z EPWN`**: `encyclopedia`, 1. Autor dodał przypis i wskazał jego źródło, Encyklopedię PWN.
5. **`wg Dz.U. 2022 poz. 1657 choroba nie kwalifikuje się na obowiązkowe leczenie`**: `other`, 0. Dziennik Ustaw to akt prawny, a prawo i administracja należą do `other`. Opis nie mówi o przypisach.
6. **`/* Kontrowersje */ sugerowane w literaturze rozwiązanie problemu…, źródła/przypisy`**: `unknown`, 1. „W literaturze” to ogólnik bez wskazania publikacji (R5), a znacznik daje `edit_about_sources = 1` (R10).
7. **`Wycofano edycję użytkownika [[Special:Contributions/…]] ([[User talk:…|dyskusja]]).`**: `none`, 0. Rewert nie jest powołaniem, a odnośniki do użytkownika to elementy techniczne (R9).
8. **`We wrześniu 2023 Uniwersytet X został mianowany Uniwersytetem Y`**: `none`, 0. Uczelnia jest tematem zmiany, a nie źródłem informacji (R2).
9. **`Dodano link wewnętrzny do GRID.`**: `none`, 0. Link wewnętrzny łączy artykuły Wikipedii i nie jest źródłem.
10. **`Objawy uzupełnione według WHO`** i link do `who.int`: `institutional`; `edit_about_sources` = 0. Autor wskazuje źródło informacji, ale nie deklaruje pracy nad przypisami. Jeśli uważasz, że link w opisie oznacza dodany przypis, wpisz 1 z `uncertain = 1` i uzasadnieniem w `notes`.

## 9. Wątpliwości: `uncertain` i `notes`

Ustaw `uncertain = 1`, gdy:

- nie wiesz, czy opis deklaruje pracę nad przypisami. Przykład: rewert z komentarzem „nie możesz usuwać bloków tekstu z przypisami”, który przywraca tekst razem z przypisami;
- skrót lub nazwa źródła jest niejasna i nie wiesz, do jakiej kategorii należy;
- nie wiesz, czy nazwa instytucji jest źródłem, czy tematem zmiany (R2).

W `notes` napisz krótko, na czym polega problem, z numerem reguły i alternatywną etykietą, np. „R10: rewert przywraca tekst z przypisami, czy to praca nad przypisami? wpisałem 0”.

Etykiety wybierasz zawsze, także przy wątpliwościach. `source_types` i `edit_about_sources` nigdy nie zostają puste (R12). Takie przypadki omawiamy na sesji uzgadniania i mogą one zmienić codebook.

## 10. Po zakończeniu

1. Sprawdź, czy każdy wiersz ma `source_types` i `edit_about_sources` oraz czy `none` nie występuje razem z innymi kodami.
2. Zapisz plik jako `.xlsx` pod tą samą nazwą (np. `pilot_JP.xlsx`) i oddaj go koordynatorowi poza gitem.
3. Koordynator kopiuje plik do `annotations/sheets/` i uruchamia `make import-labels`. Bez `make`: `uv run scripts/04_import_annotations.py --phase pilot`; z opcją `--check` skrypt tylko sprawdza arkusze. Gdy próba główna jest podzielona między osoby albo zakodowana tylko w części, import uruchamia z `--partial` (`make import-labels PHASE=gold PARTIAL=1`). Wiersze bez żadnej etykiety są wtedy pomijane, a brakujące jednostki nie są błędem. Wiersze częściowo wypełnione, np. z samym `edit_about_sources`, nadal są sprawdzane. Arkusz z błędami nie jest importowany. Typowe komunikaty:

   | Komunikat | Co poprawić |
   |---|---|
   | `nieznane kody ['oficjalne']` | literówka albo kod spoza listy, także dawny polski kod z codebooka v1.0 |
   | `source_types brak wartości (wpisz none, gdy nie ma powołania)` | pusty wiersz: wpisz kody albo `none` |
   | `none razem z innymi kodami (…)` | usuń `none` albo pozostałe kody |
   | `edit_about_sources brak wartości` | wpisz 0 lub 1 |
   | `edit_about_sources ma wartość … zamiast 0 lub 1` albo to samo dla `uncertain` | wpisz 0 lub 1 |
   | `Wikipedia: nagłówki … różnią się od oczekiwanych …` | przywróć oryginalne nagłówki i kolejność kolumn |
   | `wikipedia: brak N jednostek z manifestu` lub `powtórzone unit_id` | usunięty albo zduplikowany wiersz: przywróć go z oryginalnego arkusza |
   | `kolumna annotator zawiera …` | przywróć oryginalną wartość w kolumnie `annotator` |

4. Gdy obie osoby są zaimportowane, koordynator uruchamia `make agreement`. Tabele zgodności (także dla `edit_about_sources`), lista niezgodności i wykres trafiają do `annotations/agreement/`.
5. Na sesji uzgadniania omawiamy niezgodności i ustalamy poprawki codebooka (v2.1).
6. Próbę główną kodujemy tak samo (`--phase gold`, `PHASE=gold`). Niezgodności rozstrzyga arbiter.

## 11. Czego nie robić

- Nie otwieraj stron Wikipedii, historii zmian, linków ani pliku CSV w trakcie kodowania. Nie czytaj treści artykułu (`new_content`).
- Nie porównuj etykiet z drugą osobą przed oddaniem arkusza.
- Nie zmieniaj `unit_id`, nagłówków ani kolejności wierszy i kolumn. Nie dodawaj i nie usuwaj wierszy ani kolumn, nie sortuj.
- Nie zostawiaj pustych pól `source_types` i `edit_about_sources` i nie łącz `none` z innymi kodami.
- Nie traktuj skrótów `[[WP:…]]` ani prefiksu `/* Przypisy */` jako źródła lub pracy nad przypisami (R9).
- Nie wpisuj etykiet do `data_samples/wikipedia_sample.csv` i nie zapisuj tego pliku w Excelu.
