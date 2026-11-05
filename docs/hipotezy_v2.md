# Preregistracja v2: rozszerzony test hipotez H1 i H2

*Wersja 1.0, projekt z 25.10.2026, do zatwierdzenia przez zespół.* Ten dokument zatwierdzamy commitem razem z:
- sekcją `hypotheses_v2` w `config.yaml`;
- `codebook/topics.yaml` i `codebook/owners.yaml`;
- kodem analizy, czyli plikami z listy `PREREGISTRATION_V2` w `src/digital_media_analysis/prereg.py`.

Commit ma powstać **przed pobraniem jakichkolwiek danych v2**. Skrypty pobierające (`00b`, `00c`, `01c`) i przebieg potwierdzający (`16 --confirmatory`) odmawiają uruchomienia, gdy te pliki nie są zacommitowane. Każdą późniejszą zmianę zapisujemy w sekcji „Zmiany” z datą i powodem. Preregistracja v1 ([`hipotezy.md`](hipotezy.md)) i jej wyniki ([`wyniki_hipotez.md`](wyniki_hipotez.md)) zostają bez zmian.

## Dlaczego v2

Test v1 nie rozstrzygnął żadnej hipotezy:
- **H1:** test główny H1-A nie ma etykiet stanowiska, a wskaźniki źródeł (H1-B) mierzą zaufanie tylko pośrednio i zmieniają się przez zmianę składu subredditów.
- **H2:** osiem stron dało 10 zdarzeń. Klasyfikacja po domenie uznała oficjalne konta WHO i GIS za źródła alternatywne, a linki przywracane po rewertach liczyły się wielokrotnie.

Wersja v2 poprawia pomiar (stanowisko wobec konkretnego konsensusu, właściciel konta, pierwsze dodania), powiększa ramy do wymaganej mocy i dodaje test równoważności. Dzięki niemu „brak trendu” można wykazać, a nie tylko nie odrzucić hipotezy zerowej.

## Reguła decyzji (obie hipotezy)

Dla wskaźnika głównego każdej hipotezy:

| Wynik | Warunek |
|---|---|
| **potwierdzona** | jednostronne p < 0,05 w kierunku hipotezy |
| **obalona: brak trendu** | test równoważności (TOST) p < 0,05 wobec najmniejszego efektu istotnego (SESOI) |
| **obalona: trend przeciwny** | jednostronne p < 0,05 w kierunku przeciwnym |
| **nierozstrzygnięta** | żadne z powyższych |

SESOI to iloraz szans między pierwszym a ostatnim rokiem okresu: dla H1 1,25 (1,0173 na rok), dla H2 1,5 (1,0699 na rok). Mniejsze zmiany uznajemy za praktycznie nieistotne. Analizy drugorzędne raportujemy bez poprawki na wielokrotne testowanie i nie zmieniają one werdyktu.

## H1: zaufanie do konsensusu naukowego (Reddit 2005–2018)

**Rama.**
- Posty o temacie konsensusu naukowego w 13 subredditach z `config.yaml`:
  - naukowych: science, askscience, skeptic, conspiracy, health, vaccines, climate, climateskeptics;
  - ogólnych: news, worldnews, politics, todayilearned, AskReddit.
- Dni losowane z każdego miesiąca: 2 losowe dni (ziarno 20261025). Subreddit z mniej niż 100 postami w wylosowanych dniach roku wchodzi za ten rok w całości.
- Temat to dopasowanie wzorców z `codebook/topics.yaml` (zmiana klimatu, szczepionki, ewolucja, GMO, fluoryzacja) do tytułu lub treści posta.
- Pod każdym postem: pierwsze 100 komentarzy najwyższego poziomu, z których losujemy 20.
- Posty usunięte zostają w ramie z flagą, ale nie wchodzą do analizy (ich treść nie istnieje). Odsetek usuniętych raportujemy dla każdego roku i subredditu.

