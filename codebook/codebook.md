# Powoływanie się na źródła informacji: codebook v2.1

*2026-10-24 · wersja robocza przed pilotażem annotacji.*
Ten plik jest generowany z `codebook/codebook.yaml` (`make codebook`); nie edytuj go ręcznie.

## Konstrukt

Powołanie się na źródło to wskazanie przez autora, skąd pochodzi informacja albo na czym opiera on twierdzenie: link, nazwa źródła, ogólnikowe odwołanie („badania pokazują”) albo jawnie przywołane doświadczenie własne lub cudze. Kodujemy typ źródła, nie jego wiarygodność ani to, czy autor z nim się zgadza.

## Jednostki analizy

| Platforma | Jednostka | Tekst | Uwagi |
|---|---|---|---|
| reddit | post | tytuł, treść i link posta (kolumny `title`, `text` i `url`) | Pole `url` liczy się tylko wtedy, gdy prowadzi poza własny wątek posta (post z linkiem). Komentarzy pod postem nie ma w danych. Nie otwieramy linków: kategorię ustalamy z domeny i otaczającego tekstu. |
| wikipedia | opis zmiany jednej rewizji | pole `comment` rewizji | To krótki opis edycji wpisany przez redaktora albo wygenerowany przez narzędzie, a nie treść artykułu ani strona dyskusji. |

## Zmienne

### `source_types`: Typy źródeł

Platformy: reddit, wikipedia. Typ: multilabel.

**Pytanie:** Jakiego typu źródła przywołuje autor? Zaznacz wszystkie występujące albo wpisz `none`, gdy jednostka nie zawiera powołania.

### `cites_source`: Powołanie się na źródło

Platformy: reddit, wikipedia. Typ: binary.

**Pytanie:** Czy autor wskazuje, skąd pochodzi informacja lub na czym opiera twierdzenie?

**Wyliczana** z `source_types`: 0, gdy `source_types = none`, w przeciwnym razie 1; nie wypełniamy jej w arkuszu (R13).

- `1`: jest co najmniej jedno powołanie zgodne z definicją konstruktu i regułami
- `0`: brak powołania, także gdy występują tylko linki lub nazwy niebędące źródłem (R2, R3, R8, R9)

### `edit_about_sources`: Edycja dotyczy źródeł lub przypisów

Platformy: wikipedia. Typ: binary.

**Pytanie:** Czy opis zmiany deklaruje dodanie, usunięcie, wymianę lub poprawę źródeł albo przypisów?

- `1`: opis deklaruje pracę nad źródłami lub przypisami (w tym znacznik „źródła/przypisy”)
- `0`: brak takiej deklaracji; sam prefiks sekcji `/* Przypisy */` się nie liczy (R9)

### `consensus_stance`: Stanowisko wobec konsensusu naukowego

Platformy: reddit. Typ: nominal.

**Pytanie:** Jaki stosunek do nauki, naukowców lub konsensusu naukowego wyraża autor posta (tytułem, treścią albo sposobem przedstawienia linkowanego materiału)?

- `supports`: autor ufa nauce lub naukowcom, broni ustaleń naukowych albo przedstawia je jako wiarygodne, także kpiąc z pseudonauki (R14)
- `challenges`: autor podważa konsensus naukowy, wyraża nieufność wobec naukowców lub instytucji naukowych albo promuje twierdzenie sprzeczne z ustaleniami nauki (np. „szczepionki powodują autyzm”, „ocieplenie to oszustwo”)
- `neutral`: post dotyczy nauki, naukowców lub twierdzenia naukowego, ale autor nie zajmuje stanowiska (samo przekazanie wiadomości, pytanie)
- `not_applicable`: post nie dotyczy nauki, naukowców ani twierdzeń naukowych

## Kategorie `source_types`

### `scientific`: Publikacje naukowe

Konkretne publikacje naukowe: artykuły w czasopismach, preprinty, monografie, podręczniki akademickie i raporty badawcze (np. Nature, PubMed, Science).

