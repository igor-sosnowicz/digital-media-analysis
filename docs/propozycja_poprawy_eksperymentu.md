# Jak poprawić eksperyment: moc, istotność i słabsze hipotezy (propozycja, 31.10.2026)

Dokument roboczy do decyzji zespołu. Nie zmienia preregistracji: każda propozycja z rozdziałów 3–5 wymaga datowanego wpisu w `docs/hipotezy_v2.md` **przed** pobraniem danych v2.

**Wersja 2 propozycji:** plan nie wymaga nowego kodowania przez ludzi. Dodatkowe etykiety powstają automatycznie (rozdz. 4), a trafność sprawdzamy na istniejących etykietach ludzi i metodami, które nie potrzebują nowych etykiet.

## 0. W skrócie

1. **Na danych v1 nie da się już uczciwie „uzyskać” istotności** (rozdz. 1). Celem jest wynik rozstrzygający: istotny trend albo istotny brak trendu większego niż SESOI. Oba są statystycznie istotne.
2. **v1 miało za małą moc** (0,11–0,43 przy SESOI z v2; rozdz. 2), więc rozwiązaniem jest preregistracja v2 z nowymi danymi.
3. **Nowe etykiety bez pracy ludzi** (rozdz. 4):
   - anotator AI z zamrożonym protokołem, w dwóch niezależnych przebiegach na ślepo;
   - słaba superwizja łącząca kilka różnych źródeł etykiet;
   - etykiety rozdzielone na zbiory do uczenia i do oceny.
4. **Trafność bez nowych etykiet ludzi:**
   - istniejące etykiety IS kodowane bez AI (253 jednostki) jako kotwica;
   - estymatory odporne na błąd etykiet;
   - testy grup znanych;
   - zgodność z zewnętrznym wskaźnikiem.
5. **Uniezależnienie anotacji od pipelinu:** osobny, zamrożony protokół, ślepota na wyniki instrumentów, rozłączne zbiory i pomiar korelacji błędów (rozdz. 4.3).
6. **Uczciwy koszt tej drogi:** dla stanowiska nie mamy żadnych etykiet ludzi niezależnych od AI. Twierdzenia o trafności instrumentu stanowiska będą więc słabsze niż przy kodowaniu przez dwie osoby i trzeba to napisać wprost (rozdz. 4.5).

## 1. Granica, której nie przekraczamy

**Niedopuszczalne** (zawyża odsetek fałszywych odkryć; Simmons i in. 2011; Gelman i Loken 2014; Kerr 1998):
- powtarzanie analizy v1 z innymi definicjami, latami, subredditami, wagami lub modelami, aż wyjdzie p < 0,05;
- zmiana testu (jedno- i dwustronny), α albo SESOI po obejrzeniu danych;
- przedstawianie analiz eksploracyjnych jako potwierdzających;
- testowanie na danych v1 „słabszej hipotezy” wymyślonej na podstawie wyników v1;
- **ocena instrumentu na etykietach wygenerowanych przez ten sam model, którym instrument był uczony.** To błędne koło i zawyżona trafność.

**Dopuszczalne:**
- poprawa pomiaru i mocy przed zebraniem nowych danych, zapisana w preregistracji (Nosek i in. 2018);
- hipotezy zainspirowane v1, sprawdzane na nowych danych v2;
- etykiety AI używane jawnie, z opisanym protokołem i ograniczeniami.

## 2. Diagnoza: dlaczego v1 nie rozstrzygnęło (eksploracyjnie)

Policzone z `annotations/hypotheses/confirmatory_trends.csv`. SESOI pochodzi z v2, ustalonej po wynikach v1, więc to diagnostyka, a nie test:

| Test v1 | Minimalny wykrywalny efekt (moc 0,8) | Moc przy SESOI z v2 | Nie-wyższość względem SESOI |
|---|---|---|---|
| H1-B, źródła alternatywne (wzrost) | OR 1,46 w całym okresie | 0,43 | p = 0,006 |
| H1-B, źródła konsensusu (spadek; tylko opis) | OR 1,75 | 0,26 | p = 0,007 |
| H2 (wzrost) | OR 9,9 w całym okresie | 0,11 | p = 0,98 |

