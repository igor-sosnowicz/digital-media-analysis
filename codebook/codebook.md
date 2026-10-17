# Powoływanie się na źródła informacji: codebook v1.0

*2026-10-16 · wersja robocza przed pilotażem annotacji.*
Ten plik jest generowany z `codebook/codebook.yaml` (`make codebook`); nie edytuj go ręcznie.

## Konstrukt

Powołanie się na źródło to wskazanie przez autora, skąd pochodzi informacja albo na czym opiera on twierdzenie: link, nazwa źródła, ogólnikowe odwołanie („badania pokazują”) albo jawnie przywołane doświadczenie własne lub cudze. Kodujemy typ źródła, nie jego wiarygodność ani to, czy autor z nim się zgadza.

## Jednostki analizy

| Platforma | Jednostka | Tekst | Uwagi |
|---|---|---|---|
| reddit | post | tytuł, treść i link posta (kolumny `title`, `text` i `url`) | Pole `url` liczy się tylko wtedy, gdy prowadzi poza własny wątek posta (post z linkiem). Komentarzy pod postem nie ma w danych. Nie otwieramy linków: kategorię ustalamy z domeny i otaczającego tekstu. |
| wikipedia | opis zmiany jednej rewizji | pole `comment` rewizji | To krótki opis edycji wpisany przez redaktora albo wygenerowany przez narzędzie, a nie treść artykułu ani strona dyskusji. |

## Zmienne

### `cites_source`: Powołanie się na źródło

Platformy: reddit, wikipedia. Typ: binary.

**Pytanie:** Czy autor wskazuje, skąd pochodzi informacja lub na czym opiera twierdzenie?

- `1`: jest co najmniej jedno powołanie zgodne z definicją konstruktu i regułami
- `0`: brak powołania, także gdy występują tylko linki lub nazwy niebędące źródłem (R2, R3, R8, R9)

### `source_types`: Typy źródeł

Platformy: reddit, wikipedia. Typ: multilabel.

**Pytanie:** Jakiego typu źródła przywołuje autor? Zaznacz wszystkie występujące.

**Warunek:** cites_source = 1; przy cites_source = 0 pole zostaje puste

### `edit_about_sources`: Edycja dotyczy źródeł lub przypisów

Platformy: wikipedia. Typ: binary.

**Pytanie:** Czy opis zmiany deklaruje dodanie, usunięcie, wymianę lub poprawę źródeł albo przypisów?

- `1`: opis deklaruje pracę nad źródłami lub przypisami (w tym znacznik „źródła/przypisy”)
- `0`: brak takiej deklaracji; sam prefiks sekcji `/* Przypisy */` się nie liczy (R9)

## Kategorie `source_types`

### `media`: Media informacyjne i publicystyczne

Portale, gazety, telewizja, radio, agencje prasowe i magazyny publicystyczne.

**Włączamy:**
- link do artykułu lub materiału redakcji (wp.pl, onet.pl, gazeta.pl, money.pl, krytykapolityczna.pl, bbc.com)
- nazwa redakcji jako źródła („jak podaje TVN24”)
- porady językowe publikowane w prasie

**Wykluczamy:**
- media jako temat lub uczestnik zdarzenia („TVP zwolniła dziennikarza”)
- konto redakcji w serwisie społecznościowym bez linku do materiału redakcji (wtedy `platformy`)

**Przykłady pozytywne:**
- *(reddit)* Tytuł artykułu o wecie prezydenta i link do wiadomosci.gazeta.pl jako cała treść posta.
- *(wikipedia)* Poprawa błędu językowego, „por. np.” i link do felietonu w gazetawroclawska.pl.

**Przykłady negatywne:**
- *(reddit)* Post o tym, że ZUS konfiskuje oszczędności, z linkiem do wp.pl. **Dlaczego nie:** To jest `media`, a nie `oficjalne`. ZUS i ministerstwo są bohaterami tekstu, a wydawcą jest wp.pl (R4).

### `oficjalne`: Instytucje publiczne i oficjalne

Organy władzy i administracji, urzędy, agencje rządowe i samorządowe, organizacje międzynarodowe (WHO, ECDC) oraz dokumenty urzędowe.

**Włączamy:**
- link do domen gov.pl, who.int, ecdc.europa.eu, aids.gov.pl
- „według GUS”, „dane NFZ”, „komunikat policji”, treść ustawy

**Wykluczamy:**
- instytucja jako uczestnik zdarzenia („policja lata i pilnuje kibiców”, „Sejm uchwalił ustawę”)
- kontakt z urzędem opisany jako własne przeżycie (wtedy `osobiste`)