**Włączamy:**
- doi.org, pubmed, nature.com, science.org, arxiv.org, repozytoria publikacji (academia.edu), biblioteki cyfrowe
- tytuł lub cytat konkretnej publikacji, czasopismo jako źródło („według badania w The Lancet”)
- „źródło uniwersyteckie” w opisie edycji

**Wykluczamy:**
- instytucja naukowa lub statystyczna bez wskazania publikacji („dane GUS”, „według WHO”; wtedy `institutional`)
- własne badanie autora, np. rekrutacja do ankiety (R8)
- osobista wizyta u lekarza (wtedy `personal`)
- ogólnik bez wskazania badania („badania pokazują”; wtedy `unknown`)

**Przykłady pozytywne:**
- *(wikipedia)* Cytat z publikacji o wprowadzeniu do medycyny wraz z linkiem do PDF w bibliotece cyfrowej.
- *(reddit)* Konstruowany: tytuł badania jako tytuł posta i link do artykułu w nature.com.

**Przykłady negatywne:**
- *(reddit)* Studentka zbiera odpowiedzi do ankiety do pracy dyplomowej i podaje link do formularza. **Dlaczego nie:** To własne badanie autorki, nie powołanie się na badania (R8).
- *(reddit)* Opis wielu lat problemów zdrowotnych; „ostatni lekarz umocnił moje przypuszczenia”. **Dlaczego nie:** To relacja z osobistej konsultacji, więc `personal`, a nie publikacja.

### `institutional`: Instytucje naukowe i statystyczne

Instytucje, które wytwarzają lub udostępniają wiedzę naukową, dane statystyczne i zalecenia zdrowotne, gdy źródłem jest instytucja, a nie konkretna publikacja: urzędy statystyczne (GUS, Eurostat), organizacje i agencje zdrowia publicznego (WHO, ECDC, CDC, PZH), uczelnie, instytuty badawcze i ośrodki badania opinii.

**Włączamy:**
- link do who.int, ecdc.europa.eu, stat.gov.pl, aids.gov.pl albo strony uczelni lub instytutu
- „według GUS”, „dane WHO”, „zalecenia ECDC”
- nazwany sondaż lub ośrodek badawczy („sondaż IBRiS”), tabela wyników sondaży

**Wykluczamy:**
- urzędy i administracja publiczna, ministerstwa, samorządy, policja, sądy, parlament i akty prawne (wtedy `other`)
- konkretna publikacja naukowa (wtedy `scientific`)
- instytucja jako uczestnik zdarzenia, np. „WHO ogłosiło pandemię” w artykule portalu (liczy się wydawca; R4)

**Przykłady pozytywne:**
- *(wikipedia)* Usunięcie synonimów, bo „według tego źródła” nimi nie są, z linkiem do aids.gov.pl.
- *(wikipedia)* Objawy uzupełnione „według WHO”, z linkiem do strony pytań i odpowiedzi WHO.
- *(reddit)* Tabela ostatnich sondaży partyjnych z nazwami sondażowni, terminami i wielkością próby.

**Przykłady negatywne:**
- *(reddit)* Zbiórka pomocy w odnalezieniu bliskiej osoby; w tekście słowo „bogusiem”. **Dlaczego nie:** Nie ma żadnej instytucji. Ciąg „gus” jest tylko fragmentem imienia.
- *(reddit)* Konstruowany: „Według komunikatu urzędu miasta tramwaje nie jeżdżą do niedzieli”. **Dlaczego nie:** Urząd miasta to administracja, a nie instytucja naukowa ani statystyczna, więc `other`.

### `media`: Media informacyjne

Portale, gazety, telewizja, radio, agencje prasowe i magazyny publicystyczne (np. BBC, Reuters, Onet, WP).

**Włączamy:**
- link do artykułu lub materiału redakcji (wp.pl, onet.pl, gazeta.pl, money.pl, bbc.com, reuters.com)
- nazwa redakcji jako źródła („jak podaje TVN24”)
- porady językowe publikowane w prasie

**Wykluczamy:**
- media jako temat lub uczestnik zdarzenia („TVP zwolniła dziennikarza”)
- konto redakcji w serwisie społecznościowym bez linku do materiału redakcji (wtedy `social_blog`)
- blog prywatny lub na platformie blogowej (wtedy `social_blog`)