**Wnioski:**
- **H1-B:** przedział już wyklucza wzrost większy niż SESOI. W v2 wynik „obalona: brak istotnego wzrostu” jest realny.
- **H2:** przy 10 zdarzeniach test wykrywa tylko ogromne trendy.
- **H1-A:** problemem jest pomiar (czułość instrumentu 0,21), a nie liczebność.

## 3. Ścieżka 1: naprawa, czyli v2 z poprawkami

v2 (`docs/hipotezy_v2.md`, commit `f375df6`) już zawiera:
- regułę decyzji z TOST;
- SESOI: 1,25 dla H1, 1,5 dla H2;
- analizę mocy;
- klasyfikację po właścicielu konta i pierwsze dodania;
- komentarze i panel autorów;
- różnicę w różnicach, przerwany szereg czasowy, przetrwanie linków i krzywą specyfikacji.

v2 zakłada jednak kodowanie przez dwie osoby: walidację H1 (360 jednostek) i właścicieli kont H2. Proponowane poprawki zastępują je tak:

| # | Poprawka | Po co |
|---|---|---|
| P1 | **Etykiety bez ręcznego kodowania:** walidacja H1 i właściciele kont H2 według protokołu z rozdz. 4 zamiast kodowania przez dwie osoby | zgodnie z decyzją zespołu, bez nowej pracy ludzi |
| P2 | **Instrument stanowiska uczony na etykietach:** dostrojenie lokalnego mDeBERTa (już pobranego, bez nowych modeli) na zbiorze uczącym z rozdz. 4.2 | NLI zero-shot miał czułość 0,21 |
| P3 | **Estymator odporny na błąd etykiet** jako analiza współgłówna (*prediction-powered inference*, Angelopoulos i in. 2023; *design-based supervised learning*, Egami i in. 2023), zakotwiczony w istniejących etykietach ludzi | trend pozostaje trafnie oszacowany mimo niedoskonałego instrumentu |
| P4 | **Liczebność ustalona przed wynikami:** próbne pobranie H2 (`LIMIT`) mierzy tylko liczbę pierwszych dodań na artykuł, bez wartości wskaźnika | v2 przyznaje, że 400 artykułów może nie dać mocy 0,8 |
| P5 | **Holm** w obrębie hipotez głównych i współgłównych | chroni przed zarzutem łowienia istotności |

**Warunki:**
- zgoda zespołu na pobranie danych v2 (kilka godzin, kilka GB);
- commit poprawek przed pobraniem.

## 4. Anotacje bez ręcznego kodowania

### 4.1. Co już mamy (bez nowej pracy)

| Etykiety | Liczba | Niezależne od AI? | Rola w nowym planie |
|---|---|---|---|
| Źródła, IS (gold i pilotaż) | 200 + 53 = 253 jednostki | **tak** | **kotwica** dla P3 i ocena niezależności (rozdz. 4.3) |
| Źródła, JP (gold i pilotaż) | 250 + 113 | nie (preannotacja AI zweryfikowana przez JP) | odniesienie drugiego rzędu; analiza wrażliwości |
| Stanowisko (gold i próba wzbogacona) | 157 + 277 | nie (reguła R14 albo preannotacja AI zweryfikowana przez JP) | odniesienie z zastrzeżeniem; zbiór oceny |
| Audyt H1-B | 180 | nie (preannotacja AI zweryfikowana przez JP) | jak wyżej |
| Ślepe drugie kodowanie AI (wariant A) | 144 | nie (ten sam model co preannotacja) | miara stabilności, nie trafności |
| Wyniki instrumentów (GLiNER, NLI, reguły) | dev, test, 6240 postów H1 | – | źródła etykiet dla słabej superwizji |

### 4.2. Jak wygenerować dodatkowe etykiety

