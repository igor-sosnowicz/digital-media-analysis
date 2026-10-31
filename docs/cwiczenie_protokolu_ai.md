# Ćwiczenie protokołu anotacji AI (A1): przebiegi A i B, 31.10.2026

Status: ćwiczenie eksploracyjne na danych v1. Nie zmienia wyników v1 ani preregistracji. Protokół: `docs/protokol_anotacji_ai.md` (wersja 1). Plan, z którego wynika ćwiczenie: `docs/propozycja_poprawy_eksperymentu.md` (rozdz. 4 i 8).

## W skrócie

- **Protokół działa i jest odtwarzalny.**
  - Skrypt `scripts/26_ai_protocol.py` odtwarza ślepą partię i klucz bajt w bajt.
  - Codebook i protokół w obu przebiegach mają te same sumy kontrolne co w chwili zamrożenia.
- **Stabilność (K1) spełniona z dużym zapasem.**
  - Wyniki: κ `cites_source` 0,96, α (MASI) `source_types` 0,95, κ `edit_about_sources` 0,95. Dolne granice przedziałów wynoszą co najmniej 0,875.
  - Przebiegi różnią się w 11 z 253 jednostek, a przebieg B oznaczył wszystkie 11 jako niepewne.
- **Przebieg B, czyli nowy agent bez rozmowy tej sesji, powtarza wyniki przebiegu A wobec IS.**
  - Reddit: F1 `cites_source` 0,94 i MASI 0,61 (A: 0,93 i 0,62).
  - Wikipedia: F1 0,32 (A: 0,29) i ten sam wzorzec rozbieżności (27 z 28 jednostek).
  - Kontekst sesji A nie wpłynął więc na jej etykiety, przynajmniej w ujęciu łącznym.
- **Stabilność to jeszcze nie trafność.**
  - Oba przebiegi wykonał ten sam model. AI zgadza się samo ze sobą (κ 0,96), a z IS słabo (κ `cites_source` 0,12–0,24).
  - Rozbieżność z IS jest systematyczna. Na Wikipedii dotyczy kodu `personal` przy opiniach w opisach zmian, interwiki i rewertów. Część tych przypadków codebook rozstrzyga (R8, R9), części nie rozstrzyga.
- **Porównanie z instrumentami.**
  - Przy typach źródeł AI zgadza się z IS lepiej niż każdy instrument. MASI na Reddicie, na tych samych jednostkach: 0,62–0,65 wobec najwyżej 0,40.
  - Przy samym `cites_source` na Reddicie GLiNER jest nieco lepszy (F1 0,97 wobec 0,92–0,93).
- **K2 (niezależność błędów).**
  - Na Wikipedii K2 nie jest spełnione dla GLiNER ani dla reguł v1 w żadnym przebiegu.
  - Na Reddicie wynik dla GLiNER się odwraca (A: spełnione, B: nie). GLiNER ma tam tylko 4 błędy `cites_source`, a przy tak małych liczbach κ błędów jest niestabilne.
- **Kontrola z 27.10 zawyża zgodność AI z IS przy źródłach.**
  - Kontrola dała około 95% przy n = 22 i ten wynik cytuje ramka w preprincie.
  - Aż 16 z tych 22 postów pochodzi z konsensusu pilotażu, czyli z jednostek, w których etykiety IS zgadzały się z wcześniejszymi etykietami AI.
  - Na wszystkich 98 postach IS identyczny zbiór typów ma 0,59–0,60 postów.

## Przebiegi

| | Przebieg A | Przebieg B |
|---|---|---|
| Anotator | Claude Opus 5.5 w sesji Claude Code, która przygotowała protokół | Nowy agent (`claude-opus-5-5`) uruchomiony z tej sesji, bez jej rozmowy |
| Materiały | Ślepa partia z repozytorium | Tylko kopie codebooka, protokołu i `blind_B.csv` w osobnym folderze |
| Kody i kolejność | Ziarno 20261031 | Ziarno 20261032 |
| Zamrożenie partii (przed kodowaniem) | 06:53:55 UTC | 07:13:41 UTC |
| Etykiety | sha256 `3c70dd67…` | sha256 `3a766c72…`, zapisane o 07:31 UTC |
| `uncertain = 1` | 47 jednostek (18,6%) | 59 jednostek (23,3%) |

