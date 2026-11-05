# Plan krok po kroku: rozstrzygające wyniki dla H1 i H2 (02.11.2026)

Dokument roboczy do decyzji zespołu. Rozwija `docs/propozycja_poprawy_eksperymentu.md` o konkretne kroki, liczby mocy i bramki decyzyjne. Uwzględnia wyniki ćwiczenia protokołu AI (`docs/cwiczenie_protokolu_ai.md`).

Nic z tego planu nie zmienia v1 ani preregistracji. Każda zmiana wymaga datowanego wpisu w `docs/hipotezy_v2.md` (sekcja „Zmiany”) i commitu **przed** pobraniem danych v2.

## Stan wdrożenia (02.11.2026)

**Decyzje zespołu podjęte 02.11** (podał JP):

| Decyzja | Rozstrzygnięcie |
|---|---|
| D0.5 | szare strefy rozstrzygnięte jak w etykietach IS |
| D0.4 | bez sprawdzenia przez człowieka |
| D0.2 | zgoda na przebiegi AI; bez commitu i bez pobierania danych v2 na tym etapie |

**Zrobione (bez commitu):**

| Krok | Co powstało |
|---|---|
| 1.1 | codebook 2.3 (`codebook/codebook.yaml`, `codebook.md`); protokół AI 1.1 (`docs/protokol_anotacji_ai_1_1.md`) |
| 1.2 | przebiegi C i D źródeł według codebooka 2.3, na 253 jednostkach IS |
| 1.3 | przebiegi S1 i S2 stanowiska na 434 postach planu C (wyniki: `docs/cwiczenie_protokolu_ai.md`) |
| 1.4 | formuły mocy z błędem instrumentu i DEFF w `power.py`; `scripts/17_power_analysis.py --plan` zapisuje `power_plan.csv` i `power_plan_values.json` |
| 1.5 | parametry ramy w `config.yaml`; `post_id` i limity według rodzaju w `h1_frame.py`; wszystkie strony w `wikipedia_frame.py`; wyłączenia jednostek v1 i rewizji masowych |
| 5 (kod) | `scripts/14 --sources`: etykiety źródeł gliner_v1 dla H1-S1 i H1-S2 |
| 7 | moduł `ladders.py` i `scripts/27_power_gate.py` (z `--plan`: wybór na wartościach planistycznych) |
| 8 | `scripts/16`: warianty drabin, role z bramki, poprawka Holma, werdykty, TOST na skali skorygowanej; tryb potwierdzający wymaga zacommitowanego `power_gate.json` |
| 2.1 | projekt wpisu „Zmiana 1” w `docs/hipotezy_v2.md` |

`prereg.py` zamraża teraz także codebook, protokół 1.1, moduł drabin, formuły mocy oraz skrypty 14 i 27.

**Bramki z etapu 1:**
- **B1 (źródła) spełniona.** κ przebiegów C i D wynosi 0,96. Na Wikipedii F1 `cites_source` względem IS wzrosło z 0,29–0,32 do 0,63–0,66.
- **B2 (stanowisko) spełniona na granicy.** Czułość etykiet pewnych dla `challenges` wynosi 0,81, przy κ przebiegów 0,94.
- **Do decyzji zespołu przed etapem 5:** doprecyzowanie R14 (artykuły o badaniach udostępnione bez komentarza). Wskazali je wszyscy agenci stanowiska, a od tego zależy czułość `stance_v2`.

**Do zrobienia przez zespół:**
1. Przegląd i zatwierdzenie „Zmiany 1”, potem commit z tagiem `prereg-v2.1` (bramka B3).
2. Zgoda na próbne i pełne pobranie danych v2 (etapy 3–4).
3. Etykiety AI v2 (etap 5) i instrument stanowiska (etap 6).
4. `scripts/27` na danych, commit `power_gate.json` i jeden przebieg `make hypotheses-v2 CONFIRMATORY=1`.

## 0. Odpowiedź w skrócie

1. **Istotności nie da się zagwarantować, można natomiast zagwarantować moc.**
   - Wynik zależy od tego, jak jest naprawdę. My możemy tylko zaprojektować test, który z prawdopodobieństwem ≥ 0,8 kończy się wynikiem istotnym w jedną ze stron:
     - potwierdzenie;
     - istotny brak trendu, wykazany testem równoważności TOST;
     - istotny trend przeciwny.
   - To wymóg K4 i główny cel tego planu.
   - Na danych v1 nie wolno szukać istotności ponownie (rozdz. 7).