**Przykłady pozytywne:**
- *(wikipedia)* Usunięcie synonimów, bo „według tego źródła” nimi nie są, z linkiem do aids.gov.pl.
- *(wikipedia)* Objawy uzupełnione „według WHO”, z linkiem do strony pytań i odpowiedzi WHO.

**Przykłady negatywne:**
- *(reddit)* Zbiórka pomocy w odnalezieniu bliskiej osoby; w tekście słowo „bogusiem”. **Dlaczego nie:** Nie ma żadnej instytucji. Ciąg „gus” jest tylko fragmentem imienia.

### `nauka`: Nauka, badania i dane

Publikacje naukowe, uczelnie i instytuty, raporty badawcze, sondaże i zbiory danych ośrodków badawczych, biblioteki cyfrowe.

**Włączamy:**
- doi.org, pubmed, nature.com, repozytoria publikacji (academia.edu), biblioteki cyfrowe
- nazwany sondaż lub ośrodek badawczy („sondaż IBRiS”), tabela wyników sondaży
- „źródło uniwersyteckie” w opisie edycji

**Wykluczamy:**
- własne badanie autora, np. rekrutacja do ankiety (R8)
- osobista wizyta u lekarza (wtedy `osobiste`)
- ogólnik bez wskazania badania („badania pokazują”; wtedy `niesprecyzowane`)

**Przykłady pozytywne:**
- *(reddit)* Tabela ostatnich sondaży partyjnych z nazwami sondażowni, terminami i wielkością próby.
- *(wikipedia)* Cytat z publikacji o wprowadzeniu do medycyny wraz z linkiem do PDF w bibliotece cyfrowej.

**Przykłady negatywne:**
- *(reddit)* Studentka zbiera odpowiedzi do ankiety do pracy dyplomowej i podaje link do formularza. **Dlaczego nie:** To własne badanie autorki, nie powołanie się na badania (R8).
- *(reddit)* Opis wielu lat problemów zdrowotnych; „ostatni lekarz umocnił moje przypuszczenia”. **Dlaczego nie:** To relacja z osobistej konsultacji, więc `osobiste`, a nie publikacja czy instytucja badawcza.

### `encyklopedie`: Encyklopedie, słowniki i bazy wiedzy

Encyklopedie (w tym artykuły Wikipedii), słowniki, poradnie językowe słowników i bazy wiedzy.

**Włączamy:**
- link do artykułu Wikipedii, Wikidata, IMDb
- sjp.pwn.pl i poradnia językowa PWN
- linki objaśniające nazwy, np. nazwa partii podlinkowana do Wikipedii

**Wykluczamy:**
- skróty zasad i narzędzi Wikipedii w opisach edycji (`[[WP:SK]]`, `[[WP:POP]]`, `[[Pomoc:…]]`; R9)

**Przykłady pozytywne:**
- *(wikipedia)* „Brzydki rusycyzm” i link do poradni językowej sjp.pwn.pl.
- *(reddit)* Nazwy partii w tabeli sondaży podlinkowane do artykułów angielskiej Wikipedii.

**Przykłady negatywne:**
- *(wikipedia)* `[[WP:SK]], drobne techniczne` **Dlaczego nie:** To odnośnik do narzędzia porządkowania kodu (skrypt WP:SK), a nie źródło informacji (R9).

### `platformy`: Media społecznościowe i platformy treści użytkowników

YouTube, Facebook, X/Twitter, TikTok, Instagram, Wykop, Reddit, fora i podobne serwisy.

**Włączamy:**
- link do filmu, wpisu lub wątku udostępnionego jako informacja
- „widziałem na Twitterze, że…”, wpis polityka w serwisie społecznościowym

**Wykluczamy:**
- zdjęcia i filmy autora hostowane przez platformę (i.redd.it, preview.redd.it, v.redd.it, imgur; R3)
- nazwa serwisu w innym znaczeniu, np. kod rabatowy „reddit100”

**Przykłady pozytywne:**
- *(reddit)* Post z okazji rocznicy zaprzysiężenia prezydenta z linkiem do filmu na YouTube jako materiałem do dyskusji.

**Przykłady negatywne:**
- *(reddit)* Reklama perfumerii, której treścią jest tylko zdjęcie z preview.redd.it. **Dlaczego nie:** Zdjęcie jest własną treścią autora, a nie źródłem (R3).

### `komercyjne`: Źródła komercyjne

Sklepy, producenci, serwisy ogłoszeniowe i rezerwacyjne oraz strony firm użyte jako źródło informacji (cena, specyfikacja, opinie).

**Włączamy:**
- „według strony producenta rama waży 1,2 kg”
- link do oferty jako dowód ceny lub dostępności

