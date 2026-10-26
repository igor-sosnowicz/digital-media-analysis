# Instrukcja annotacji: Reddit (`reddit_sample.csv`)

*Codebook v2.1 z 24.10.2026* (kategorie źródeł bez zmian od v2.0; stanowisko wobec konsensusu w punkcie 11). Ta instrukcja prowadzi krok po kroku przez kodowanie postów z Reddita. Pełne definicje kategorii i reguły R1–R14 są w [`codebook/codebook.md`](../codebook/codebook.md); gdy instrukcja i codebook się różnią, rozstrzyga codebook. Opisy zmian z Wikipedii kodujemy według osobnej instrukcji: [`instrukcja_annotacji_wikipedia.md`](instrukcja_annotacji_wikipedia.md).

## W skrócie

1. Kodujesz w arkuszu `annotations/sheets/<faza>_<inicjały>.xlsx`, w zakładce **Reddit**. Nie wpisujesz etykiet do pliku CSV.
2. Jednostka to cały post: tytuł, treść i link. Linków nie otwierasz.
3. W każdym wierszu wpisujesz `source_types`: kody źródeł rozdzielone średnikiem (np. `media;scientific`) albo `none`, gdy post nie powołuje się na żadne źródło.
4. Przy wątpliwościach ustawiasz `uncertain = 1` i krótko opisujesz problem w `notes`.
5. Kodujesz samodzielnie, do końca arkusza, a potem oddajesz plik koordynatorowi.

## 1. Plik `reddit_sample.csv` a arkusz annotacji

`data_samples/reddit_sample.csv` zawiera 500 postów wylosowanych do gold standardu: lata 2005–2020, po 31–32 posty na rok, z subredditów wymienionych w `config.yaml` (`reddit_subreddits`). To plik referencyjny z pełnymi danymi. Etykiety wpisujemy w arkuszu XLSX, który koordynator generuje z tej samej próby. Zakładka Reddit zawiera posty jednej fazy:

- **pilotaż:** 62 posty (`phase = pilot`), na kalibrację codebooka: najpierw 32 z pierwszej rundy (`split = pilot`), potem 30 z drugiej (`split = pilot2`). Druga runda pochodzi spoza 500 postów próby, więc plik CSV ma 530 wierszy;
- **próba główna:** 468 postów (`phase = gold`). Posty `dev` i `test` są wymieszane, więc nie wiadomo, które są testowe.

Dlaczego arkusz, a nie CSV:

- arkusz jest ślepy, czyli bez kolumn losowania i wyników instrumentu;
- ma ustaloną losową kolejność, listy 0/1 i podpowiedź z kodami;
- import (`make import-labels`) sprawdza go automatycznie.

Kolumny losowania z CSV (np. `stratum`, `weight`) nie mogą wpływać na etykietę, dlatego annotator ich nie widzi.

| Kolumna w CSV | Kolumna w arkuszu | Czy używasz przy kodowaniu? |
|---|---|---|
| `unit_id` (= `id` posta) | `unit_id` | identyfikator; nie zmieniaj go |
| `subreddit` | `subreddit` | tylko jako kontekst (np. r/science, r/warszawa) |
| `title` | `tytuł` | tak |
| `text` | `treść` | tak; często jest pusta (post z samym linkiem) |
| `url` | `link` | tak; puste, gdy post nie linkuje poza własny wątek (post tekstowy) |
| `permalink`, `score`, `num_comments`, `created_utc`, `created_at_utc`, `removed_by_category`, `day_weight` | (brak) | nie |
| `year`, `phase`, `split`, `order`, `stratum`, `signal`, `N_h`, `n_h`, `weight` | (brak) | nie: to kolumny losowania |

Czego się spodziewać w tej próbie:

- 442 z 500 postów to posty z linkiem, a 449 ma pustą treść. W większości przypadków kodujesz więc tytuł i domenę linku.
- Większość postów jest po angielsku (r/science, r/conspiracy, r/skeptic, r/reddit.com); 11 pochodzi z polskich subredditów. Oba języki kodujemy według tych samych reguł (R11).

## 2. Przygotowanie