2. **H1 da się rozstrzygnąć, ale tylko przy trzech warunkach naraz.** Wszystkie sprawdzamy przed testem (bramki B3–B5):
   - instrument stanowiska ma czułość ≥ 0,7 i swoistość ≥ 0,98 (`stance_v1` ma czułość 0,21);
   - udział `challenges` wśród jednostek ze stanowiskiem wynosi co najmniej 10%;
   - analiza obejmuje 55–77 tys. jednostek (posty i komentarze), żeby wykryć SESOI, a 77–107 tys., żeby z mocą 0,8 wykazać także brak trendu (TOST). Zakres wynika z efektu klastrów DEFF 2–2,8; wartość 2,8 wynika z błędu standardowego v1.

   Z obecnym instrumentem moc nie przekracza 0,49 nawet przy 70 tys. jednostek.
3. **H2 w obecnym brzmieniu nie da się rozstrzygnąć na polskiej Wikipedii.**
   - Źródła alternatywne to 0,15–0,75% nowych przypisów.
   - Test potrzebuje 46–227 tys. efektywnych dodań (134–668 tys. linków przy efekcie klastrów rewizji), a rama v2 da szacunkowo kilka tysięcy.
   - H2 trzeba więc zastąpić słabszą wersją jako testem głównym, a oryginał zostawić jako opis.
4. **Słabsze hipotezy z mocą ≥ 0,8 istnieją dla obu pytań** (rozdz. 3):
   - H1: wskaźnik źródeł zamiast stanowiska, poziom całej dyskusji albo uczestnictwo;
   - H2: źródła nieeksperckie zamiast alternatywnych, porównanie z grupą kontrolną, granica udziału, odźwiernictwo.
5. **Bramka mocy wybiera test główny.**
   - Reguła zapisana przed danymi: testem głównym zostaje pierwszy wariant z drabiny (rozdz. 3), który ma moc ≥ 0,8.
   - Moc liczymy z liczebności, jakości instrumentu i parametrów niezależnych od trendu.
   - Na dwa testy główne stosujemy Holma, a reszta drabiny to testy drugorzędne (rozdz. 4).
6. **Koszt.**
   - Ludzie: 0 godzin, opcjonalnie około 1 godziny na niezależne sprawdzenie stanowiska.
   - Sesje AI: około 30 przebiegów agenta.
   - Pobieranie danych: kilka do kilkunastu godzin.
   - Całość: około 2 tygodnie.

## 1. Skąd te liczby

### 1.1. Wartości planistyczne z v1

Liczone tylko poziomy i liczebności, bez trendów. Wszystkie liczby z rozdz. 1 i 3 odtwarza `uv run python scripts/17_power_analysis.py --plan`, który zapisuje `annotations/hypotheses_v2/power_plan_values.json` i `power_plan.csv`.

| Wielkość | Wartość | Źródło |
|---|---|---|
| Udział `challenges` wśród postów ze stanowiskiem | 0,05: 4 z 78, wszystkie 4 z r/conspiracy | etykiety gold v1 (157 postów) |
| `stance_v1` na teście | precyzja 0,80, czułość 0,21, swoistość ≈ 0,99 | test v1 (216 postów, 42 `challenges`) |
| Posty o tematach konsensusu w ramie v1 | 2072 w latach 2005–2018, czyli 3–11% postów | rama v1: science, skeptic, conspiracy, 1 dzień w miesiącu |
| GLiNER jako wskaźnik źródeł alternatywnych | czułość 0,81, swoistość 0,77; udział prawdziwy po korekcie 0,36 (widziany 0,44) | audyt H1-B v1 (258 postów) i test v1 |
| Efekt klastrów (DEFF) w H1 | 2,8, wynikający z błędu standardowego trendu H1-B (0,0116 na rok przy 5154 postach) | test v1 |
| Źródła alternatywne według domeny | 0,75% dodanych linków | 8 stron v1, 2020–2026 (1341 linków) |
| Źródła alternatywne według właściciela konta | 0,15%, bo 8 z 10 trafień domenowych to konta instytucji | `scripts/10` v1 |
| Źródła nieeksperckie (media, platformy, inne) | 43% dodanych linków, 49% bez rewizji masowych | 8 stron v1 |
| Dodane linki na stronę i rok | 24 na dużych stronach v1, na losowych artykułach v2 zapewne kilka razy mniej | v1 |
| Efekt klastrów rewizji (DEFF) dla źródeł nieeksperckich | 14 dla wszystkich rewizji, 2,9 bez rewizji z ponad 20 linkami (importy, tłumaczenia) | v1, ICC metodą ANOVA |

### 1.2. Wzór mocy

Trend logistyczny udziału p w latach o wariancji roku var(t) daje statystykę:

z = β_obs · √(N · p_obs · (1 − p_obs) · var(t) / DEFF)

gdzie:
- p_obs = Se · p + (1 − Sp) · (1 − p) to udział widziany przez instrument;
- β_obs = (Se + Sp − 1) · β · p(1 − p) / (p_obs(1 − p_obs)) to spłaszczony trend;
- moc testu jednostronnego wynosi Φ(z − 1,645), a moc TOST przy braku trendu 2Φ(z − 1,645) − 1.