**Próba analityczna.** Najwyżej 200 jednostek na subreddit, rok i rodzaj (post albo komentarz), z wagami do ramy. Waga posta to waga dnia; waga komentarza to waga dnia posta razy liczba przejrzanych komentarzy przez liczbę wylosowanych. Autorów zapisujemy w repozytorium tylko jako pseudonimy (sól poza gitem).

**Wskaźnik główny.** Udział jednostek `challenges` wśród jednostek o temacie konsensusu (`consensus_stance` ≠ `not_applicable`, codebook 2.2, reguły R14 i R15). Kierunek: wzrost. Stanowisko oceniamy względem konsensusu danego tematu (instrument `stance_v2`).

**Walidacja i warunek trafności.**
- Próba walidacyjna: po 120 jednostek z okresów 2005–2010, 2011–2014 i 2015–2018. W każdym okresie 1/3 idzie do strojenia (`dev`), 2/3 do testu.
- Dwie osoby kodują niezależnie `consensus_topic` i `consensus_stance`. Raportujemy α Krippendorffa. Spory rozstrzygamy przy uzgadnianiu i zapisujemy w `annotations/labels/h1v2_validation/adjudicated.csv`.
- Progi `stance_v2` stroimy na `dev`, zamrażamy commitem i oceniamy raz na teście (`14 --evaluate`).
- **Warunek trafności:** F1 dla `challenges` ≥ 0,5 i κ ≥ 0,4 na teście.
- Jeśli `stance_v2` go nie spełni, wskaźnikiem głównym zostaje leksykon nieufności `distrust_v1`, pod warunkiem że ma F1 ≥ 0,5 względem `challenges` na teście. Jeśli i on nie spełni warunku, H1 uznajemy za niemierzalną tymi instrumentami. To wynik negatywny i raportujemy go jako taki.

**Model główny.** Ważona regresja logistyczna: wskaźnik ~ rok + efekty stałe subredditu, wagi przeskalowane do średniej 1, błędy grupowane po dniu. Test jednostronny i TOST.

**Analizy drugorzędne:**
1. udział `supports` (kierunek: spadek);
2. same posty i same komentarze;
3. subreddity naukowe i ogólne osobno;
4. `distrust_v1` jako drugi wskaźnik;
5. **panel autorów:** autorzy z jednostkami w co najmniej 3 latach, regresja logistyczna warunkowa po autorze; liczy się tylko zmiana u tej samej osoby;
6. **korekta błędu pomiaru:** logit z czułością i swoistością `stance_v2` z testu walidacji w funkcji wiarygodności, ich niepewność przez 100 losowań z rozkładów Beta (reguły Rubina);
7. **dekompozycja zmiany** udziału między latami 2005–2009 a 2014–2018 na zmianę w obrębie subredditów i zmianę składu;
8. **krzywa specyfikacji:** wskaźnik (`challenges`, `distrust`) × rodzaj jednostki (wszystkie, posty, komentarze) × wagi (z próby, równe) × efekty stałe (subreddit, brak), razem 24 specyfikacje;
9. **błąd różnicowy:** metryki instrumentu w każdym okresie z testu walidacji;
10. **zgodność zewnętrzna:** korelacja rocznego wskaźnika z odsetkiem „a great deal” zaufania do środowiska naukowego w GSS (CONSCI), jeśli zespół pobierze dane do `data/external/gss_consci.csv`. To nie jest test H1.

**Moc** (`scripts/17_power_analysis.py`; 13 subredditów, 14 lat, efekt równy SESOI, 200 powtórzeń, błędy Walda bez grupowania, więc to górna granica):

| Udział bazowy `challenges` | Jednostek na komórkę | Moc wykrycia | Moc wykazania braku trendu |
|---|---|---|---|
| 0,05 | 100 / 200 | 0,65 / 0,90 | 0,38 / 0,88 |
| 0,15 | 100 / 200 | 0,96 / 1,00 | 0,95 / 1,00 |
| 0,30 | 50 / 100 | 0,92 / 1,00 | 0,81 / 1,00 |