**Przykłady pozytywne:**
- *(reddit)* Tytuł artykułu o wecie prezydenta i link do wiadomosci.gazeta.pl jako cała treść posta.
- *(reddit)* Post o tym, że ZUS konfiskuje oszczędności, z linkiem do wp.pl (ZUS jest tematem, wydawcą jest wp.pl; R4).
- *(wikipedia)* Poprawa błędu językowego, „por. np.” i link do felietonu w gazetawroclawska.pl.

**Przykłady negatywne:**
- *(reddit)* Konstruowany: „TVP zwolniła dziennikarza, co o tym myślicie?” bez linku i bez powołania się na relację mediów. **Dlaczego nie:** Medium jest tematem posta, a nie źródłem informacji (R2).

### `personal`: Doświadczenia własne

Autor opiera twierdzenie na własnym doświadczeniu albo na relacji konkretnej osoby z otoczenia, w tym specjalisty spotkanego osobiście („Z własnego doświadczenia powiem, że…”).

**Włączamy:**
- „z własnego doświadczenia”, „u mnie w pracy zawsze…” użyte jako dowód twierdzenia
- „znajomy pracuje w szpitalu i mówi, że…”, „lekarz powiedział mi, że…”
- kontakt z urzędem opisany jako własne przeżycie

**Wykluczamy:**
- opis sytuacji bez funkcji dowodu („mieszkam w centrum, można odebrać”)
- osoby jako uczestnicy, np. szukanie znajomych czy prezent dla znajomego
- własna opinia („według mnie”, „moim zdaniem”; R8)

**Przykłady pozytywne:**
- *(reddit)* Opis wielu lat problemów zdrowotnych; „ostatni lekarz umocnił moje przypuszczenia”.

**Przykłady negatywne:**
- *(reddit)* Para szuka znajomych do wspólnego wychodzenia. **Dlaczego nie:** „znajomych” to cel posta, a nie źródło informacji.
- *(reddit)* „Mieszkam na wsi” i pytanie o lepszego dostawcę internetu. **Dlaczego nie:** Miejsce zamieszkania jest kontekstem, a nie dowodem.

### `social_blog`: Media społecznościowe, blogi

Serwisy społecznościowe i platformy treści użytkowników (Reddit, YouTube, Facebook, X/Twitter, TikTok, Instagram, Wykop, fora) oraz blogi, w tym prywatne i hobbystyczne.

**Włączamy:**
- link do filmu, wpisu lub wątku udostępnionego jako informacja
- „widziałem na Twitterze, że…”, wpis polityka w serwisie społecznościowym
- link do bloga użytego jako źródło informacji

**Wykluczamy:**
- zdjęcia i filmy autora hostowane przez platformę (i.redd.it, preview.redd.it, v.redd.it, imgur; R3)
- nazwa serwisu w innym znaczeniu, np. kod rabatowy „reddit100”
- blog redakcji medium informacyjnego (wtedy `media`)

**Przykłady pozytywne:**
- *(reddit)* Post z okazji rocznicy zaprzysiężenia prezydenta z linkiem do filmu na YouTube jako materiałem do dyskusji.
- *(reddit)* Konstruowany: „Trasę opisał autor bloga rowerowego X, tam są też wysokości przewyższeń” z linkiem do bloga.

**Przykłady negatywne:**
- *(reddit)* Reklama perfumerii, której treścią jest tylko zdjęcie z preview.redd.it. **Dlaczego nie:** Zdjęcie jest własną treścią autora, a nie źródłem (R3).

### `encyclopedia`: Encyklopedie, słowniki

Encyklopedie (w tym artykuły Wikipedii i Britannica), słowniki (np. Słownik Języka Polskiego, sjp.pl), poradnie językowe słowników i bazy wiedzy.

**Włączamy:**
- link do artykułu Wikipedii, Wikidata, Britannica, IMDb
- sjp.pl, sjp.pwn.pl i poradnia językowa PWN
- linki objaśniające nazwy, np. nazwa partii podlinkowana do Wikipedii