**A1. Anotator AI z zamrożonym protokołem (główne źródło nowych etykiet).**
- Kto: Claude w sesjach Claude Code, tak jak przy dotychczasowych preannotacjach. To jedyny dostępny LLM bez klucza API i bez lokalnych LLM, zgodnie z ustaleniami.
- Protokół, zapisany w repozytorium przed kodowaniem:
  - stały tekst instrukcji = codebook 2.2 (R1–R15) z przykładami;
  - widzi tylko tekst jednostki, bez wyników instrumentów, wag, roku i etykiet innych osób;
  - losowa kolejność, partie o stałej wielkości;
  - zapis etykiety, pewności i krótkiego uzasadnienia.
- **Dwa niezależne przebiegi** z różną kolejnością, w osobnych sesjach i bez wglądu w pierwszy przebieg. Zgodność obu (κ) to miara stabilności. Etykieta „pewna” wymaga zgody obu przebiegów; reszta trafia do kategorii „niepewne”.
- Skala: kilka tysięcy jednostek w kilku sesjach, np. 300 jednostek na rok i rodzaj dla H1 v2 oraz wszystkie konta z linków H2 v2.
- W literaturze anotatorzy LLM bywają porównywalni z koderami z platform crowdsourcingowych, ale wymagają walidacji w każdym zadaniu (Gilardi i in. 2023; Ziems i in. 2024; Pangakis i in. 2023).

**A2. Słaba superwizja: wiele różnych źródeł etykiet zamiast jednego.** Model etykiet (Ratner i in. 2017) łączy niezależne źródła i szacuje ich trafność z ich wzajemnej zgodności, bez etykiet ludzi:
- reguły codebooka (R2, R3, R9, R10, R14 jako funkcje etykietujące);
- leksykon nieufności `distrust_v1`;
- GLiNER i NLI (zero-shot);
- dwa przebiegi anotatora AI (A1);
- dla H2: rejestr oficjalnych kont instytucji (WHO, CDC, ministerstwa, GIS) zbudowany z ich stron.

Wynik to etykiety probabilistyczne. Model etykiet sprawdzamy na 253 etykietach IS (dla źródeł).

**A3. Rozdzielenie zbiorów (warunek konieczny).**
- **Zbiór uczący** (strojenie, dostrajanie mDeBERTa w P2): etykiety A1 i A2, także wzbogacone o posty `challenges` (dobór warstwowy jak w próbie wzbogaconej v1).
- **Zbiór oceny:** rozłączny z uczącym, wylosowany przed wygenerowaniem etykiet uczących, z etykietami z innego źródła niż te, którymi uczono instrument (rozdz. 4.4).
- Instrument uczony na etykietach Claude nie może być oceniany wyłącznie na etykietach Claude. To byłoby błędne koło (rozdz. 1).

**A4. Syntetyczne przykłady (opcjonalnie, tylko do uczenia).** Parafrazy rzadkich postów `challenges` przygotowane przez anotatora AI mogą zwiększyć zbiór uczący. Nigdy nie wchodzą do oceny ani do testów hipotez, a ryzyko przesunięcia rozkładu trzeba opisać.

**A5. Właściciele kont H2 bez kodowania ręcznego.**
- Rejestr oficjalnych kont (A2) i klasyfikacja kont przez anotatora AI (A1) według `owners.yaml`, w dwóch przebiegach.
- Konta niepewne zostają bez kodu, a v2 już przewiduje regułę dwóch granic: niezakodowane jako nie-alternatywne i jako alternatywne. Werdykt jest ważny tylko przy zgodności obu granic.
- Rozwiązywanie kanałów YouTube przez publiczny endpoint jest już w v2 (wymaga zgody na ruch sieciowy).

### 4.3. Jak uniezależnić anotacje od pipelinu