**Wspólne dla obu przebiegów**
- Jednostki: 253 zakodowane przez IS bez AI. Reddit 98, Wikipedia 155 (pilotaż 53, gold 200).
- Pliki zamrożone: codebook v2.2 (sha256 `6d22b1cd…`) i protokół v1 (sha256 `002600b5…`).
- Pola jak w arkuszach. Reddit: subreddit, tytuł, treść, link. Wikipedia: strona i opis zmiany.
- Klucz otwarty dopiero po zamrożeniu etykiet. Po zamrożeniu etykiet nie zmieniano.
- Miary są nieważone i liczone na jednostkach pilotażu i gold, a nie na losowej próbie populacji.

**Kontrola przebiegu B**
- Klucz B leżał na czas kodowania poza repozytorium.
- Zapis pracy agenta zawiera:
  - 5 odczytów, wyłącznie trzech udostępnionych plików;
  - 1 zapis etykiet;
  - 1 skrypt sprawdzający format.
- Agent nie korzystał z internetu ani z gita. Etykiety wpisał bezpośrednio, a nie programem.
- Harness dołączył do kontekstu agenta trzy rzeczy, których agent nie otwierał i które nie zawierają etykiet tych jednostek:
  - indeks pamięci projektu: 7 jednozdaniowych notatek, np. o wcześniejszych preanotacjach AI;
  - stan gita, czyli same nazwy plików;
  - tytuły ostatnich commitów.

## Stabilność (K1): przebieg B a przebieg A

| Miara | n | wartość | 95% CI (bootstrap) | K1 (≥ 0,8) |
|---|---|---|---|---|
| κ `cites_source` | 253 | 0,96 | 0,92–0,99 | tak |
| α Krippendorffa (MASI) `source_types` | 253 | 0,95 | 0,91–0,98 | tak |
| κ `edit_about_sources` | 155 | 0,95 | 0,88–1,00 | tak |

Miary i próg ustalono w skrypcie przed obejrzeniem etykiet B.

- **Według platform.**
  - Reddit: α 0,92 (0,85–0,97), identyczny zbiór typów w 0,93 postów.
  - Wikipedia: α 0,89 (0,66–1,00), identyczny zbiór w 0,99 edycji. Szeroki przedział wynika z małej liczby edycji ze źródłem.
- **κ według kategorii.**
  - `scientific`, `institutional`, `encyclopedia`: 1,00.
  - `social_blog`: 0,99. `media`: 0,95. `unknown`: 0,91.
  - `other`: 0,59.
  - `personal`: 0,00, bo jedna jednostka w B i żadna w A.
- **Gdzie przebiegi się różnią** (`disagreements_B_vs_A.csv`): 11 jednostek.
  - Reddit, 7 postów: głównie `other` albo `none` przy linku do strony produktu lub organizacji, która jest przedmiotem rozmowy (R2), oraz `media` albo `social_blog`.
  - Wikipedia, 4 edycje: 2 różnią się typem, 2 tylko `edit_about_sources`.
  - Przebieg B oznaczył wszystkie 11 jednostek jako niepewne, przebieg A 9 z 11.

## Zgodność z IS

| Platforma | Przebieg | n | zgodność `cites_source` | κ | F1 | identyczny zbiór typów | MASI |
|---|---|---|---|---|---|---|---|
| Reddit | A | 98 | 0,88 | 0,22 | 0,93 | 0,60 | 0,62 |
| Reddit | B | 98 | 0,89 | 0,12 | 0,94 | 0,59 | 0,61 |
| Wikipedia | A | 155 | 0,81 | 0,22 | 0,29 | 0,79 | 0,79 |
| Wikipedia | B | 155 | 0,81 | 0,24 | 0,32 | 0,79 | 0,79 |

- `edit_about_sources` (Wikipedia, n = 155):
  - przebieg A: zgodność 0,79, κ 0,40, F1 0,52;
  - przebieg B: zgodność 0,77, κ 0,36, F1 0,49.
- κ dla `cites_source` jest niskie przy wysokiej zgodności, bo jedna klasa jest rzadka: na Reddicie brak powołania, na Wikipedii powołanie.