**Wykluczamy:**
- skróty zasad i narzędzi Wikipedii w opisach edycji (`[[WP:SK]]`, `[[WP:POP]]`, `[[Pomoc:…]]`; R9)

**Przykłady pozytywne:**
- *(wikipedia)* „Brzydki rusycyzm” i link do poradni językowej sjp.pwn.pl.
- *(reddit)* Nazwy partii w tabeli sondaży podlinkowane do artykułów angielskiej Wikipedii.

**Przykłady negatywne:**
- *(wikipedia)* `[[WP:SK]], drobne techniczne` **Dlaczego nie:** To odnośnik do narzędzia porządkowania kodu (skrypt WP:SK), a nie źródło informacji (R9).

### `other`: Inne źródła

Źródło dające się zidentyfikować (nazwa lub link), które nie pasuje do pozostałych kategorii: sklepy, producenci i strony firm, urzędy i administracja publiczna (ministerstwa, samorządy, policja, sądy, parlament, akty prawne), organizacje pozarządowe, społeczne i polityczne oraz inne strony.

**Włączamy:**
- „według strony producenta rama waży 1,2 kg”, link do oferty jako dowód ceny lub dostępności
- link do gov.pl lub strony urzędu, „komunikat policji”, treść ustawy
- link do strony fundacji, NGO lub partii (wwf.pl, greenpeace.org), „raport fundacji X”

**Wykluczamy:**
- źródło pasujące do innej kategorii; `other` stosujemy tylko w ostateczności (R7)
- serwis lub strona jako miejsce poszukiwań albo przedmiot rozmowy (R2)
- reklama, link afiliacyjny, spam, kod rabatowy (R3)
- instytucja lub sklep jako uczestnik albo miejsce zdarzenia („Sejm uchwalił ustawę”, „sklepy zamykały rolety”)

**Przykłady pozytywne:**
- *(reddit)* Konstruowany: „Na Allegro ten model kosztuje 300 zł, więc 500 zł to przesada” z linkiem do oferty.
- *(wikipedia)* Link do strony WWF o klimacie z dopiskiem „inspiracja”.
- *(reddit)* Konstruowany: „Według komunikatu urzędu miasta tramwaje nie jeżdżą do niedzieli”.

**Przykłady negatywne:**
- *(reddit)* Pytanie po angielsku, czy poza OLX i Otodom są inne serwisy z mieszkaniami na krótki termin. **Dlaczego nie:** Serwisy są przedmiotem pytania, a nie źródłem informacji (R2).
- *(reddit)* Post kasyna online o bonusie powitalnym; link posta prowadzi do serwisu z promocjami hazardowymi. **Dlaczego nie:** Reklama lub spam (R3).
- *(reddit)* Pytanie o aplikacje do „zbierania kwadratów” z linkami do ich stron głównych. **Dlaczego nie:** Linki wskazują przedmiot rozmowy, a nie źródło informacji (R2).
- *(reddit)* Post o rozłamie w partii z linkiem do artykułu wprost.pl. **Dlaczego nie:** Partia jest tematem, a wydawcą jest medium, więc `media` (R4).

### `unknown`: Nieokreślone

Autor odwołuje się do źródła, którego nie da się zidentyfikować („Badania pokazują, że…”, „czytałem gdzieś”, „według ekspertów”, „wg źródła”).

**Włączamy:**
- „takie badania zostały przeprowadzone” bez wskazania których
- „wg źródła” w opisie edycji bez nazwy lub linku

**Wykluczamy:**
- sam znacznik „źródła/przypisy” lub „dodano przypis” w opisie edycji (to `edit_about_sources`; R10)
- słowo „link” lub „artykuł” w innym znaczeniu („podeślijcie link partnerkom”, „poprawiam link”)
- własna opinia („według mnie”; R8)

**Przykłady pozytywne:**
- *(wikipedia)* Uwaga, że takie badania przeprowadzono, a korzyści leku są dyskusyjne; bez wskazania badań.
- *(wikipedia)* „wg źródła jeszcze kapusta”