**Koordynator** (osoba z lokalną kopią danych w `data/`):

1. Generuje arkusze pilotażu: `make pilot-sheets ANNOTATORS="JP IS"`. Bez `make`: `uv run scripts/03_export_annotation_sheets.py --phase pilot --annotators JP IS`. Powstają pliki `annotations/sheets/pilot_JP.xlsx` i `pilot_IS.xlsx`; jeden plik zawiera zakładki Reddit i Wikipedia.
2. Przekazuje każdej osobie jej plik poza gitem, np. na dysku zespołu. Arkusze zawierają treść postów, więc są w `.gitignore` i nie trafiają do repozytorium.
3. Po pilotażu i poprawkach codebooka (v2.1) generuje arkusze próby głównej: `uv run scripts/03_export_annotation_sheets.py --phase gold --annotators JP IS`.
4. Gdy próbę główną dzielicie między osoby, eksportuje tylko kolejne jednostki za ostatnim wierszem zakodowanym przez kogoś innego, np. `uv run scripts/03_export_annotation_sheets.py --phase gold --annotators JP --after annotations/sheets/gold_IS.xlsx --reddit 60 --wikipedia 130`. Arkusz ma te same zakładki i kolumny, ale tylko wybrane wiersze. Zgodność liczymy wtedy tylko na pilotażu, który obie osoby kodują w całości.

**Annotator:**

1. Czyta w całości `codebook/codebook.md`, a potem tę instrukcję.
2. Otwiera swój plik w Excelu albo w LibreOffice Calc. Nie konwertuje go do Arkuszy Google, bo giną listy rozwijane i zapisana w pliku wersja codebooka.
3. Trzyma pod ręką zakładkę „Instrukcja” z tabelą kodów.

## 3. Kolumny do wypełnienia (zakładka Reddit)

Wypełniasz żółte kolumny:

| Kolumna | Co wpisać | Wymagana? |
|---|---|---|
| `source_types` | kody z listy poniżej rozdzielone średnikiem, np. `media;scientific`; `none`, gdy nie ma powołania | tak, w każdym wierszu |
| `uncertain` | `0` lub `1` (lista rozwijana); puste pole liczy się jako 0 | nie |
| `notes` | krótki opis wątpliwości, numer reguły, proponowana zmiana codebooka | tak, gdy `uncertain = 1` |
| `annotator` | (wpisane już inicjały) | nie zmieniaj |

Dozwolone kody: `scientific`, `institutional`, `media`, `personal`, `social_blog`, `encyclopedia`, `other`, `unknown`, `none`. Kolejność kodów, wielkość liter i spacje nie mają znaczenia, a przecinek też działa jako separator.

W zakładce Reddit nie ma kolumny `cites_source`, bo wyliczamy ją z `source_types`: 0 przy `none`, 1 przy każdym innym kodzie (R13). Nie ma też `edit_about_sources`, bo ta zmienna dotyczy tylko Wikipedii.

## 4. Procedura dla jednego posta

**Krok 1. Przeczytaj tytuł, treść i link.** Z linku bierzesz domenę i ścieżkę (np. `nature.com/articles/…`, `youtube.com/watch?…`). Nie otwierasz go: kategorię ustalamy z domeny i otaczającego tekstu.

**Krok 2. Wypisz kandydatów na powołanie:**

- link posta i linki w treści;
- nazwy redakcji, instytucji, czasopism i serwisów;
- zwroty typu „according to”, „według”, „studies show”, „z mojego doświadczenia”.

**Krok 3. Odrzuć to, co nie jest źródłem:**

- własne zdjęcia i filmy hostowane przez platformę: `i.redd.it`, `v.redd.it`, `preview.redd.it`, `imgur.com` (R3);
- formularze ankiet, reklamy, linki afiliacyjne, spam, kody rabatowe i linki do profili użytkowników (R3);
- instytucję, osobę lub serwis występujące jako temat albo uczestnik zdarzenia, a nie jako źródło informacji (R2). Przykłady: „NASA launched a probe” bez wskazania, skąd ta wiadomość; strona aplikacji, o którą autor pyta;
- własną opinię („I think”, „moim zdaniem”), prośbę o źródło („any sources?”) i własne badanie autora, np. rekrutację do ankiety (R8).