| Kod | jednostki IS | jednostki A | jednostki B | κ z IS: A / B |
|---|---|---|---|---|
| `scientific` | 6 | 7 | 7 | 0,61 / 0,61 |
| `institutional` | 7 | 7 | 7 | 0,41 / 0,41 |
| `media` | 39 | 32 | 33 | 0,72 / 0,71 |
| `personal` | 22 | 0 | 1 | 0,00 / −0,01 |
| `social_blog` | 36 | 39 | 40 | 0,70 / 0,69 |
| `encyclopedia` | 9 | 3 | 3 | 0,49 / 0,49 |
| `other` | 14 | 4 | 6 | 0,20 / 0,28 |
| `unknown` | 2 | 5 | 6 | 0,28 / 0,24 |

### Gdzie są rozbieżności

Pełne listy są w `annotations/ai_protocol/disagreements_A.csv` i `disagreements_B.csv`.

Przypisanie reguł w poniższych tabelach to odczytanie anotatora AI, czyli strony ocenianej. Zespół powinien je potwierdzić.

**Wikipedia, `cites_source`.** W 28 jednostkach (przebieg A) IS widzi powołanie, a AI nie. Przebieg B pomija 27 z nich, w tym ten sam układ etykiet IS.

| IS | A / B | przykłady opisów zmian | co mówi codebook |
|---|---|---|---|
| `personal` | 14 / 14 | „Ściema”, „prawda o coid 19”, „poprawiono literówkę”, „Aktualizacja wykresu.” | `personal` to własne doświadczenie podane jako dowód. Własna opinia nie jest powołaniem (R8). Wskazanie: `none`. |
| `encyclopedia` | 6 / 6 | „interwiki”, „poprawiam linki interwiki”, automatyczny opis narzędzia „dodaj link” | Nierozstrzygnięte. `encyclopedia` obejmuje link do artykułu Wikipedii, ale R9 wyłącza elementy techniczne. |
| `other` | 5 / 5 | „link”, „/* Linki zewnętrzne */”, rewert „Wycofano edycje…” | Rewerty i sam prefiks sekcji nie są źródłem (R9). |
| `institutional` | 2 / 2 | rewert z uzasadnieniem „zmiany w artykułach muszą mieć oparcie w opublikowanych źródłach”; nowa nazwa uczelni | Rewert (R9). Instytucja jako przedmiot zmiany, a nie źródło (R2). |
| `media` | 1 / 0 | ilustracja: artykuł z nowozelandzkiej gazety z 1912 r. | Przebieg A dał `none`, a przebieg B `media`, jak IS. Obie etykiety oznaczono jako niepewne. |

Reguły R2, R3, R8 i R9 są w codebooku od wersji 1.0 (commit `5c663ac`, 17.10.2026). Etykiety IS powstały według wersji 2.0.

**Reddit, typy źródeł.** Przebieg A ma 39 sporów, przebieg B 40, ze zbliżonym układem:

| Wzorzec (przebieg A) | n | przykłady | uwagi |
|---|---|---|---|
| `media` czy `social_blog` przy nieznanej domenie | 9 | treehugger.com, heresyclub.com, bootsnall.com | R7 pozwala sprawdzić, kto prowadzi domenę. Protokół zabrania otwierania linków, więc AI ocenia tylko po nazwie domeny. |
| reklama, spam, własne zdjęcie (AI: `none`) | 8 | strona producenta farb, firma od rozliczeń medycznych, imgur | R3: reklama i spam nie są źródłem. W etykietach IS jest typ linkowanej strony. |
| `personal` | 8 | „All my pro Donald comments won't post…” | AI prawie nie używa `personal` (A: 0, B: 1 na 253 jednostki). Część tych przypadków to prawdopodobnie błędy AI. |
| inne granice kategorii | 14 | sciam.com (`media` czy `institutional`), wiadomości nature.com (`scientific` czy `media`), strona uczelni (`institutional` czy `scientific`) | |

### Flaga `uncertain`

- **Reddit.** Oznaczone posty skupiają większość sporów z IS:

  | Przebieg | oznaczone posty | spory o typy w oznaczonych | identyczny zbiór: oznaczone / pozostałe |
  |---|---|---|---|
  | A | 29 (30%) | 22 z 39 (56%) | 0,24 / 0,75 |
  | B | 37 (38%) | 26 z 40 (65%) | 0,30 / 0,77 |

- **Wikipedia.** Flaga nie wychwytuje różnic systematycznych: oznaczone są tylko 6 (A) i 5 (B) z 32 sporów o typy.
- **Różnice między przebiegami.** Flaga obejmuje też prawie całą niestabilność między przebiegami (zob. wyżej).

### Wcześniejsze etykiety Claude