Wzór sprawdzono symulacją:

| Ustawienie | Symulacja | Wzór |
|---|---|---|
| idealny pomiar, p = 0,15, N = 10 tys. | 0,78 | 0,80 |
| Se 0,6, Sp 0,97, p = 0,10, N = 30 tys. | 0,69 | 0,70 |

SESOI jest bez zmian: dla H1 OR 1,25 w latach 2005–2018, dla H2 OR 1,5 w latach 2020–2026.

### 1.3. Ile jednostek potrzeba (moc 0,8)

**H1, trend stanowiska.** Wartości w komórkach to jednostki potrzebne przy DEFF 2 / DEFF 2,8:

| Instrument | p = 0,05 | p = 0,10 | p = 0,15 |
|---|---|---|---|
| idealny | 54 / 76 tys. | 29 / 40 tys. | 20 / 28 tys. |
| `stance_v1` (Se 0,21, Sp 0,987) | 659 / 919 tys. | 260 / 363 tys. | 167 / 233 tys. |
| Se 0,6, Sp 0,97 | 194 / 271 tys. | 78 / 109 tys. | 50 / 70 tys. |
| **Se 0,7, Sp 0,98 (cel)** | 126 / 176 tys. | **55 / 77 tys.** | **37 / 51 tys.** |
| Se 0,85, Sp 0,98 | 96 / 134 tys. | 43 / 60 tys. | 29 / 40 tys. |

TOST potrzebuje około 1,4 raza więcej jednostek. Dla celu przy p = 0,10 to 77 / 107 tys.

Rama v2 daje najwyżej 72,8 tys. jednostek (13 subredditów × 14 lat × 2 rodzaje × 200). Wczesne lata są puste, więc realnie wychodzi 40–55 tys.

**Wniosek:** H1 jest wykonalne tylko przy dobrym instrumencie, p ≥ 0,10 i podniesionych limitach (krok 1.5).

**H2, trend 2020–2026:**

| Wskaźnik | Udział | N efektywne (DEFF 1) | N linków przy DEFF 2,9 |
|---|---|---|---|
| alternatywne według właściciela (v2, test główny) | 0,15% | 227 tys. | 668 tys. |
| alternatywne według domeny (v1) | 0,75% | 46 tys. | 134 tys. |
| **nieeksperckie (media + platformy + inne)**, bez rewizji masowych | 49% | **1,4 tys.** | **4,0 tys.** (TOST: 5,5 tys.) |

**Wniosek:** rzadkość źródeł alternatywnych blokuje H2 niezależnie od starań. Wskaźnik o udziale około 40% potrzebuje około stu razy mniej danych.

## 2. Plan krok po kroku

Każdy krok podaje: co zrobić, jak, co powstaje, warunek przejścia dalej (bramka), kto i ile czasu. „Zespół” oznacza wspólną decyzję. Role mogą się zmienić.

### Etap 0. Decyzje zespołu (1 spotkanie)

| # | Decyzja | Rekomendacja |
|---|---|---|
| D0.1 | Czy robimy v2 jako nowy cykl (preprint v2), a v1 zostaje bez zmian? | tak |
| D0.2 | Zgoda na pobranie danych v2 (kilka GB, kilka do kilkunastu godzin) | tak, po etapie 2 |
| D0.3 | Drabiny hipotez i kolejność wariantów (rozdz. 3) | jak w rozdz. 3 |
| D0.4 | Czy dopuszczamy około 1 godziny pracy człowieka na ślepe sprawdzenie 100 jednostek stanowiska | tak; to jedyne niezależne odniesienie dla H1 |
| D0.5 | Rozstrzygnięcie szarych stref codebooka z ćwiczenia AI: `personal` przy opiniach, interwiki, reklamy, strony będące przedmiotem rozmowy (R2), rewerty a `edit_about_sources` | decyzja zespołu; wynik → codebook 2.3 |
| D0.6 | Próg „marginalności” źródeł alternatywnych dla H2-S4 | 2% nowych przypisów |
| D0.7 | Instrument stanowiska: dostrojenie lokalnego mDeBERTa albo klasyfikator na jego zamrożonych wektorach (szybszy na CPU) | najpierw klasyfikator na wektorach; dostrojenie, jeśli nie osiągnie celu |

### Etap 1. Przygotowanie pomiaru i mocy, bez danych v2 (1–2 dni)

**1.1. Codebook 2.3 i protokół AI 1.1.**
- Wpisać decyzje D0.5 do `codebook/codebook.yaml`, wyrenderować `codebook.md` i dopisać historię zmian.
- Protokół 1.1: nowa wersja `docs/protokol_anotacji_ai.md`, w tym zmienna `consensus_stance` (R14, R15). Wersji 1 nie zmieniamy, bo jej sumy są w `freeze_A.json`.
- Kto: zespół i JP. Czas: pół dnia.