| # | Zasada | Jak to sprawdzić |
|---|---|---|
| N1 | Protokół anotacji (instrukcja, model, wersja codebooka, kolejność, ziarno) zacommitowany **przed** strojeniem instrumentów | commit w historii |
| N2 | Anotator nie widzi wyników instrumentów ani innych etykiet | kod eksportu bez tych kolumn (jak eksport ślepy z wariantu A) |
| N3 | Brak iteracyjnego poprawiania instrukcji pod wyniki instrumentów; zmiana instrukcji = nowa wersja i ponowne kodowanie całości | wersje protokołu w repozytorium |
| N4 | Zbiór oceny rozłączny z uczącym i wylosowany przed generowaniem etykiet | manifest z ziarnem |
| N5 | Ocena przez źródło innej rodziny niż instrument: instrument uczony na etykietach Claude oceniany na etykietach IS (źródła), regułach i testach grup znanych; NLI zero-shot oceniany na etykietach Claude | tabela „kto uczy / kto ocenia” w raporcie |
| N6 | **Pomiar niezależności błędów:** na 253 etykietach IS liczymy, czy anotator AI i instrument mylą się w tych samych jednostkach (κ wskaźników błędu). Wysoka zgodność błędów oznacza, że ocena jest zawyżona | raport κ błędów |
| N7 | Etykiety z sumą kontrolną (hash) zapisaną przy commicie; żadnych zmian po teście | plik z hashami |
| N8 | Pełne ujawnienie w sekcji 7: które etykiety są z AI, z jakiego protokołu i w jakiej roli | tekst preprintu |

### 4.4. Jak oceniać trafność bez nowych etykiet ludzi

1. **Kotwica w istniejących etykietach ludzi (P3).** Estymator *prediction-powered inference* albo *design-based supervised learning* łączy etykiety instrumentu dla wszystkich jednostek z etykietami odniesienia dla podpróby. Daje nieobciążony trend z uczciwym przedziałem.
   - Dla źródeł podpróbą jest 253 etykiet IS.
   - Dla stanowiska podpróbą jest odniesienie z planu C (zweryfikowane przez JP), z jawnym zastrzeżeniem.
   - Warunek: podpróba musi być losowa względem ramy. Etykiety v1 pochodzą z innej ramy niż v2, więc ich użycie w v2 to założenie, które trzeba zapisać i sprawdzić w analizie wrażliwości.
2. **Testy grup znanych** (trafność teoretyczna; Cronbach i Meehl 1955), bez żadnych etykiet:
   - udział `challenges` wyższy w r/conspiracy i r/climateskeptics niż w r/science i r/climate;
   - udział źródeł alternatywnych wyższy w r/conspiracy niż w r/science (v1 eksploracyjnie: 48 % wobec 34 %).

   Progi różnic zapisujemy z góry.
3. **Zgodność zbieżna:** dwa instrumenty różnych rodzin (dostrojony mDeBERTa i leksykon `distrust_v1`) dają zgodne trendy roczne.
4. **Zgodność zewnętrzna:** korelacja rocznego wskaźnika z zaufaniem do nauki w GSS (v2 już ją przewiduje; wymaga zgody na pobranie danych GSS).
5. **Stabilność:** κ dwóch przebiegów anotatora AI ≥ 0,8.

### 4.5. Czego ta droga nie daje (do zapisania w preprincie)

- **Brak niezależnego ludzkiego odniesienia dla stanowiska.** Warunek „F1 ≥ 0,5 i κ ≥ 0,4 względem ludzi” nie może być spełniony w sensie z v1. Zastępujemy go zestawem: zgodność z odniesieniem planu C, testy grup znanych, stabilność i zgodność zbieżna. To słabszy dowód trafności.
- **Etykiety AI mogą mieć systematyczne błędy**, np. dryf w czasie, gdy język się zmienia, co dla testu trendu jest groźne. Dlatego potrzebny jest błąd różnicowy liczony na kotwicy IS (dla źródeł) i analiza z P3.
- **Opcjonalnie, jako wzmocnienie, a nie warunek:** krótkie sprawdzenie przez człowieka 50 losowych etykiet stanowiska bez podpowiedzi, około 30 minut. To jedyna droga do niezależnego odniesienia dla stanowiska.

## 5. Ścieżka 2: słabsze, ale rozstrzygalne hipotezy (preregistrowane przed danymi v2)