Planujemy 200 jednostek na komórkę (osobno posty i komentarze). Jeśli w ramie zabraknie jednostek, raportujemy faktyczną liczność i moc dla niej.

## H2: źródła alternatywne (Wikipedia 2020–2026)

**Rama.**
- Artykuły polskiej Wikipedii z drzew kategorii `config.yaml`, do 2 poziomów podkategorii:
  - grupa „zdrowie”: Medycyna, Choroby, Szczepionki, Dietetyka, Medycyna niekonwencjonalna, Globalne ocieplenie, Klimatologia;
  - grupa kontrolna: Matematyka, Fizyka, Architektura.
- Po najwyżej 400 artykułów na grupę, losowo (ziarno 20261025); artykuł z kilku kategorii liczy się raz, w pierwszej grupie. Kategorię bez artykułów `00b` zgłasza; zmiana listy kategorii po tym zgłoszeniu to zmiana, którą zapisujemy niżej.
- Dla każdego artykułu i jego strony dyskusji: pełna historia rewizji od 1.01.2015 do dnia pobrania, z ostatnią rewizją sprzed 2015 r. jako stanem wyjściowym.

**Jednostka i wskaźnik główny.**
- Jednostka to **pierwsze dodanie** linku do przypisów (`<ref>`) artykułu z grupy „zdrowie” w latach 2020–2026: link, którego wcześniej nie było na stronie w obserwowanej historii.
- Wskaźnik to `alt_owner`: link prowadzi do konta, którego właściciel jest niezależnym ekspertem, influencerem albo anonimem (`codebook/owners.yaml`). Kierunek: wzrost.
- Właściciela ustala człowiek dla każdego konta z listy `owner_review.csv`, według definicji z `owners.yaml`, bez oceny prawdziwości treści (R6). Filmy z YouTube przypisujemy do kanału przez publiczny endpoint oEmbed. Dwie osoby kodują niezależnie konta z co najmniej 2 linkami, raportujemy κ, spory rozstrzygamy.
- **Reguła dla niezakodowanych kont:** przebieg potwierdzający wymaga zakodowania wszystkich kont z jednostek głównych. Jeśli mimo to ponad 5% linków do platform zostanie bez kodu, raportujemy dwie granice (niezakodowane jako nie-alternatywne i jako alternatywne). Werdykt jest wtedy rozstrzygnięty tylko przy zgodności obu granic.

**Model główny.** Regresja logistyczna: wskaźnik ~ rok + efekty stałe strony, błędy grupowane po rewizji. Test jednostronny i TOST.

**Analizy drugorzędne:**
1. inne definicje źródła alternatywnego:
   - kategoria domeny z v1 (`codebook/domains.yaml`, `social_blog`);
   - domena z listy „perennial sources” angielskiej Wikipedii o statusie: ogólnie niewiarygodne, wycofane albo na czarnej liście (lista pobrana raz, z datą, przejrzana ręcznie);
2. wszystkie dodania (z powtórnymi);
3. pierwsze dodania poza edycjami później cofniętymi;
4. granica górna z niezakodowanymi kontami jako alternatywnymi;
5. strony dyskusji (wszystkie linki w treści, czyli **próby** powołania się na źródło, także te, które nie trafiły do artykułu);
6. logit Firtha bez efektów stałych (rzadkie zdarzenia);
7. ujemny dwumianowy dla liczby linków alternatywnych na stronę i miesiąc z offsetem log(liczby dodanych linków);
8. **różnica w różnicach:** zdrowie a kontrola, lata 2015–2026, interakcja „zdrowie × po marcu 2020” w logicie z efektami stałymi strony i roku;
9. **przerwany szereg czasowy** dla stron o zdrowiu: zmiana poziomu i nachylenia w marcu 2020;
10. **przetrwanie linków:** czas do usunięcia linku alternatywnego i pozostałych (Kaplan–Meier, test log-rank, model Coxa), czyli czy społeczność usuwa źródła alternatywne szybciej;
11. **krzywa specyfikacji:** definicja (3) × jednostka (wszystkie, pierwsze, pierwsze bez cofniętych) × przestrzeń nazw (artykuł, dyskusja) × model (logit z efektami stałymi, Firth), razem 36 specyfikacji.