**1.2. Ponowne ćwiczenie protokołu na 253 jednostkach IS** (dwa przebiegi, nowe ziarna; `scripts/26_ai_protocol.py`).
- Bramka B1:
  - K1: κ przebiegów ≥ 0,8;
  - na Wikipedii F1 `cites_source` względem IS rośnie po decyzjach D0.5.

  Jeśli nie rośnie, rozbieżność z IS zostaje opisana jako różnica odczytania, a nie błąd AI.
- Czas: 2 przebiegi agenta, około 1 godziny.

**1.3. Ćwiczenie protokołu dla stanowiska** na 157 postach gold i 277 z próby wzbogaconej (odniesienie planu C).
- Raport: κ przebiegów (K1), F1 `challenges` i κ względem odniesienia planu C.
- Zastrzeżenie: to odniesienie powstało z preannotacji AI zweryfikowanych przez JP, więc zgodność jest zawyżona.
- Opcjonalnie (D0.4): jedna osoba koduje 100 losowych jednostek bez podpowiedzi AI. Daje to czułość i swoistość AI względem człowieka.
- Bramka B2: czułość AI dla `challenges` ≥ 0,8 względem odniesienia planu C, a jeśli jest sprawdzenie przez człowieka, także względem niego. Inaczej nie ma sensu uczyć instrumentu na tych etykietach.
- Czas: 4 przebiegi agenta, opcjonalnie 1 godzina człowieka.

**1.4. Realistyczna analiza mocy w repozytorium.**
- Rozszerzyć `scripts/17_power_analysis.py` o czułość i swoistość instrumentu, DEFF oraz tabele z rozdz. 1.3, ze wzorem z rozdz. 1.2 i kontrolą symulacją.
- Wynik: `annotations/hypotheses_v2/power_plan.csv`. Liczby z tego dokumentu stają się odtwarzalne.
- Czas: pół dnia.

**1.5. Parametry ramy pod moc** (zmiana `config.yaml`, wpis w „Zmianach”):

| Parametr | Było | Będzie | Po co |
|---|---|---|---|
| H1 `units_per_cell` | 200 | 500 (komentarze), posty bez limitu | etykiety są automatyczne, więc dodatkowe jednostki kosztują tylko obliczenia; N ≥ 77 tys. |
| H1 `comments_per_post` | 20 | 30 | więcej komentarzy z wczesnych lat |
| H1 `days_per_month` | 2 | 4 | więcej postów z małych subredditów i wczesnych lat |
| H2 `pages_per_group` | 400 | wszystkie artykuły drzew kategorii albo tyle, ile wskaże krok 3.1 | H2-S1 potrzebuje ≥ 5,5 tys. linków |
| H2: rewizje z ponad 20 linkami | w analizie | wyłączone z analizy głównej, raportowane osobno | DEFF z 14 do około 3 |
| Jednostki v1 | – | wyłączone z testów v2: dni ramy v1 na Reddicie i 8 stron v1 na Wikipedii | hipotezy zainspirowane v1 testujemy na rozłącznych danych |

### Etap 2. Preregistracja zmian (pół dnia)

**2.1.** W `docs/hipotezy_v2.md`, w sekcji „Zmiany”, dopisać datowany wpis:
- parametry z kroku 1.5;
- drabiny hipotez z rozdz. 3 z dokładnym brzmieniem, wskaźnikiem, testem i SESOI;
- regułę bramki mocy i wielokrotności (rozdz. 4);
- kryteria K1–K10 (rozdz. 5);
- protokół AI 1.1 i codebook 2.3 jako źródło etykiet uczących;
- zakaz liczenia trendów przed przebiegiem potwierdzającym.

Szkic wpisu jest w rozdz. 8.

**2.2.** Commit wpisu, `config.yaml`, codebooka, protokołu i kodu z listy `PREREGISTRATION_V2` (skrypty pobierające odmówią startu bez commitu) oraz tag `prereg-v2.1`. Push.

**Bramka B3:** zatwierdzenie przez zespół. Po tym kroku niczego z listy nie zmieniamy bez nowego wpisu.

### Etap 3. Próbne pobranie samych liczebności (pół do 1 dnia)

**3.1. H2:** `make h2-history` z `LIMIT` na około 50 losowych artykułach z każdej grupy.
- Skrypt raportuje tylko liczby:
  - pierwsze dodania na artykuł i rok;
  - rewizje z linkami;
  - udział rewizji masowych.

  Kategorii linków nie raportuje.
- Z tych liczb: ile artykułów potrzeba na ≥ 5,5 tys. linków w grupie zdrowia po wyłączeniach.

**3.2. H1:** liczba postów i komentarzy o tematach konsensusu na subreddit i rok w wylosowanych dniach, bez stanowiska i źródeł. Wynik: przewidywane N po limitach z kroku 1.5.