| Hipoteza (propozycja) | Dlaczego łatwiejsza do rozstrzygnięcia | Pomiar (bez ręcznego kodowania) | Sygnał z v1 (eksploracyjny) | Ryzyko |
|---|---|---|---|---|
| **H1-W1: brak istotnego wzrostu.** Udział źródeł alternatywnych w obrębie społeczności naukowych nie rośnie bardziej niż SESOI | test nie-wyższości lub TOST | GLiNER z kotwicą IS (P3) | p = 0,006 dla nie-wyższości | to „obalenie” kierunku H1-B |
| **H1-W2: migracja dyskusji.** Udział postów o tematach konsensusu publikowanych w społecznościach sceptycznych i spiskowych rośnie w latach 2008–2018 | **nie wymaga żadnych etykiet** (liczby postów), moc bardzo duża | `topics.yaml` + subreddit | r/conspiracy: 2 % → 58 % próby z powołaniem | mierzy uczestnictwo, nie postawy |
| **H1-W3: poziom populacji.** W całej dyskusji o nauce rośnie udział postów podważających konsensus lub źródeł alternatywnych | efekt składu i efekt wewnątrz sumują się | instrument z P2/P3 | źródła alternatywne: 35 % → 47 % | trzeba z góry nazwać ją hipotezą o populacji |
| **H2-W1: odźwiernictwo.** Linki alternatywne są usuwane szybciej niż pozostałe (współczynnik ryzyka > 1) | duży spodziewany efekt, wiele zdarzeń | historia rewizji v2 (bez etykiet poza kategorią linku) | brak | zależy od liczby linków alternatywnych |
| **H2-W2: próby a przyjęcie.** Źródła alternatywne częstsze na stronach dyskusji niż w artykułach | porównanie przekrojowe | strony dyskusji v2 | brak | definicja „próby” powołania |
| **H2-W3: hipoteza pomiarowa.** Co najmniej 25 % linków „alternatywnych według domeny” prowadzi do kont instytucji | test proporcji, duży efekt | rejestr kont + anotator AI (A5), dwie granice | 8 z 10 w v1 | wynik metodologiczny |

Nie zmieniamy SESOI, okresu ani zakresu po to, żeby ułatwić uzyskanie istotności. Hipotezy H1-W2 i H2-W1 są najmniej zależne od etykiet, więc najbezpieczniejsze przy rezygnacji z ręcznego kodowania.

## 6. Kryteria końcowe (definicja ukończenia)

| # | Kryterium | Próg |
|---|---|---|
| K1 | Jakość etykiet automatycznych | κ dwóch przebiegów anotatora AI ≥ 0,8; model etykiet (A2) na kotwicy IS: F1 `cites_source` ≥ 0,8 i MASI ≥ 0,5 |
| K2 | Niezależność oceny | ocena każdego instrumentu przez źródło innej rodziny (N5); κ wskaźników błędu anotatora i instrumentu na kotwicy IS < 0,4 (N6) |
| K3 | Trafność instrumentu stanowiska przed testem trendu | F1 `challenges` ≥ 0,5 i κ ≥ 0,4 względem odniesienia planu C, **oraz** testy grup znanych w zapisanym kierunku (p < 0,05), **oraz** zgodność zbieżna z `distrust_v1` (korelacja roczna > 0) |
| K4 | Moc przed danymi | ≥ 0,8 przy SESOI w obu kierunkach testu; inaczej wynik „niedostatecznie mocny” |
| K5 | Zamrożenie i jeden przebieg | protokół anotacji (N1), progi, liczebności i kod zacommitowane przed testem; jeden test potwierdzający |
| K6 | Reguła decyzji | v2: potwierdzona / obalona: brak trendu (TOST) / trend przeciwny / nierozstrzygnięta |
| K7 | Wielokrotność | Holm w obrębie hipotez głównych i współgłównych |
| K8 | Sukces projektu | każda hipoteza główna kończy się wynikiem rozstrzygającym przy spełnionych K1–K7; jawne ujawnienie roli AI w etykietach (N8) |