**Przykłady negatywne:**
- *(wikipedia)* „drobne redakcyjne, źródła/przypisy” **Dlaczego nie:** To znacznik typu edycji, a nie powołanie, więc edit_about_sources = 1 i source_types = none (R10).
- *(wikipedia)* Bot: „poprawiam link tożsamy z tekstem linka” **Dlaczego nie:** Słowo „link” oznacza tu element techniczny strony.

### `none`: Brak

Brak odwołania do źródła: jednostka nie zawiera żadnego powołania zgodnego z definicją konstruktu i regułami. Kod `none` wpisujemy sam, bez innych kodów (R13).

**Włączamy:**
- tekst bez linków, nazw źródeł i odwołań
- linki i nazwy, które nie pełnią funkcji źródła (R2, R3, R8, R9), np. własne zdjęcie z i.redd.it
- opis edycji z samym znacznikiem „źródła/przypisy” (R10)

**Wykluczamy:**
- jakiekolwiek rozpoznane powołanie, także ogólnikowe (wtedy jego kategoria albo `unknown`)

**Przykłady pozytywne:**
- *(reddit)* Para szuka znajomych do wspólnego wychodzenia.
- *(wikipedia)* `[[WP:SK]], drobne techniczne`

**Przykłady negatywne:**
- *(wikipedia)* „wg źródła jeszcze kapusta” **Dlaczego nie:** To ogólnikowe powołanie, więc `unknown`, a nie `none` (R5).

## Reguły rozstrzygania

- **R1.** Etykietujemy całą jednostkę: post (tytuł, treść i link) albo opis zmiany. Przy `source_types` zaznacz każdą kategorię, która wystąpiła choć raz; liczba wystąpień nie ma znaczenia.
- **R2.** Powołanie wymaga funkcji źródła: tekst lub link musi wskazywać, skąd pochodzi informacja, albo podawać ją jako podstawę twierdzenia. Sama wzmianka o instytucji, osobie lub serwisie jako uczestniku zdarzenia albo przedmiocie rozmowy to nie powołanie.
- **R3.** Nie są źródłem: własne zdjęcia i filmy hostowane przez platformę (i.redd.it, preview.redd.it, v.redd.it, imgur), formularze ankiet, reklamy, linki afiliacyjne, spam, kody rabatowe i linki do profili użytkowników.
- **R4.** Kategorię wyznacza wydawca lub kanał, z którego pochodzi informacja, a nie temat ani osoby opisane w materiale. Artykuł wp.pl o decyzji ministerstwa to `media`. Gdy autor wymienia też źródło pierwotne przywołane w materiale („onet, powołując się na raport GUS”), zaznacz obie kategorie.
- **R5.** Konkret wygrywa z ogólnikiem. `unknown` zaznaczamy tylko wtedy, gdy jakieś odwołanie w jednostce pozostaje nierozpoznawalne. Jeśli ten sam fragment wskazuje konkretne źródło, kodujemy jego kategorię.
- **R6.** Nie oceniamy wiarygodności. Tekst pseudonaukowy w repozytorium publikacji to nadal `scientific`, a artykuł z portalu o niskiej wiarygodności to nadal `media`.
- **R7.** Kategoria `other` jest ostatecznością. Gdy domena jest nieznana, można sprawdzić, kto ją prowadzi, ale nie kodujemy treści strony docelowej.
- **R8.** Nie są powołaniem: własna opinia („według mnie”, „moim zdaniem”), prośba o źródło („macie jakieś dane?”) ani własne badanie autora (rekrutacja do ankiety).
- **R9.** Wikipedia, elementy techniczne. Pomijamy automatyczny prefiks sekcji `/* … */`. Skróty zasad i narzędzi (`[[WP:…]]`, `[[Pomoc:…]]`), opisy redakcyjne („drobne redakcyjne”, „int.”, „kat.”), komunikaty botów i rewerty („Wycofano edycje użytkownika…”, „Anulowanie wersji…”) nie są źródłem.
- **R10.** Wikipedia, praca nad przypisami. Deklaracja pracy nad źródłami (znacznik „źródła/przypisy”, „dodano przypis”, poprawa przypisów) daje `edit_about_sources = 1`. Kategorię źródła zamiast `none` dajemy tylko wtedy, gdy opis identyfikuje źródło albo jego typ („wg WHO”, „źródło uniwersyteckie”).
- **R11.** Wpisy po angielsku i w innych językach kodujemy według tych samych reguł.
- **R12.** W razie wątpliwości wybierz najlepszą etykietę, ustaw `uncertain = 1` i opisz problem w `notes`. Takie przypadki omawiamy przy uzgadnianiu etykiet i mogą one zmienić codebook.
- **R13.** `source_types` wypełniamy zawsze. `none` wpisujemy wtedy i tylko wtedy, gdy jednostka nie zawiera żadnego powołania, i nie łączymy go z innymi kodami. `cites_source` nie jest kodowane w arkuszu: wynosi 0 przy `none` i 1 przy każdej innej etykiecie.
- **R14.** `consensus_stance` kodujemy tylko na Reddicie, w osobnym arkuszu stanowiska (`stance_*.xlsx`). Podstawą jest to, co autor pisze sam albo jak przedstawia linkowany materiał w tytule; nie otwieramy linków i nie oceniamy, kto ma rację (R6). Artykuł o badaniu udostępniony bez komentarza to `neutral`. Ironia lub kpina wobec naukowców albo nauki to `challenges`, a kpina z pseudonauki (typowa dla r/skeptic) to `supports`. Post bez związku z nauką (polityka, technologia, rozrywka bez twierdzeń naukowych) to `not_applicable`.