**Bramka B4:**
- Gdy przewidywane N dla H1 jest poniżej 77 tys., H1-A traci szansę na moc 0,8 przy DEFF 2,8. Bramka mocy (krok 7) i tak zdecyduje na danych, ale wtedy zespół wie z góry, że testem głównym zostanie raczej wariant słabszy.
- Gdy dla H2 zabraknie linków nawet przy pełnych drzewach kategorii, dokładamy kategorie lub drugą wiki tylko nowym wpisem przed pobraniem. Inaczej H2-S1 schodzi na H2-S4.

### Etap 4. Pełne pobranie v2 (1–2 dni, zgoda D0.2)

- **Komendy:**
  - `make h2-frame`, `make h2-history`, `make h1-frame` z parametrami z kroku 1.5;
  - potem `make h2-links ARGS="--fetch-rsp --resolve-youtube"`.
- **Wyłączenie jednostek v1** zgodnie z krokiem 1.5, zapisane w manifeście.
- **Zamrożenie:** sumy kontrolne ramy w `fetch_log.json`, a log dodany do gita.

### Etap 5. Etykiety automatyczne (1–2 dni, bez pracy ludzi)

**5.1. Zbiory (przed jakimkolwiek etykietowaniem, ziarno w manifeście).**
- Zbiór uczący stanowiska: 3000 jednostek, warstwowo, z nadreprezentacją subredditów sceptycznych, żeby było dość `challenges`.
- Zbiór oceny: preregistrowana próba walidacyjna, 360 jednostek w trzech okresach, rozłączna z uczącym.
- Próba analityczna: cała reszta.

**5.2. Protokół AI 1.1, dwa ślepe przebiegi w świeżych agentach**, jak w przebiegu B ćwiczenia:
- najpierw zbiór oceny, potem uczący (około 26 przebiegów);
- zgoda obu przebiegów daje etykietę pewną, a niezgoda trafia do kategorii „niepewne”, która nie wchodzi do uczenia;
- etykiety zamrażamy sumą kontrolną (N7).

**5.3. Właściciele kont H2 (A5).**
- Źródła etykiet:
  - rejestr oficjalnych kont instytucji;
  - dwa przebiegi anotatora AI według `owners.yaml`.
- Reguła dwóch granic z v2.

**5.4. Udział bazowy p.**
- Skrypt podaje **jeden** łączny udział `challenges` w zbiorze oceny, bez podziału na okresy i subreddity, żeby nie zdradzić trendu.

**Bramka B5 (K1, K2):**
- κ przebiegów ≥ 0,8 dla stanowiska i właścicieli kont;
- κ wskaźników błędu anotatora AI i instrumentu < 0,4 tam, gdzie jest odniesienie IS.

### Etap 6. Instrument stanowiska i zamrożenie (1 dzień)

**6.1.** Uczenie na pewnych etykietach zbioru uczącego. Najpierw regresja logistyczna na zamrożonych wektorach lokalnego mDeBERTa, a jeśli to za mało, dostrojenie mDeBERTa (D0.7).
- Progi wyznaczamy walidacją krzyżową **wewnątrz zbioru uczącego**.
- Commit instrumentu i progów (`TUNED = True`).

**6.2.** Jedna ocena na zbiorze oceny (`14 --evaluate`). Mierzymy czułość, swoistość, F1 `challenges`, κ, a do tego błąd różnicowy w trzech okresach.

**6.3. Bramka B6 (K3).** Wszystkie warunki naraz:
- czułość ≥ 0,7, swoistość ≥ 0,98, F1 ≥ 0,5 i κ ≥ 0,4;
- test grup znanych w zapisanym kierunku (p < 0,05): udział `challenges` w r/conspiracy i r/climateskeptics wyższy niż w r/science i r/climate;
- różnica czułości między okresami < 0,15.

Jeśli bramka nie przejdzie, H1-A przechodzi do opisu, a testem głównym zostaje H1-S1 (rozdz. 4). Instrumentu nie poprawiamy po ocenie. Każda poprawka oznacza nowy zbiór oceny i nowy wpis.

### Etap 7. Bramka mocy (pół dnia, przed testem)

**7.1. Moc każdego wariantu z drabiny.** Liczymy wzorem z kroku 1.4, wstawiając:
- N z próby analitycznej;
- czułość i swoistość z kroku 6.2;
- p z kroku 5.4;
- DEFF z ICC wskaźnika w klastrach (posty, rewizje), liczonym bez zmiennej czasu.

Żaden z tych parametrów nie zdradza trendu. To odpowiednik ślepego przeliczenia liczebności w badaniach klinicznych.

**7.2. Wybór testu głównego.** Testem głównym zostaje pierwszy wariant drabiny z mocą ≥ 0,8 dla wykrycia SESOI i dla TOST (rozdz. 4). Wybór zapisujemy w `annotations/hypotheses_v2/power_gate.json` i commitujemy **przed** krokiem 8.