**Krok 4. Każdemu pozostałemu powołaniu przypisz kategorię według wydawcy lub kanału (R4)**, korzystając ze ściągawki w punkcie 5.

- Post z linkiem, który udostępnia artykuł lub materiał jako informację, powołuje się na wydawcę tego materiału.
- Gdy post wymienia także źródło pierwotne (np. tytuł „…, study in PNAS finds” i link do portalu informacyjnego), zaznaczasz obie kategorie.

**Krok 5. Ogólniki.** Odwołanie, którego nie da się zidentyfikować („studies show”, „scientists say”, „czytałem gdzieś”), to `unknown`. Stosujesz go tylko wtedy, gdy w tym samym fragmencie nie ma konkretnego źródła (R5).

**Krok 6. Wpisz kody.** Każdy znaleziony kod wpisujesz raz; liczba wystąpień nie ma znaczenia (R1). Jeśli po kroku 3 nie zostało żadne powołanie, wpisujesz `none` bez innych kodów (R13).

**Krok 7. Oceń pewność.** Jeśli się wahasz, wybierasz najlepszą etykietę, ustawiasz `uncertain = 1` i piszesz w `notes`, czego dotyczy wątpliwość (punkt 8).

Nie oceniamy wiarygodności ani tego, czy autor ma rację (R6). Artykuł z rt.com to `media`, a tekst pseudonaukowy w repozytorium publikacji to `scientific`.

## 5. Kategorie na Reddicie: ściągawka

| Kod | Kiedy | Typowe domeny i zwroty w tej próbie |
|---|---|---|
| `scientific` | konkretna publikacja naukowa | `nature.com/articles/…`, `science.org` / `sciencemag.org`, `pnas.org`, `pubmed`, `doi.org`, `arxiv.org`; „study published in The Lancet” |
| `institutional` | instytucja naukowa, statystyczna albo zdrowia publicznego jako źródło (a nie konkretna publikacja) | `who.int`, `cdc.gov`, `nih.gov`, agencje badawcze (`nasa.gov`, `noaa.gov`), strony i komunikaty uczelni i instytutów, GUS, ośrodki badania opinii; „according to the WHO” |
| `media` | redakcje informacyjne i magazyny, także popularnonaukowe | `news.bbc.co.uk`, `nytimes.com`, `theguardian.com`, `cnn.com`, `foxnews.com`, `news.yahoo.com`, `msnbc.msn.com`, `phys.org`, `sciencedaily.com`, `livescience.com`, `news.nationalgeographic.com`, `sciam.com`, `the-scientist.com`, `rt.com`; polskie: onet.pl, wp.pl, gazeta.pl |
| `personal` | własne doświadczenie albo relacja konkretnej osoby, podane jako dowód twierdzenia | „as a nurse I see…”, „my doctor told me…”, „z własnego doświadczenia” |
| `social_blog` | media społecznościowe, platformy treści użytkowników i blogi | `youtube.com`, `youtu.be`, `twitter.com` / `x.com`, `facebook.com`, link do innego wątku Reddita (`reddit.com/r/…/comments/…`), `scienceblogs.com`, `blogspot.com`, `wordpress.com` |
| `encyclopedia` | encyklopedie, słowniki i bazy wiedzy | `wikipedia.org`, `britannica.com`, `imdb.com`, `sjp.pl` |
| `other` | zidentyfikowane źródło spoza powyższych: sklepy i firmy, urzędy i administracja, sądy i prawo, NGO i partie, inne strony | `amazon.com`, strony producentów, strony rządowe i samorządowe (poza agencjami z wiersza `institutional`), ustawy, strony fundacji, prywatna strona, która nie jest blogiem |
| `unknown` | odwołanie bez wskazania źródła | „studies show”, „research says”, „experts say”, „I read somewhere” |
| `none` | brak jakiegokolwiek powołania | post tekstowy z pytaniem lub opinią; post, którego treścią jest samo zdjęcie z `i.redd.it` |

Granice, które najczęściej sprawiają trudność:

- **Portal popularnonaukowy a publikacja.** Wydawcą artykułu na phys.org, sciencedaily.com czy livescience.com jest portal, więc kod to `media`, nawet jeśli tekst opisuje badanie. `scientific` dodajesz tylko wtedy, gdy post wskazuje konkretną publikację lub czasopismo (R4).
- **Czasopismo a jego dział informacyjny.** Link do artykułu naukowego (np. `nature.com/articles/…`) to `scientific`. Link do działu wiadomości tego samego wydawcy (np. ścieżka z `/news/`) to `media`. Jeśli adres tego nie rozstrzyga, wpisz `uncertain = 1`.
- **Strona rządowa.** Agencje naukowe, statystyczne i zdrowia publicznego to `institutional`. Urzędy, ministerstwa, parlament, sądy, policja i prawo to `other`.
- **Blog a strona prywatna.** Gdy po adresie widać blog (np. `blogspot`, `/blog/`), kod to `social_blog`. Inna prywatna lub firmowa strona to `other`. Blog redakcji informacyjnej to `media`.

## 6. Typowe sytuacje

| Sytuacja | `source_types` | Reguła |
|---|---|---|
| Tytuł artykułu i link do serwisu informacyjnego | `media` | R4 |
| Tytuł mówi o badaniu, link prowadzi do portalu popularnonaukowego | `media` | R4 |
| Jak wyżej, ale tytuł wymienia czasopismo lub badanie („…, study in PNAS”) | `media;scientific` | R4 |
| Link bezpośrednio do artykułu w czasopiśmie naukowym | `scientific` | |
| „According to the CDC…” i link do cnn.com | `institutional;media` | R4 |
| Link do filmu na YouTube jako materiał do dyskusji | `social_blog` | |
| Link do innego wątku Reddita (crosspost) | `social_blog` | |
| Treścią posta jest samo zdjęcie lub film z `i.redd.it`, `v.redd.it` albo `imgur.com` | `none` | R3 |
| Post tekstowy z pytaniem („Is it true that…?”) | `none` | R8 |
| Post tekstowy: „Studies show that…” bez wskazania badań | `unknown` | R5 |
| Link do strony produktu lub aplikacji, o którą autor pyta | `none` | R2 |
| „Według ZTM tramwaje nie jeżdżą…” (polski subreddit) | `other` | ZTM to jednostka administracji miejskiej |

## 7. Przykłady rozwiązane

Przykłady są uproszczone i nie pochodzą z arkusza; pokazują sposób rozumowania.

1. **r/science**, tytuł „Scientists find gene linked to longevity”, treść pusta, link `news.bbc.co.uk/2/hi/health/…`. **`media`**. Post udostępnia artykuł BBC jako informację, a wydawcą jest BBC (R4). Naukowcy w tytule to temat, a nie wskazane źródło.
2. **r/science**, tytuł „Calorie restriction extends lifespan in mice”, link `nature.com/articles/…`. **`scientific`**. Link prowadzi do konkretnej publikacji.
3. **r/science**, tytuł „New study in PNAS links air pollution to dementia”, link `phys.org/news/…`. **`media;scientific`**. Wydawcą jest portal, a tytuł wskazuje też źródło pierwotne (R4).
4. **r/science**, tytuł „According to the WHO, measles cases rose by 30%”, link `cnn.com/…`. **`institutional;media`**.
5. **r/conspiracy**, tytuł i link `youtube.com/watch?v=…`. **`social_blog`**.
6. **r/conspiracy**, post tekstowy: „They don't want you to know. Studies prove fluoride harms the brain.” **`unknown`**. „Studies prove” nie wskazuje żadnych badań (R5). Nie oceniamy, czy twierdzenie jest prawdziwe (R6).
7. **r/skeptic**, post tekstowy: „My aunt swears homeopathy cured her. How do I talk to her?” **`none`**. Ciocia jest kontekstem pytania, a nie dowodem twierdzenia autora, więc to nie jest `personal`.
8. **r/skeptic**, post tekstowy: „I've worked in an ER for ten years and full moons don't change anything.” **`personal`**. Autor opiera twierdzenie na własnym doświadczeniu.
9. **r/science**, tytuł „My kid's science fair volcano”, link `i.redd.it/…`. **`none`**. To własne zdjęcie autora (R3).
10. **r/PolskaPolityka**, tytuł artykułu i link `wiadomosci.gazeta.pl/…`. **`media`**.
11. **r/warszawa**, post tekstowy: „Jak dojechać nocą na lotnisko?” **`none`**.
12. **r/science**, tytuł „Why the hockey stick graph holds up”, link `scienceblogs.com/…`. **`social_blog`**. To sieć blogów naukowych, a nie redakcja.