| Porównanie | n | identyczny zbiór typów: A / B |
|---|---|---|
| Wcześniejsze etykiety Claude z pilotażu (`labels/pilot/JP.csv`, zatwierdzone przez JP 23.10) | Reddit 32, Wikipedia 21 | 0,91 i 1,00 / 0,94 i 1,00 |
| IS a te same etykiety Claude | Reddit 32, Wikipedia 21 | 0,50 i 0,86 (bez AI z tego ćwiczenia) |
| Ślepe kodowanie AI z 27.10 | 22 posty | 0,91 / 1,00 |

## Instrumenty i niezależność błędów (N6)

Porównanie obejmuje jednostki, dla których instrumenty mają predykcje (`dev` i `test`): Reddit 66, Wikipedia 134.

| Platforma | Miara | AI A | AI B | GLiNER v1 | zero-shot v1 | reguły v1 |
|---|---|---|---|---|---|---|
| Reddit | F1 `cites_source` | 0,92 | 0,93 | 0,97 | 0,93 | 0,06 |
| Reddit | MASI typów | 0,65 | 0,62 | 0,40 | 0,32 | 0,04 |
| Wikipedia | F1 `cites_source` | 0,31 | 0,34 | 0,17 | 0,26 | 0,24 |
| Wikipedia | MASI typów | 0,78 | 0,78 | 0,77 | 0,51 | 0,56 |

| Instrument | Platforma | κ błędów `cites`: A / B | κ błędów typów: A / B | K2 (< 0,4): A / B |
|---|---|---|---|---|
| GLiNER v1 | Reddit | 0,24 / 0,46 | 0,30 / 0,35 | tak / nie |
| GLiNER v1 | Wikipedia | 0,84 / 0,80 | 0,87 / 0,83 | nie / nie |
| zero-shot v1 | Reddit | 0,10 / 0,12 | 0,22 / 0,20 | tak / tak |
| zero-shot v1 | Wikipedia | 0,18 / 0,18 | 0,35 / 0,35 | tak / tak |
| reguły v1 | Reddit | 0,02 / −0,02 | 0,04 / −0,01 | tak / tak |
| reguły v1 | Wikipedia | 0,41 / 0,44 | 0,49 / 0,49 | nie / nie |

- **Wikipedia.** 27 (A) i 26 (B) z 29 błędów typów AI to także błędy GLiNER.
  - Oba systemy dają `none` przy większości opisów zmian. Dodatnie etykiety IS to głównie przypadki z tabeli wyżej.
  - Przy jednym kodującym człowieku nie da się oddzielić wspólnej ślepej plamki maszyn od odczytania IS, które odbiega od codebooka.
- **Reddit.** Odwrócenie wyniku K2 dla GLiNER opiera się na bardzo małych liczbach: GLiNER ma 4 błędy `cites_source`, a AI 9 (A) i 8 (B). κ wskaźników błędu przy kilku błędach nie jest wiarygodne.

## Kryteria z planu

- **K1, stabilność** (κ przebiegów A i B ≥ 0,8): spełnione we wszystkich trzech miarach.
- **K1, progi jakości** (F1 ≥ 0,8 i MASI ≥ 0,5): w planie dotyczą modelu etykiet A2. Tu stosujemy je poglądowo do jednego anotatora.
  - Reddit: spełnione w obu przebiegach (A: 0,93 i 0,62; B: 0,94 i 0,61).
  - Wikipedia: F1 niespełnione (0,29 i 0,32). MASI spełnione (0,79), ale głównie dlatego, że większość jednostek to `none` u obu stron.
- **K2** (κ błędów < 0,4):
  - zero-shot: spełnione na obu platformach w obu przebiegach;
  - reguły v1: spełnione na Reddicie, niespełnione na Wikipedii;
  - GLiNER: na Wikipedii niespełnione, na Reddicie wynik niestabilny (A: tak, B: nie).

## Wnioski dla planu bez nowej ręcznej anotacji

1. **Reddit.** K1 jest spełnione w całości (stabilność i progi jakości), więc etykiety AI mogą zastąpić ręczne kodowanie źródeł.
   - Przewaga AI nad instrumentami dotyczy typów źródeł (MASI 0,62–0,65 wobec najwyżej 0,40 na tych samych jednostkach). Przy samym `cites_source` GLiNER jest równie dobry.