## Arkusz annotacji

| Kolumna | Opis |
|---|---|
| `unit_id` | identyfikator jednostki (Reddit `id` posta; Wikipedia `strona#numer_rewizji`) |
| `annotator` | inicjały osoby annotującej |
| `source_types` | kody kategorii rozdzielone średnikiem, np. `media;scientific`; `none`, gdy nie ma powołania (R13) |
| `edit_about_sources` | 0 lub 1 (tylko Wikipedia; dla Reddita puste) |
| `consensus_stance` | supports, challenges, neutral albo not_applicable (tylko Reddit, w arkuszu stanowiska `stance_*.xlsx`; R14) |
| `uncertain` | 1, jeśli etykieta budzi wątpliwości (R12); w przeciwnym razie 0 |
| `notes` | uzasadnienie wątpliwości, numer reguły, propozycja zmiany codebooka |

## Historia zmian

- **1.0** (2026-10-16): Pierwsza wersja. Zastępuje dwa niezgodne schematy instrumentu v1 (Reddit: 7 kategorii plus „link/domena” i „sygnał powołania”; Wikipedia: 6 kategorii plus 3 kategorie pomocnicze) jednym zestawem 10 kategorii. Dodaje definicje, kryteria wykluczenia, przykłady z danych i reguły rozstrzygania. Wydziela zmienną `edit_about_sources` dla Wikipedii.
- **2.0** (2026-10-18): Kategorie i kody zgodne ze slajdem „Codebook”: dziewięć angielskich kodów (`scientific`, `institutional`, `media`, `personal`, `social_blog`, `encyclopedia`, `other`, `unknown`, `none`) zamiast dziesięciu polskich. `nauka` dzieli się na `scientific` (publikacje) i `institutional` (uczelnie, instytuty, sondażownie); `oficjalne` na `institutional` (instytucje statystyczne i zdrowia publicznego) i `other` (urzędy, administracja, prawo). `komercyjne`, `organizacje` i `inne` łączą się w `other`, z wyjątkiem blogów, które trafiają do `social_blog`. Nowy kod `none` zastępuje puste `source_types`, a `cites_source` jest wyliczane z `source_types` (R13).
- **2.1** (2026-10-24): Nowa zmienna `consensus_stance` (stanowisko wobec konsensusu naukowego: `supports`, `challenges`, `neutral`, `not_applicable`) dla postów z Reddita, kodowana w osobnym arkuszu stanowiska, do weryfikacji hipotezy o spadku zaufania do konsensusu naukowego w latach 2005–2018 (R14). Kategorie i zmienne z wersji 2.0 bez zmian.