## 8. Wątpliwości: `uncertain` i `notes`

Ustaw `uncertain = 1`, gdy:

- z domeny nie da się ustalić wydawcy albo jego rodzaju;
- przypadek leży na granicy kategorii (punkt 5);
- nie wiesz, czy link jest źródłem informacji, czy tematem rozmowy (R2).

W `notes` napisz krótko, na czym polega problem, z numerem reguły i alternatywnym kodem, np. „R4: phys.org czy komunikat uczelni? rozważam institutional”.

Etykietę wybierasz zawsze, także przy wątpliwościach; `source_types` nigdy nie zostaje puste (R12). Takie przypadki omawiamy na sesji uzgadniania i mogą one zmienić codebook.

## 9. Po zakończeniu

1. Sprawdź, czy każdy wiersz ma `source_types` i czy `none` nie występuje razem z innymi kodami.
2. Zapisz plik jako `.xlsx` pod tą samą nazwą (np. `pilot_JP.xlsx`) i oddaj go koordynatorowi poza gitem.
3. Koordynator kopiuje plik do `annotations/sheets/` i uruchamia `make import-labels`. Bez `make`: `uv run scripts/04_import_annotations.py --phase pilot`; z opcją `--check` skrypt tylko sprawdza arkusze. Gdy próba główna jest podzielona między osoby albo zakodowana tylko w części, import uruchamia z `--partial` (`make import-labels PHASE=gold PARTIAL=1`). Wiersze bez żadnej etykiety są wtedy pomijane, a brakujące jednostki nie są błędem. Wiersze częściowo wypełnione nadal są sprawdzane. Arkusz z błędami nie jest importowany. Typowe komunikaty:

   | Komunikat | Co poprawić |
   |---|---|
   | `nieznane kody ['medai']` | literówka albo kod spoza listy, także dawny polski kod (np. `oficjalne`) |
   | `source_types brak wartości (wpisz none, gdy nie ma powołania)` | pusty wiersz: wpisz kody albo `none` |
   | `none razem z innymi kodami (…)` | usuń `none` albo pozostałe kody |
   | `uncertain ma wartość … zamiast 0 lub 1` | wpisz 0 lub 1 |
   | `Reddit: nagłówki … różnią się od oczekiwanych …` | przywróć oryginalne nagłówki i kolejność kolumn |
   | `reddit: brak N jednostek z manifestu` lub `powtórzone unit_id` | usunięty albo zduplikowany wiersz: przywróć go z oryginalnego arkusza |
   | `kolumna annotator zawiera …` | przywróć oryginalną wartość w kolumnie `annotator` |

4. Gdy obie osoby są zaimportowane, koordynator uruchamia `make agreement`. Tabele zgodności, lista niezgodności i wykres trafiają do `annotations/agreement/`.
5. Na sesji uzgadniania omawiamy niezgodności i ustalamy poprawki codebooka (v2.1).
6. Próbę główną kodujemy tak samo (`--phase gold`, `PHASE=gold`). Niezgodności rozstrzyga arbiter.

## 10. Czego nie robić

- Nie otwieraj linków, nie szukaj postów na Reddicie i nie zaglądaj do komentarzy ani do pliku CSV w trakcie kodowania.
- Nie porównuj etykiet z drugą osobą przed oddaniem arkusza.
- Nie zmieniaj `unit_id`, nagłówków ani kolejności wierszy i kolumn. Nie dodawaj i nie usuwaj wierszy ani kolumn, nie sortuj.
- Nie zostawiaj pustego `source_types` i nie łącz `none` z innymi kodami.
- Nie oceniaj wiarygodności źródła ani tego, czy autor ma rację (R6).
- Nie wpisuj etykiet do `data_samples/reddit_sample.csv`.