**Wykluczamy:**
- serwis jako miejsce poszukiwań lub przedmiot pytania („poza OLX i Otodom szukam innych stron”; R2)
- reklama, link afiliacyjny, spam, kod rabatowy (R3)
- sklep jako miejsce zdarzenia („sklepy zamykały rolety”)

**Przykłady pozytywne:**
- *(reddit)* Konstruowany: „Na Allegro ten model kosztuje 300 zł, więc 500 zł to przesada” z linkiem do oferty.

**Przykłady negatywne:**
- *(reddit)* Pytanie po angielsku, czy poza OLX i Otodom są inne serwisy z mieszkaniami na krótki termin. **Dlaczego nie:** Serwisy są przedmiotem pytania, a nie źródłem informacji (R2).
- *(reddit)* Post kasyna online o bonusie powitalnym; link posta prowadzi do serwisu z promocjami hazardowymi. **Dlaczego nie:** Reklama lub spam (R3).

### `organizacje`: Organizacje pozarządowe, społeczne i polityczne

Fundacje, stowarzyszenia, NGO, związki zawodowe i partie polityczne jako wydawcy informacji.

**Włączamy:**
- link do strony fundacji lub NGO (wwf.pl, greenpeace.org)
- „raport fundacji X”, stanowisko partii opublikowane na jej stronie

**Wykluczamy:**
- organizacja jako temat lub uczestnik zdarzenia
- polityk pełniący funkcję państwową, który mówi w imieniu urzędu (wtedy `oficjalne`)

**Przykłady pozytywne:**
- *(wikipedia)* Link do strony WWF o klimacie z dopiskiem „inspiracja”.

**Przykłady negatywne:**
- *(reddit)* Post o rozłamie w partii z linkiem do artykułu wprost.pl. **Dlaczego nie:** Partia jest tematem, a wydawcą jest medium, więc `media` (R4).

### `osobiste`: Doświadczenie własne i relacje z drugiej ręki

Autor opiera twierdzenie na własnym doświadczeniu albo na relacji konkretnej osoby z otoczenia, w tym specjalisty spotkanego osobiście.

**Włączamy:**
- „z własnego doświadczenia”, „u mnie w pracy zawsze…” użyte jako dowód twierdzenia
- „znajomy pracuje w szpitalu i mówi, że…”, „lekarz powiedział mi, że…”

**Wykluczamy:**
- opis sytuacji bez funkcji dowodu („mieszkam w centrum, można odebrać”)
- osoby jako uczestnicy, np. szukanie znajomych czy prezent dla znajomego
- własna opinia („według mnie”, „moim zdaniem”; R8)

**Przykłady pozytywne:**
- *(reddit)* Opis wielu lat problemów zdrowotnych; „ostatni lekarz umocnił moje przypuszczenia”.

**Przykłady negatywne:**
- *(reddit)* Para szuka znajomych do wspólnego wychodzenia. **Dlaczego nie:** „znajomych” to cel posta, a nie źródło informacji.
- *(reddit)* „Mieszkam na wsi” i pytanie o lepszego dostawcę internetu. **Dlaczego nie:** Miejsce zamieszkania jest kontekstem, a nie dowodem.

### `niesprecyzowane`: Ogólnikowe powołanie bez wskazania źródła

Autor odwołuje się do źródła, którego nie da się zidentyfikować („badania pokazują”, „czytałem gdzieś”, „według ekspertów”, „wg źródła”).

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
- *(wikipedia)* „drobne redakcyjne, źródła/przypisy” **Dlaczego nie:** To znacznik typu edycji, a nie powołanie, więc edit_about_sources = 1 i cites_source = 0 (R10).
- *(wikipedia)* Bot: „poprawiam link tożsamy z tekstem linka” **Dlaczego nie:** Słowo „link” oznacza tu element techniczny strony.

### `inne`: Inne zidentyfikowane źródło

Źródło dające się zidentyfikować (nazwa lub link), które nie pasuje do żadnej z powyższych kategorii, np. prywatny blog.

**Włączamy:**
- link do prywatnego bloga lub strony hobbystycznej użytej jako źródło informacji

**Wykluczamy:**
- źródło pasujące do innej kategorii; `inne` stosujemy tylko w ostateczności
- strona będąca przedmiotem rozmowy, np. aplikacja polecana w poście (R2)

**Przykłady pozytywne:**
- *(reddit)* Konstruowany: „Trasę opisał autor bloga rowerowego X, tam są też wysokości przewyższeń” z linkiem do bloga.