**Moc** (200 stron z linkami, 7 lat, udział bazowy 0,75% jak w v1, efekt równy SESOI, model bez efektów stałych):

| Dodane linki razem | Moc wykrycia | Moc wykazania braku trendu |
|---|---|---|
| 14 000 | 0,42 | 0,00 |
| 28 000 | 0,68 | 0,32 |
| 56 000 | 0,91 | 0,78 |

Moc 0,8 wymaga około 40–50 tys. pierwszych dodań w artykułach o zdrowiu. Liczbę stron (400) wybraliśmy, żeby się do tego zbliżyć. Jeśli pobrane dane dadzą mniej niż 28 tys. jednostek głównych, raportujemy test jako niedostatecznie mocny, a jego wynik bez zmian.

## Kolejność prac

1. Przegląd i commit tego dokumentu z plikami z listy `PREREGISTRATION_V2`.
2. Pobieranie danych (zgoda zespołu; kilka godzin i kilka GB ruchu sieciowego):
   - `make h2-frame`;
   - `make h2-history` (najpierw z `LIMIT=5` na próbę);
   - `make h1-frame`.
3. **H1:**
   - `make label-h1-v2 ARGS="--validation-annotators IS JP"`;
   - kodowanie i `ARGS=--import-validation`;
   - `ARGS=--tune`;
   - ustawienie progów i `TUNED = True` w `stance_v2.py`, commit;
   - `ARGS=--evaluate`;
   - `make label-h1-v2`.
4. **H2:**
   - `make h2-links ARGS="--fetch-rsp --resolve-youtube"`;
   - kodowanie kont w `codebook/owners.yaml` (z `owner_review.csv`);
   - przegląd listy „perennial sources”;
   - commit kodów kont (zmiana przewidziana, zapisywana niżej);
   - ponownie `make h2-links`.
5. `make hypotheses-v2 CONFIRMATORY=1`, wyniki w `annotations/hypotheses_v2/`.

## Ograniczenia znane z góry

- Wzorce tematów pomijają jednostki o konsensusie bez słów kluczowych; walidacja mierzy precyzję tematu, nie jego czułość w całej ramie.
- Komentarze spoza pierwszych 100 pod postem nie wchodzą do ramy.
- Usunięte posty i komentarze nie mają treści, więc nie wiemy, czy usuwanie zmienia się w czasie inaczej dla postów podważających konsensus. Raportujemy odsetek usuniętych w czasie.
- Kategorie Wikipedii są niejednorodne; grupa kontrolna ma inny rytm edycji niż artykuły o zdrowiu.
- Kodowanie właścicieli kont jest pracą ludzi i ma własny błąd (κ raportujemy).

## Zmiany

*Tu zapisujemy każdą zmianę po commicie preregistracji, z datą i powodem, przed przebiegiem potwierdzającym.*

### Zmiana 1 — PROJEKT z 02.11.2026, niezatwierdzony

Zespół zatwierdza ten wpis osobnym commitem, który usuwa z nagłówka słowa „PROJEKT” i „niezatwierdzony”, razem z plikami z listy `PREREGISTRATION_V2`, przed pobraniem danych v2. Do tego czasu wpis nie obowiązuje, także wtedy, gdy projekt i te pliki są już w repozytorium. Szczegóły i uzasadnienie liczb są w `docs/plan_poprawy_krok_po_kroku.md`.

**Powód.**
- Analiza mocy z błędem instrumentu i efektem klastrów pokazała, że przy parametrach powyżej:
  - H1 ze `stance_v1` ma moc ≤ 0,49;
  - H2 według właściciela konta wymaga ponad 220 tys. linków, bo źródła alternatywne to około 0,15% dodań.

  Liczby odtwarza `scripts/17_power_analysis.py --plan`.