2. **Wikipedia.** Etykiety AI są stabilne, ale systematycznie inne niż etykiety IS.
   - Zanim ich użyjemy, zespół musi rozstrzygnąć szare strefy codebooka (lista w „Następnych krokach”). To decyzja o regułach, a nie ponowna anotacja.
   - Potem nowy przebieg całości według codebooka 2.3 i protokołu 1.1.
3. **Ocena instrumentów na Wikipedii.** Etykiety AI nie mogą być jedynym odniesieniem dla GLiNER i reguł v1, bo K2 nie jest spełnione w żadnym przebiegu. Potrzebne jest źródło innej rodziny (N5).
4. **K2 w v2.** Kryterium warto zapisać w preregistracji v2 z minimalną liczbą błędów, np. co najmniej 10 błędów każdego systemu na platformie. Bez tego κ błędów bywa przypadkowe. To propozycja na v2, niestosowana wstecz do v1.
5. **Opcja z udziałem człowieka.** Jeśli zespół dopuści niewielki wkład ręczny, na Reddicie wystarczy przejrzeć posty z flagą `uncertain`. To 30–38% jednostek, które obejmują 56–65% sporów z IS i prawie całą niestabilność między przebiegami. To opcja, nie wymóg.
6. **Preprint.** Ramka walidacji (`report/preprint.tex`, wiersz 253) cytuje kontrolę z 27.10 (n = 22). Trzeba dodać zastrzeżenie o doborze tej próby albo podać wynik na 253 jednostkach.

## Ograniczenia

- **Ten sam model w obu przebiegach.**
  - K1 mierzy powtarzalność jednego anotatora (test–retest), a nie zgodność niezależnych kodujących.
  - Wspólne skrzywienia modelu nie obniżają κ między przebiegami.
- **Kontekst przebiegu A.**
  - Przebieg A wykonała sesja, która wcześniej długo pracowała z projektem: dyskusje o codebooku, wyniki i kontrola z 27.10, obejmująca 22 z tych postów.
  - Przebieg B w nowym agencie powtarza wyniki A, więc ten kontekst nie zmienił etykiet w ujęciu łącznym.
  - Kontekst agenta B nie był całkiem pusty: indeks pamięci, nazwy plików i tytuły commitów (zob. „Kontrola przebiegu B”).
- **Jedno odniesienie.** Odniesieniem jest jeden kodujący (IS), więc zgodność z IS nie jest trafnością.
- **Nierówny dostęp do informacji.** Ludzie mogli sprawdzić właściciela domeny (R7), a anotator AI nie otwiera linków.
- **Charakter wyniku.** Wynik jest nieważony i eksploracyjny.

## Następne kroki

1. **Decyzja zespołu o szarych strefach codebooka:**
   - `personal` przy opiniach w opisach zmian;
   - interwiki i automatyczne „dodaj link”;
   - posty-reklamy z linkiem do strony firmy;
   - strony, które są przedmiotem rozmowy (R2);
   - rewerty z uzasadnieniem dotyczącym źródeł (`edit_about_sources`).

   Po decyzji: codebook 2.3, protokół 1.1 i nowe przebiegi całości, bo zmiana instrukcji oznacza nowy przebieg.
2. **Preprint.** Poprawić zdanie o kontroli z 27.10 w ramce walidacji.
3. **Preregistracja v2.** Jeśli zespół przyjmie protokół w v2, trzeba zapisać:
   - operacjonalizację K1: κ `cites_source`, α (MASI) `source_types` i κ `edit_about_sources`, każde ≥ 0,8;
   - minimalną liczbę błędów przy K2.

## Pliki

- `scripts/26_ai_protocol.py`: krok `blind` oraz krok `score`, który porównuje też przebieg B z A.
- `annotations/ai_protocol/`:
  - `freeze_A.json`, `freeze_B.json`;
  - `key_A.csv`, `key_B.csv`;
  - `labels_A.csv`, `labels_B.csv`;
  - `scores_A.json`, `scores_B.json`;
  - `disagreements_A.csv`, `disagreements_B.csv`, `disagreements_B_vs_A.csv`.
- `annotations/sheets/ai_protocol/blind_A.csv` i `blind_B.csv`: poza gitem, bo zawierają teksty.

Sumy kontrolne w `freeze_*.json` zależą od końcówek linii w kopii roboczej. Codebook miał CRLF z checkoutu gita, a protokół LF. Dlatego `score` porównuje pliki także po ujednoliceniu końcówek linii na LF i na CRLF.