**Przykłady negatywne:**
- *(reddit)* Pytanie o aplikacje do „zbierania kwadratów” z linkami do ich stron głównych. **Dlaczego nie:** Linki wskazują przedmiot rozmowy, a nie źródło informacji (R2).

## Reguły rozstrzygania

- **R1.** Etykietujemy całą jednostkę: post (tytuł, treść i link) albo opis zmiany. Przy `source_types` zaznacz każdą kategorię, która wystąpiła choć raz; liczba wystąpień nie ma znaczenia.
- **R2.** Powołanie wymaga funkcji źródła: tekst lub link musi wskazywać, skąd pochodzi informacja, albo podawać ją jako podstawę twierdzenia. Sama wzmianka o instytucji, osobie lub serwisie jako uczestniku zdarzenia albo przedmiocie rozmowy to nie powołanie.
- **R3.** Nie są źródłem: własne zdjęcia i filmy hostowane przez platformę (i.redd.it, preview.redd.it, v.redd.it, imgur), formularze ankiet, reklamy, linki afiliacyjne, spam, kody rabatowe i linki do profili użytkowników.
- **R4.** Kategorię wyznacza wydawca lub kanał, z którego pochodzi informacja, a nie temat ani osoby opisane w materiale. Artykuł wp.pl o decyzji ministerstwa to `media`. Gdy autor wymienia też źródło pierwotne przywołane w materiale („onet, powołując się na raport NIK”), zaznacz obie kategorie.
- **R5.** Konkret wygrywa z ogólnikiem. `niesprecyzowane` zaznaczamy tylko wtedy, gdy jakieś odwołanie w jednostce pozostaje nierozpoznawalne. Jeśli ten sam fragment wskazuje konkretne źródło, kodujemy jego kategorię.
- **R6.** Nie oceniamy wiarygodności. Tekst pseudonaukowy w repozytorium publikacji to nadal `nauka`, a artykuł z portalu o niskiej wiarygodności to nadal `media`.
- **R7.** Kategoria `inne` jest ostatecznością. Gdy domena jest nieznana, można sprawdzić, kto ją prowadzi, ale nie kodujemy treści strony docelowej.
- **R8.** Nie są powołaniem: własna opinia („według mnie”, „moim zdaniem”), prośba o źródło („macie jakieś dane?”) ani własne badanie autora (rekrutacja do ankiety).
- **R9.** Wikipedia, elementy techniczne. Pomijamy automatyczny prefiks sekcji `/* … */`. Skróty zasad i narzędzi (`[[WP:…]]`, `[[Pomoc:…]]`), opisy redakcyjne („drobne redakcyjne”, „int.”, „kat.”), komunikaty botów i rewerty („Wycofano edycje użytkownika…”, „Anulowanie wersji…”) nie są źródłem.
- **R10.** Wikipedia, praca nad przypisami. Deklaracja pracy nad źródłami (znacznik „źródła/przypisy”, „dodano przypis”, poprawa przypisów) daje `edit_about_sources = 1`. `cites_source = 1` dajemy tylko wtedy, gdy opis identyfikuje źródło albo jego typ („wg WHO”, „źródło uniwersyteckie”).
- **R11.** Wpisy po angielsku i w innych językach kodujemy według tych samych reguł.
- **R12.** W razie wątpliwości wybierz najlepszą etykietę, ustaw `uncertain = 1` i opisz problem w `notes`. Takie przypadki omawiamy przy uzgadnianiu etykiet i mogą one zmienić codebook.

## Arkusz annotacji

| Kolumna | Opis |
|---|---|
| `unit_id` | identyfikator jednostki (Reddit `id` posta; Wikipedia `strona#numer_rewizji`) |
| `annotator` | inicjały osoby annotującej |
| `cites_source` | 0 lub 1 |
| `source_types` | kody kategorii rozdzielone średnikiem, np. `media;nauka`; puste przy cites_source = 0 |
| `edit_about_sources` | 0 lub 1 (tylko Wikipedia; dla Reddita puste) |
| `uncertain` | 1, jeśli etykieta budzi wątpliwości (R12); w przeciwnym razie 0 |
| `notes` | uzasadnienie wątpliwości, numer reguły, propozycja zmiany codebooka |

## Historia zmian

- **1.0** (2026-10-16): Pierwsza wersja. Zastępuje dwa niezgodne schematy instrumentu v1 (Reddit: 7 kategorii plus „link/domena” i „sygnał powołania”; Wikipedia: 6 kategorii plus 3 kategorie pomocnicze) jednym zestawem 10 kategorii. Dodaje definicje, kryteria wykluczenia, przykłady z danych i reguły rozstrzygania. Wydziela zmienną `edit_about_sources` dla Wikipedii.