- Zespół zdecydował, że nie koduje ręcznie walidacji. Etykiety daje protokół AI, przećwiczony 31.10 i 02.11.2026 (`docs/cwiczenie_protokolu_ai.md`).
- Żadnych danych v2 nie oglądaliśmy.

**Zmiany.**
1. **Rama** (`config.yaml`):
   - H1: 4 dni w miesiącu, 30 komentarzy na post, do 500 komentarzy na subreddit i rok, posty bez limitu;
   - H2: wszystkie artykuły drzew kategorii.
2. **Wyłączenia z każdego testu v2:**
   - posty ram Reddita v1 z ich komentarzami;
   - 8 stron Wikipedii z v1.

   Z analiz H2 wypadają też rewizje dodające ponad 20 linków. Test główny H2 z tymi rewizjami raportujemy osobno.
3. **Etykiety walidacyjne i uczące** zamiast kodowania przez dwie osoby:
   - protokół AI 1.1 (`docs/protokol_anotacji_ai_1_1.md`, codebook 2.3), czyli dwa ślepe przebiegi w nowych agentach;
   - odniesieniem są jednostki, w których oba przebiegi się zgadzają; odsetek niezgodnych raportujemy;
   - sprawdzenia przez człowieka nie ma (decyzja D0.4), co ujawniamy jako słabszy dowód trafności.
4. **Warunek trafności stanowiska.** Do F1 ≥ 0,5 i κ ≥ 0,4 dochodzą:
   - czułość ≥ 0,7 i swoistość ≥ 0,98 dla `challenges`;
   - test grup znanych: udział `challenges` w r/conspiracy i r/climateskeptics wyższy niż w r/science i r/climate, p < 0,05;
   - różnica czułości między okresami walidacji < 0,15.
5. **Drabiny hipotez** (brzmienie w rozdz. 3 planu):
   - H1 → H1-S1 (źródła alternatywne w społecznościach, gliner_v1) → H1-S2 (to samo w całej dyskusji, bez efektów stałych) → H1-S3 (udział jednostek w r/conspiracy i r/climateskeptics, bez etykiet);
   - H2 → H2-S1 (udział źródeł nieeksperckich: media, platformy, inne) → H2-S2 (zdrowie a grupa kontrolna) → H2-S4 (źródła alternatywne według właściciela poniżej 2% pierwszych dodań);
   - H2-S3 (linki nieeksperckie usuwane szybciej; HR ≥ 1,25) i H2-S5 (≥ 25% linków alternatywnych według domeny to konta instytucji) są zawsze drugorzędne.
6. **Bramka mocy** (`scripts/27_power_gate.py`):
   - testem głównym rodziny zostaje pierwszy wariant drabiny, który przeszedł bramki trafności i ma moc ≥ 0,8 dla wykrycia SESOI i dla TOST;
   - moc liczymy z liczebności, czułości i swoistości, łącznego udziału bazowego i efektu klastrów liczonego bez roku;
   - `power_gate.json` commitujemy przed przebiegiem potwierdzającym, a `scripts/16` bez niego odmawia.
7. **TOST** trendów mierzonych instrumentem (H1, H1-S1, H1-S2) liczymy względem granicy spłaszczonej przez błąd instrumentu.
8. **Wielokrotność:** poprawka Holma na dwóch testach głównych i, osobno, w rodzinach testów drugorzędnych. Werdykt każdego testu drabiny wynika z reguły decyzji powyżej, stosowanej do skorygowanych p.
9. **Bez zmian:** SESOI, α, okresy, kierunki i modele główne (poza wyłączeniami z punktu 2).

**Kolejność prac.** Krok 3 (kodowanie walidacji przez IS i JP) zastępuje protokół AI 1.1. Krok 5 poprzedza `scripts/27_power_gate.py` i commit `power_gate.json`.