### Etap 8. Jeden przebieg potwierdzający (pół dnia)

- **Uruchomienie:** `make hypotheses-v2 CONFIRMATORY=1`. Skrypt sprawdza tag, `power_gate.json` i sumy etykiet.
- **Werdykt:** dla każdego testu reguła v2: potwierdzona, obalona przez brak trendu (TOST), obalona przez trend przeciwny albo nierozstrzygnięta.
- **Wielokrotność:**
  - Holm na dwóch testach głównych (H1, H2);
  - Holm w obrębie każdej rodziny dla testów drugorzędnych.
- **Krzywe specyfikacji i analizy wrażliwości:** raportujemy wszystkie, ale nie zmieniają werdyktu.

### Etap 9. Raport (2–3 dni)

- **Preprint v2:** werdykty, moc zrealizowana, reguła bramki i to, który wariant został testem głównym oraz dlaczego.
- **Ujawnienie:**
  - które etykiety pochodzą od AI i z jakiego protokołu;
  - czy było sprawdzenie przez człowieka (N8).
- **Dyskusja:** wariant słabszy to inne twierdzenie niż hipoteza pierwotna, więc piszemy wprost, co wynik mówi o pierwotnym pytaniu, a czego nie mówi.

## 3. Drabiny hipotez

Wszystkie warianty zapisujemy przed danymi v2. Każdy ma tę samą regułę decyzji, z TOST, bez zmiany SESOI ani α.

### 3.1. H1: zaufanie do konsensusu naukowego (Reddit 2005–2018)

| Wariant | Twierdzenie | Wskaźnik i test | Moc (warunki) | Słabość |
|---|---|---|---|---|
| **H1** (v2, pierwotna) | W społecznościach rośnie udział jednostek podważających konsensus | `challenges` z `stance_v2`, logit z efektami stałymi subredditu, SESOI 1,25 | przy Se 0,7, Sp 0,98 i p = 0,10: wykrycie wymaga 55 / 77 tys., TOST 77 / 107 tys. (DEFF 2 / 2,8); ze `stance_v1` moc ≤ 0,49 | brak |
| **H1-S1** | W społecznościach rośnie udział jednostek ze źródłami alternatywnymi wśród jednostek z powołaniem | GLiNER (źródła; czułość 0,81, swoistość 0,77), ten sam model; spadek udziału źródeł konsensusu tylko jako drugi wskaźnik i tylko wtedy, gdy przejdzie audyt trafności (J > 0,2) | wykrycie wymaga 35 / 48 tys. jednostek z powołaniem, TOST 48 / 67 tys. (DEFF 2 / 2,8); przy 70 tys.: 0,91 i 0,82 | pośrednia miara zaufania (źródła, nie postawy); v1 sugeruje wynik „brak wzrostu” |
| **H1-S2** | W całej dyskusji o nauce, łącznie z napływem nowych społeczności, rośnie udział jednostek ze źródłami alternatywnymi | ten sam wskaźnik, logit **bez** efektów stałych, z wagami ramy | jak H1-S1, gdy efekt = SESOI; gdy powtórzy się zmiana z eksploracji v1 (OR 1,65), wykrycie wymaga tylko 7–10 tys. | twierdzenie o populacji, nie o zmianie postaw; zmiana składu jest częścią efektu i trzeba to napisać |
| **H1-S3** | Rośnie udział dyskusji o tematach konsensusu prowadzonych w społecznościach kwestionujących konsensus (r/conspiracy, r/climateskeptics) | liczba jednostek o tematach z `topics.yaml` według subredditu, **bez etykiet**, cała rama | wykrycie 21,5 tys., TOST 30 tys. (DEFF 1,5); przy 30 tys.: 0,90 i 0,80 | mierzy uczestnictwo, nie postawy; kierunek niepewny, bo rosną też subreddity ogólne |

**Uwagi:**
- r/skeptic to społeczność sceptycyzmu naukowego (prokonsensusowa), więc nie wchodzi do grupy kwestionującej.
- H1-S2 i H1-S3 są zainspirowane v1, dlatego testujemy je na jednostkach rozłącznych z v1 (krok 1.5).

### 3.2. H2: źródła alternatywne (polska Wikipedia, artykuły o zdrowiu)