## 7. Kolejność i koszt

1. Decyzja zespołu: które poprawki (P1–P5), które hipotezy (rozdz. 5) i czy robimy opcjonalne sprawdzenie 50 etykiet (rozdz. 4.5).
2. Protokół anotacji (A1, N1–N7) i datowane wpisy w `docs/hipotezy_v2.md`; commit **przed** pobraniem.
3. Próbne pobranie H2, tylko liczebności (P4).
4. Pełne pobranie v2 (zgoda zespołu).
5. Anotacje automatyczne: dwa przebiegi A1, model etykiet A2, właściciele kont A5. Kilka sesji, bez pracy ludzi.
6. Dostrojenie i zamrożenie instrumentu (P2), sprawdzenie K1–K3, jeden test.
7. `make hypotheses-v2 CONFIRMATORY=1`, raport według K6–K8.

**Szacunek kosztu:**
- ludzie: 0 godzin (opcjonalnie 30 minut);
- sesje AI: kilka;
- pobieranie: kilka godzin;
- analiza: 1–2 dni.

To nowy cykl badania (preprint v2), a nie poprawka obecnego preprintu.

## 8. Co można zrobić od razu, bez nowych danych

- Zostawić v1 jako uczciwy wynik negatywny lub nierozstrzygnięty.
- Dopisać do dyskusji diagnostykę mocy z rozdz. 2, oznaczoną jako eksploracyjna.
- Przećwiczyć protokół A1 i pomiar niezależności N6 na istniejących danych v1, czyli na 253 etykietach IS. To nie zmienia wyników v1, a pokazuje, czy etykiety automatyczne są wystarczająco dobre, zanim pobierzemy v2. Przebiegi A i B wykonano 31.10.2026; wyniki są w `docs/cwiczenie_protokolu_ai.md` (K1 spełnione, K2 na Wikipedii nie).

## Literatura (do sprawdzenia przed cytowaniem)

- Angelopoulos, A. N., Bates, S., Fannjiang, C., Jordan, M. I., Zrnic, T. (2023). Prediction-powered inference. *Science*, 382(6671), 669–674.
- Cronbach, L. J., Meehl, P. E. (1955). Construct validity in psychological tests. *Psychological Bulletin*, 52(4), 281–302.
- Egami, N., Hinck, M., Stewart, B. M., Wei, H. (2023). Using imperfect surrogates for downstream inference: Design-based supervised learning for social science applications of large language models. *NeurIPS* 36.
- Gelman, A., Loken, E. (2014). The statistical crisis in science. *American Scientist*, 102(6), 460–465.
- Gilardi, F., Alizadeh, M., Kubli, M. (2023). ChatGPT outperforms crowd workers for text-annotation tasks. *PNAS*, 120(30), e2305016120.
- Kerr, N. L. (1998). HARKing: Hypothesizing after the results are known. *Personality and Social Psychology Review*, 2(3), 196–217.
- Lakens, D. (2017). Equivalence tests: A practical primer for t tests, correlations, and meta-analyses. *Social Psychological and Personality Science*, 8(4), 355–362.
- Nosek, B. A., Ebersole, C. R., DeHaven, A. C., Mellor, D. T. (2018). The preregistration revolution. *PNAS*, 115(11), 2600–2606.
- Pangakis, N., Wolken, S., Fasching, N. (2023). Automated annotation with generative AI requires validation. arXiv:2306.00176.
- Ratner, A., Bach, S. H., Ehrenberg, H., Fries, J., Wu, S., Ré, C. (2017). Snorkel: Rapid training data creation with weak supervision. *Proceedings of the VLDB Endowment*, 11(3), 269–282.
- Simmons, J. P., Nelson, L. D., Simonsohn, U. (2011). False-positive psychology. *Psychological Science*, 22(11), 1359–1366.
- Ziems, C., Held, W., Shaikh, O., Chen, J., Zhang, Z., Yang, D. (2024). Can large language models transform computational social science? *Computational Linguistics*, 50(1), 237–291.