## 11. Arkusz stanowiska: `consensus_stance` (codebook 2.1)

Stanowisko wobec konsensusu naukowego kodujemy w osobnym przebiegu, w arkuszu `annotations/sheets/stance_<faza>_<inicjały>.xlsx`. Arkusz ma te same posty i kolumny z treścią co zakładka Reddit, a do wypełnienia są w nim tylko `consensus_stance`, `uncertain` i `notes`. Źródeł w tym arkuszu nie kodujesz.

| Wartość | Kiedy |
|---|---|
| `supports` | autor ufa nauce lub naukowcom, broni ustaleń naukowych albo przedstawia je jako wiarygodne; także kpina z pseudonauki (typowa dla r/skeptic) |
| `challenges` | autor podważa konsensus naukowy, wyraża nieufność wobec naukowców lub instytucji naukowych albo promuje twierdzenie sprzeczne z ustaleniami nauki („szczepionki powodują autyzm”, „ocieplenie to oszustwo”); także ironia lub kpina wobec naukowców |
| `neutral` | post dotyczy nauki, naukowców lub twierdzenia naukowego, ale autor nie zajmuje stanowiska: samo przekazanie wiadomości o badaniu, pytanie |
| `not_applicable` | post nie dotyczy nauki, naukowców ani twierdzeń naukowych: polityka, technologia, rozrywka bez twierdzeń naukowych |

Krok po kroku (reguła R14):

1. **Czy post dotyczy nauki?** Chodzi o naukę, naukowców, badania albo twierdzenie, które nauka rozstrzyga (zdrowie, klimat, szczepionki, ewolucja). Jeśli nie, wpisz `not_applicable`.
2. **Czy autor zajmuje stanowisko?** Decyduje to, co pisze sam, albo jak przedstawia linkowany materiał w tytule. Tytuł artykułu przepisany bez komentarza to `neutral`.
3. **Jakie stanowisko?** Zaufanie lub obrona nauki to `supports`; podważanie, nieufność albo twierdzenia sprzeczne z nauką to `challenges`.
4. **Nie oceniamy, kto ma rację** (R6). Nie otwieramy linków.
5. Przy wątpliwościach: najlepsza wartość, `uncertain = 1` i krótki opis w `notes` (R12).

Przykłady (uproszczone):
- r/science, „New study finds bees can count”, link do phys.org → `neutral`;
- r/conspiracy, „They lied about vaccines from the start, wake up” → `challenges`;
- r/skeptic, „Homeopathy is just expensive water — again shown in a large trial” → `supports`;
- r/conspiracy, „The Fed is printing money again” → `not_applicable` (gospodarka, bez twierdzenia naukowego).

Sprawdzenie w trakcie i przed oddaniem, bez zapisywania czegokolwiek: `make check-stance PHASE=gold PARTIAL=1` (albo `PHASE=pilot`). Kolejne kroki po kodowaniu: [`h1a_kroki.md`](h1a_kroki.md).

**Podpowiedzi AI (od 26.10.2026).** Arkusze stanowiska mają wstępnie wypełnioną kolumnę `consensus_stance` i kolumny `ai_stance`, `ai_uncertain`, `ai_reason` oraz `verified`. Sprawdź każdy wiersz według kroków powyżej, popraw etykietę, jeśli się nie zgadzasz, i wpisz `verified = 1`. Kolumn `ai_*` nie zmieniaj. Import liczy tylko sprawdzone wiersze. Szczegóły: [`h1a_kroki.md`](h1a_kroki.md).

Import: `make import-stance PHASE=pilot` (albo `PHASE=gold`, z `PARTIAL=1` dla arkusza wypełnionego w części). Etykiety trafiają do `annotations/labels/<faza>/stance_<inicjały>.csv`. Po imporcie obu osób skrypt wypisuje zgodność (α Krippendorffa, κ Cohena) na wspólnych postach rundy `pilot2`.