| Wariant | Twierdzenie | Wskaźnik i test | Moc (warunki) | Słabość |
|---|---|---|---|---|
| **H2** (v2, pierwotna) | W latach 2020–2026 rośnie udział pierwszych dodań linków do kont ekspertów niezależnych, influencerów i anonimów | `alt_owner`, logit z efektami stałymi strony, SESOI 1,5 | potrzeba 227–668 tys. linków; przy 4–10 tys. moc 0,07–0,13 | praktycznie nierozstrzygalna; zostaje jako opis |
| **H2-S1** | W latach 2020–2026 rośnie udział źródeł nieeksperckich (media, platformy, inne) w pierwszych dodaniach przypisów | kategoria domeny (`domains.yaml`) po decyzjach D0.5, logit z efektami stałymi strony, bez rewizji masowych, SESOI 1,5 | wykrycie 4,0 tys. linków, TOST 5,5 tys. (DEFF 2,9); przy 6 tys.: 0,92 i 0,84; przy błędzie kategorii 5%: 4,9 i 6,8 tys. | szerszy konstrukt, „odchodzenie od źródeł eksperckich”, a nie „źródła alternatywne” |
| **H2-S2** | W artykułach o zdrowiu udział źródeł nieeksperckich jest wyższy niż w grupie kontrolnej (matematyka, fizyka, architektura) | porównanie przekrojowe, 2020–2026, logit z błędami grupowanymi po stronie, różnica i TOST | ≈ 1,0 przy 2 tys. linków na grupę, gdy różnica wynosi 43% wobec 30% (założenie) | nie mówi nic o zmianie w czasie |
| **H2-S3** | Linki nieeksperckie są usuwane szybciej niż eksperckie (odźwiernictwo) | model Coxa, czas do usunięcia, HR ≥ 1,25 | 0,8 przy 506 usunięciach (HR 1,25) albo 154 (HR 1,5) | inne pytanie: o reakcję społeczności, nie o trend |
| **H2-S4** | Źródła alternatywne (według właściciela) to mniej niż 2% pierwszych dodań w artykułach o zdrowiu | jednostronny test granicy udziału z błędem z bootstrapu klastrów | ≈ 1,0 przy 1,5 tys. linków dla udziału według właściciela; 0,95 dla udziału według domeny (DEFF 2,9) | wynik o poziomie, nie o trendzie; próg D0.6 musi być ustalony przed danymi |
| **H2-S5** (pomiarowa) | Co najmniej 25% linków „alternatywnych według domeny” prowadzi do kont instytucji | dokładny test dwumianowy na kontach z A5 | 0,75 i 0,82 przy 20 i 30 linkach, gdy udział wynosi 0,5; ≈ 1,0, gdy 0,8 jak w v1 | wynik metodologiczny; zainspirowany v1 (8 z 10), więc bez 8 stron v1 |

## 4. Reguła wyboru testu głównego i wielokrotność

1. **Drabiny w zapisanej kolejności.**
   - H1: H1 → H1-S1 → H1-S2 → H1-S3.
   - H2: H2 → H2-S1 → H2-S2 → H2-S4.

   Kolejność idzie od twierdzenia najbliższego hipotezie pierwotnej do najsłabszego, **nie** według spodziewanego kierunku wyniku.
2. **Wybór.** Testem głównym rodziny zostaje pierwszy wariant, który:
   - przeszedł swoje bramki trafności (B6 dla stanowiska, B5 dla etykiet);
   - ma moc ≥ 0,8 dla wykrycia SESOI i dla TOST (krok 7.1).
3. **Testy główne.** Są dwa (po jednym z H1 i H2), z poprawką Holma.
   - Pozostałe warianty, które spełniają warunki, to testy drugorzędne potwierdzające, z Holmem w obrębie rodziny.
   - Warianty bez mocy raportujemy opisowo.
4. **Nic nie zależy od trendu.** Wybór opiera się wyłącznie na liczebnościach, jakości instrumentu, udziale bazowym i DEFF. Przed krokiem 8 nikt nie liczy trendu żadnego wskaźnika v2. Kod `16` odmawia startu bez `power_gate.json`.
5. **H2-S3 i H2-S5** są zawsze drugorzędne, bo odpowiadają na inne pytanie niż H2.

## 5. Kryteria końcowe (definicja ukończenia)

| # | Kryterium | Próg |
|---|---|---|
| K1 | Stabilność etykiet AI | κ dwóch przebiegów ≥ 0,8 dla każdej zmiennej |
| K2 | Niezależność oceny | ocena przez źródło innej rodziny; κ błędów anotatora i instrumentu < 0,4 przy co najmniej 10 błędach każdego |
| K3 | Trafność instrumentu stanowiska | Se ≥ 0,7, Sp ≥ 0,98, F1 ≥ 0,5, κ ≥ 0,4, grupy znane, błąd różnicowy < 0,15 |
| K4 | Moc przed testem | ≥ 0,8 dla wykrycia i TOST w wybranym wariancie (bramka mocy) |
| K5 | Zamrożenie | tag `prereg-v2.1` przed pobraniem; `power_gate.json` i instrument przed testem; jeden przebieg |
| K6 | Reguła decyzji | jak w v2, z TOST |
| K7 | Wielokrotność | Holm na testach głównych i w rodzinach drugorzędnych |
| K8 | Rozłączność z v1 | hipotezy zainspirowane v1 testowane bez jednostek v1 |
| K9 | Ujawnienie | rola AI w etykietach, protokół, sprawdzenie przez człowieka lub jego brak |
| K10 | Sukces | oba testy główne kończą się wynikiem rozstrzygającym (istotnym w jedną ze stron) przy spełnionych K1–K9 |

K10 to uczciwa definicja celu „wyniki istotne dla obu hipotez”. Kierunku nie da się z góry obiecać: dla H1 dane v1 wskazują raczej na brak spadku zaufania.

## 6. Ryzyka i plan B

| Ryzyko | Sygnał | Co robimy |
|---|---|---|
| Udział `challenges` poniżej 0,10 | krok 5.4 | H1 przechodzi na H1-S1 w bramce mocy; H1 zostaje opisem |
| Anotator AI słabo rozpoznaje `challenges` | bramka B2 | bez uczenia instrumentu na AI; H1 przechodzi na H1-S1 |
| Za mało linków w H2 | krok 3.1 | przed pobraniem: więcej kategorii albo druga wiki (nowy wpis); inaczej H2-S4 |
| Wysoki DEFF (wątki, rewizje) | krok 7.1 | moc liczona z rzeczywistym DEFF; bramka może zejść niżej po drabinie |
| Etykiety AI systematycznie inne niż ludzi (jak na Wikipedii w ćwiczeniu) | B1, B5 | decyzje codebooka (D0.5), raport błędu różnicowego, P3 z kotwicą IS |
| Pokusa „poprawienia” instrumentu po ocenie | – | zakaz; każda zmiana to nowy zbiór oceny i nowy wpis |
| Wynik zgodny z v1: brak spadku zaufania | krok 8 | to też wynik istotny (TOST); raportujemy go jako obalenie |

## 7. Czego nie robimy

- Nie liczymy ponownie testów v1 na innych definicjach, latach czy modelach.
- Nie zmieniamy SESOI, α, okresów ani kierunku testów po zobaczeniu danych.
- Nie wybieramy wariantu po wyniku. Wybór należy do bramki mocy przed testem.
- Nie oceniamy instrumentu na etykietach, na których był uczony.
- Nie przedstawiamy wariantu słabszego jako potwierdzenia hipotezy pierwotnej.

## 8. Szkic wpisu do „Zmian” w `docs/hipotezy_v2.md`

> **[data commitu]. Zmiana 1: moc, etykiety automatyczne i drabiny hipotez.**
>
> **Powód.** Analiza mocy z błędem pomiaru i efektem klastrów (`docs/plan_poprawy_krok_po_kroku.md`, rozdz. 1) pokazała dwie rzeczy:
> - H1 wymaga instrumentu o czułości ≥ 0,7, swoistości ≥ 0,98, udziału `challenges` ≥ 0,10 i 77–107 tys. jednostek przy DEFF 2,8;
> - H2 według właściciela konta wymaga ponad 220 tys. linków, czego rama nie da.
>
> Nie oglądaliśmy żadnych danych v2.
>
> **Zmiany.**
> 1. Parametry ramy według tabeli z kroku 1.5. Jednostki v1 są wyłączone z testów.
> 2. Etykiety walidacyjne i uczące według protokołu AI 1.1 (dwa ślepe przebiegi; codebook 2.3) zamiast kodowania przez dwie osoby. Opcjonalnie 100 jednostek stanowiska kodowanych przez człowieka bez podpowiedzi.
> 3. Kryterium trafności stanowiska K3 według rozdz. 5.
> 4. Drabiny hipotez H1 → H1-S1 → H1-S2 → H1-S3 i H2 → H2-S1 → H2-S2 → H2-S4 z brzmieniem z rozdz. 3. H2-S3 i H2-S5 są drugorzędne.
> 5. Bramka mocy: testem głównym rodziny zostaje pierwszy wariant z mocą ≥ 0,8 dla wykrycia i TOST, liczoną bez danych o trendzie. Wybór jest zapisany w `power_gate.json` przed przebiegiem potwierdzającym.
> 6. Holm na dwóch testach głównych i w rodzinach drugorzędnych.
>
> SESOI, α, okresy i kierunki pozostają bez zmian.

## Literatura uzupełniająca (do sprawdzenia przed cytowaniem)

- Kieser, M., Friede, T. (2003). Simple procedures for blinded sample size adjustment that do not affect the type I error rate. *Statistics in Medicine*, 22(23), 3571–3581.
- Lakens, D., Scheel, A. M., Isager, P. M. (2018). Equivalence testing for psychological research: A tutorial. *Advances in Methods and Practices in Psychological Science*, 1(2), 259–269.
- Schoenfeld, D. A. (1983). Sample-size formula for the proportional-hazards regression model. *Biometrics*, 39(2), 499–503.
- Pozostała literatura: `docs/propozycja_poprawy_eksperymentu.md`.
