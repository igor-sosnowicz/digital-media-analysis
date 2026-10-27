# Instrukcja dokończenia preprintu (stan 27.10.2026)

Ta instrukcja zastępuje listę z 26.10 ([`do_dokonczenia_preprint.md`](do_dokonczenia_preprint.md)). Etapy 0–5 planu ([`plan_dokonczenia.md`](plan_dokonczenia.md)) są zrobione, a wyniki wypchnięte na gałąź `jan-samples`. **Nic nie trzeba już przeliczać.** Zostały tylko prace ludzi: tekst, kompilacja, kontrola i oddanie.

Spis:
1. Stan w skrócie
2. Lista zadań
3. Organizacja pracy: kto, gdzie i jak pisze
4. Zasady pisania i ściąga LaTeX-a
5. Makra: jak ich używać i na co uważać
6. Sekcja po sekcji: plan akapitów
7. Tytuł, autorzy, słowa kluczowe, literatura
8. Kompilacja na Overleafie i limit stron
9. Kontrola końcowa
10. Commit, push, PR
11. Red teaming i slajd
12. Zadania opcjonalne
13. Czego nie robić
14. Harmonogram

## 1. Stan w skrócie

| Element | Stan |
|---|---|
| Dane, codebook, gold, walidacja instrumentów źródeł | gotowe |
| H1-A (`stance_v1`) | jedyny test wykonany: F1 `challenges` 0,33, κ 0,24; warunek trafności niespełniony, więc H1-A jest niemierzalne tym instrumentem |
| H1-B | konsensus tylko opisowo (J = 0,20); źródła alternatywne trafne (J = 0,59), bez trendu (OR 0,99, p = 0,85) |
| H2 | OR 1,47, p = 0,006, ten sam wynik przed przeglądem domen i po nim; według właściciela konta (test dokładny) p = 0,205, czyli artefakt |
| Kontrola wariantu A | gotowa ([`kontrola_wariant_a_2026-10-27.md`](kontrola_wariant_a_2026-10-27.md)) |
| `report/numbers.tex`, 5 tabel, 5 rysunków | gotowe; żadne makro nie ma wartości zastępczej |
| `report/preprint.tex` | 9 ramek `\punkty{}` z faktami i makrami czeka na tekst autorów |
| `make check-preprint` | jedyny zgłaszany problem: „9 ramek do zastąpienia tekstem” |

## 2. Lista zadań

| # | Zadanie | Kto | Czas | Obowiązkowe? | Punkt |
|---|---|---|---|---|---|
| 1 | Tekst 9 ramek | role z pkt 6 | 2–3 dni | tak | 3–6 |
| 2 | Tytuł, autorzy, słowa kluczowe, 2–3 pozycje literatury | lead badawczy | 1–2 godz. | tak | 7 |
| 3 | Kompilacja na Overleafie i limit stron | jedna osoba | 1 godz. | tak | 8 |
| 4 | Kontrola końcowa i lektura PDF-u | jedna osoba plus drugi czytelnik | 1–2 godz. | tak | 9 |
| 5 | Commit, push i PR do `main` | każdy swój tekst; PR: JP | 15 min | tak | 10 |
| 6 | Przygotowanie do red teamingu i slajdu | wszyscy | 1 godz. | tak, przed turniejem | 11 |
| 7 | Sprawdzenie 14 rozbieżności z kontroli | dowolna osoba | 30 min | nie | 12 |
| 8 | Pilotaż stanowiska dwóch osób | IS i JP osobno | 2 × 30 min | nie (tylko opisowo) | 12 |

## 3. Organizacja pracy: kto, gdzie i jak pisze

**Źródłem prawdy jest `report/preprint.tex` w repozytorium.** Kurs ocenia wkład indywidualny po historii commitów, więc każda osoba commituje swoją sekcję sama.

Zalecany sposób pracy jednej osoby nad jej sekcją:

1. Pobierz aktualny stan:
   ```bash
   git switch jan-samples
   ```
   ```bash
   git pull origin jan-samples
   ```
2. Zbuduj paczkę dla Overleafa i załóż **własny** projekt z podglądem (zob. pkt 8, kroki 1–3):
   ```bash
   make check-preprint ZIP=data/preprint_overleaf.zip
   ```
3. Pisz swoją sekcję na Overleafie (podgląd PDF na żywo). Ruszaj tylko tekst między `\section{…}` swojej sekcji a następnym `\section{…}`. Tabel, rysunków i preambuły nie zmieniaj.
4. Gdy sekcja jest gotowa, skopiuj **tylko swój fragment** z Overleafa do `report/preprint.tex` w repozytorium, w to samo miejsce. Przedtem zrób jeszcze raz `git pull`, bo w międzyczasie inne osoby mogły dodać swoje sekcje.
5. Sprawdź, że nic się nie zepsuło (liczba ramek powinna spaść o jedną):
   ```bash
   make check-preprint
   ```
6. Commit i push od razu (pkt 10), żeby kolejna osoba pracowała na aktualnym pliku.

Każdy edytuje inny fragment pliku, więc git scali zmiany sam. Gdyby jednak pojawił się konflikt, zostawcie obie wersje swoich fragmentów i usuńcie znaczniki `<<<<<<<`, `=======` i `>>>>>>>`.

Nie dzielcie `preprint.tex` na osobne pliki sekcji (`\input`): skrypt kontrolny czyta makra i ramki tylko z `preprint.tex`.

## 4. Zasady pisania i ściąga LaTeX-a

### Zasady (ważne dla oceny)

- **Tekst piszecie sami.** Kurs sprawdza preprint Pangramem i ocenia wkład indywidualnie. Asystent AI przygotował tylko punkty i tę instrukcję, nie zdania. Nie wklejajcie tekstu z czatów AI, także „do poprawki”.
- **Każda liczba z wyników to makro** (pkt 5). Nie przepisujcie liczb ręcznie. Wyjątki to stałe projektu: progi (0,5 i 0,4), lata, liczba stron Wikipedii (8) i subredditów, numery commitów.
- **Preregistrowane czy eksploracyjne:** przy każdej analizie piszecie to wprost. Rozstrzyga `docs/hipotezy.md` oraz podział w tabelach (Tab. 4 i Tab. 5 mają te słowa w pierwszej kolumnie).
- **Wynik negatywny to pełny wynik** (zasady kursu). H1-A „niemierzalne”, H1-B „bez trendu” i H2 „artefakt” opisujecie wprost, bez łagodzenia i bez wyolbrzymiania.
- „Brak istotnego trendu” to nie „dowód braku trendu”. W v1 nie robiliśmy testu równoważności (TOST), więc nie piszemy, że zaufanie „się nie zmieniło”.
- Korelacja w czasie to nie przyczynowość; musi to paść w dyskusji.
- **Ujawnień nie wolno skracać ani łagodzić:**
  - etykiety źródeł JP w pilotażu i gold to zatwierdzone etykiety wstępne AI;
  - odniesienie stanowiska to podpowiedzi AI sprawdzone przez jedną osobę (JP), która je znała;
  - przebieg próbny potoku na etykietach AI przed prawdziwym testem;
  - brak pilotażu stanowiska dwóch osób.
- Żadnych nazw użytkowników ani cytatów, po których da się znaleźć autora posta (RODO). Przykład z danych parafrazujcie.
- Styl: pierwsza osoba liczby mnogiej („testowaliśmy”), czas przeszły dla tego, co zrobiono, krótkie akapity z jedną myślą.

### Ściąga LaTeX-a

| Chcę | Piszę |
|---|---|
| nowy akapit | pusta linia |
| procent w tekście | `\%` |
| podkreślnik | `\_` (w nazwach: `\kod{stance\_v1}`) |
| nazwa zmiennej, pliku, commitu | `\kod{source\_types}`, `\kod{7ad9409}` |
| zakres lat lub stron | `2005--2018` (dwa myślniki) |
| myślnik w zdaniu | ` -- ` (ze spacjami) |
| polski cudzysłów | `„tekst”` (bezpośrednio) albo `,,tekst''` |
| wyróżnienie | `\emph{tekst}` |
| symbol w tekście | `$p$`, `$\kappa$`, `$\alpha$`, `$\geq$` |
| odwołanie do tabeli lub rysunku | `Tab.~\ref{tab:h2}`, `Rys.~\ref{fig:h1}` (tylda: bez łamania linii) |
| cytowanie | `\cite{feinstein1990}`, kilka: `\cite{cohen1960,krippendorff2004}` |
| komentarz (nie trafia do PDF-u) | `% tekst` |

Etykiety tabel i rysunków w preprincie: `tab:dane`, `tab:test`, `tab:stance`, `tab:h1`, `tab:h2`, `fig:zgodnosc`, `fig:instrumenty`, `fig:stance`, `fig:h1`, `fig:h2`. Każda z nich musi być przywołana w tekście co najmniej raz.

Klucze literatury, które już są: `cohen1960`, `feinstein1990`, `firth1993`, `kendall1938`, `krippendorff2004`, `laurer2024`, `mcnemar1947`, `passonneau2006`, `zaratiana2024`.

## 5. Makra: jak ich używać i na co uważać

Makra są zdefiniowane w `report/numbers.tex` (plik generowany; nie edytujcie go). Pełna lista z opisem: [`podsumowanie_wynikow.md`](podsumowanie_wynikow.md).

- Po makrze, za którym stoi spacja i słowo, piszcie `{}`: `\resHtwoLinks{} linków`. Bez `{}` LaTeX zje spację („1341linków”). Przed przecinkiem, nawiasem lub kropką `{}` nie jest potrzebne.
- **Makra z przedziałem** zawierają już przedział ufności, np. `\resHtwoOr` = „1,47 [1,09; 1,99]”. Nie dopisujcie drugiego. Dotyczy: `\resHtwoOr`, `\resHtwoBeforeReviewOr`, `\resHoneBConsensusOr`, `\resHoneBAlternativeOr`, `\resTestGlinerRedditCitesF`, `\resTestGlinerRedditMasi`, `\resTestGlinerWikipediaCitesF`, `\resPilotRedditCitesAlpha`, `\resPilotRedditMasiAlpha`, `\resAuditConsensusJ`, `\resAuditAlternativeJ`, `\resControlStanceAgreement`, `\resControlSourcesIsExact`.
- **Makra z jednostką** zawierają już „%” albo „pp”: `\resErrorsVoneUrlShare`, `\resPlanCStanceAutoShare`, `\resPlanCAiChanged`, `\resHoneBConsensusShare…`, `\resHoneConspiracyShare…`, `\resHoneBAlternativeShift…`, `\resControl…`.
- **Makra słowne** wstawiają całe wyrażenia, więc zdanie musi do nich pasować gramatycznie:
  - `\resHoneAStatus` = „warunek trafności niespełniony: H1-A niemierzalne instrumentem `stance_v1`”;
  - `\resHoneAGate` = „niespełniony”;
  - `\resAuditConsensusValid` = „tylko opis”, `\resAuditAlternativeValid` = „ważny”;
  - `\resHoneAThresholds` = „relevance 0,30, supports 0,30, challenges 0,70”.
- **Uwaga na trzy makra:**
  - `\resPlanCCheckedBy` = „ludzi”. Faktycznie wszystkie wiersze sprawdził jeden człowiek (JP), więc lepiej napisać to wprost, bez makra.
  - `\resPlanCAiChanged` = „0 %”: JP nie zmienił żadnej podpowiedzi AI. To trzeba opisać uczciwie (ryzyko zakotwiczenia na podpowiedzi), a nie ukrywać.
  - `\resHoneAPilotKappa` i `\resHoneAPilotUnits` = „nie zakodowano”. Używajcie ich tylko w zdaniu, w którym to pasuje, albo napiszcie wprost, że pilotażu stanowiska dwóch osób nie było.
- Makra trendu H1-A (`\resHoneAChallengesOr`, `\resHoneASupportsOr`, `\resHoneARelevantPosts` i inne) mają wartość „nie testowano”. W tekście ich nie używajcie, bo trendu H1-A nie liczyliśmy.
- `\resPending` i `\resWaiting` to wartości zastępcze. Nie mogą pojawić się w tekście.

## 6. Sekcja po sekcji: plan akapitów

### Jak zamienić ramkę

Nad każdą ramką są komentarze `% …` z tezami i budżetem stron. Mogą zostać, bo nie trafiają do PDF-u. Zastąpcie **cały blok** od `\punkty{rola}{` do zamykającego `}` własnymi akapitami, a makra i odwołania z punktów przenieście do tekstu.

Przed:
```latex
\punkty{wyniki H2, inżynier analityk}{
\item Test z preregistracji: OR \resHtwoOr{} na rok, $p$ = \resHtwoP{} ...
...
}
```
Po (tylko struktura; treść piszecie sami):
```latex
... OR \resHtwoOr{} ... ($p$ = \resHtwoP) ... (Tab.~\ref{tab:h2}).

... \resHtwoOfficialLinks{} ... (Rys.~\ref{fig:h2}) ...
```

### Długość

Przy czcionce 10 pt i marginesach 2 cm pełna strona samego tekstu to około 750 słów. Rysunki i tabele zajmują razem około 3 stron, bibliografia około 0,4, więc na tekst zostaje około 3,5 strony, czyli **około 2600 słów na cały preprint**. Limity słów poniżej są orientacyjne; rozstrzyga pierwsza kompilacja (pkt 8).

Kolejność pisania: najpierw sekcje 2–5, potem dyskusja, na końcu wprowadzenie i streszczenie, bo one zależą od wyników.

---

### Streszczenie (lead badawczy, do 200 słów, 1 akapit)

**Cel:** czytelnik po samym streszczeniu zna pytanie, dane, metodę i trzy wyniki.

Kolejne zdania:
1. Pytanie: H1 (Reddit, 2005–2018) i H2 (Wikipedia, 2020–2026), obie preregistrowane.
2. Dane: `\resHoneSample` postów z 4 subredditów, `\resHtwoLinks` linków z przypisów 8 stron Wikipedii, gold standard do walidacji.
3. Metoda: instrumenty AI walidowane na gold, jeden test na zamrożonych instrumentach, warunki trafności zapisane przed testem.
4. Wynik H1-A: instrument nie spełnił warunku (F1 `\resHoneATestChallengesF`, κ `\resHoneATestKappa`), więc H1-A jest niemierzalne.
5. Wynik H1-B: brak trendu źródeł alternatywnych w obrębie subredditów; zmiana w całej próbie wynika ze składu.
6. Wynik H2: formalnie istotny, ale `\resHtwoOfficialLinks` z `\resHtwoAlternativeLinks` linków to oficjalne konta WHO i GIS; według właściciela konta efekt znika.
7. Wniosek: lekcja o walidacji pomiaru przed testem trendu.

**Uwagi:** najwyżej 4–5 liczb; bez cytowań i odwołań do tabel. W streszczeniu wystarczą `\resHtwoP` i `\resHtwoExactP`, bez OR z przedziałem, bo jest długi. Słowa liczcie po skompilowaniu (zaznaczyć tekst w PDF-ie i wkleić do licznika).

---

### 1. Wprowadzenie (lead badawczy, około 400 słów, 4 akapity)

**A1. Zjawisko i literatura.** Zaufanie do nauki i sięganie po źródła spoza nauki i mediów w sieci, z 2–3 cytowaniami (pkt 7). Dlaczego Reddit i Wikipedia: dwa różne środowiska (dyskusja a encyklopedia z przypisami).

**A2. Pytania badawcze.** H1 i H2 w brzmieniu z preregistracji (`docs/hipotezy.md`, commit `440b5fb`):
- H1: „w latach 2005–2018 w przestrzeni online maleje zaufanie do konsensusu naukowego”;
- H2: „w latach 2020–2026 użytkownicy częściej odwołują się do alternatywnych źródeł wiedzy”.

Dalej: H1-A (stanowisko wobec konsensusu) to test główny, a H1-B (rodzaj źródeł) to wskaźniki poboczne.

**A3. Problem pomiaru.** W takiej skali da się mierzyć tylko automatycznie, więc wynik testu zależy od tego, czy instrument mierzy to, co opisuje codebook. Stąd walidacja na gold i warunek trafności zapisany przed testem.

**A4. Wkład i struktura.** Cztery elementy wkładu (z ramki), potem jedno zdanie o układzie artykułu.

**Częste błędy:**
- zapowiadanie wyniku („potwierdzamy H2”);
- przeformułowanie hipotez;
- obietnica wniosków przyczynowych.

---

### 2. Dane i próba (inżynier danych, około 300 słów, Tab. 1)

**A1. Źródła.**
- Reddit: archiwum Arctic Shift, 10 subredditów z `config.yaml` (6 polskich spoza tematu nauki, r/reddit.com w 2005 r., r/science, r/skeptic, r/conspiracy), lata 2005–2020.
- Wikipedia: 8 stron przez API MediaWiki, od 2020 r. do października 2026 r.
- Rama: `\resRedditFrame` postów, `\resWikipediaFrame` opisów zmian.

**A2. Próba do annotacji (gold).**
- Losowanie warstwowe po latach (w Wikipedii: rok × sygnał), wagi $N_h/n_h$, stałe ziarno.
- Podział na pilotaż (`\resRedditPilot` + `\resWikipediaPilot`), `dev` i `test`.
- Zakodowane jednostki: Reddit `\resRedditCodedDev`/`\resRedditCodedTest`, Wikipedia `\resWikipediaCodedDev`/`\resWikipediaCodedTest` (dev/test).
- Przywołać `Tab.~\ref{tab:dane}`.
- Po co podział: strojenie tylko na `dev`, jeden test na `test`.

**A3. Próby analityczne.**
- H1: `\resHoneSample` postów z **4** subredditów (r/reddit.com, r/science, r/skeptic, r/conspiracy), do 150 postów na subreddit i rok. To 42 pary subreddit–rok w latach 2005–2020; okres główny to 2005–2018, lata 2019–2020 to wrażliwość. Posty mają wagi.
- Próba wzbogacona r/conspiracy (`\resEnrichedPosts` postów, z wagami włączenia) służyła tylko do walidacji stanowiska, nie do testu trendu.
- H2: jednostką jest link dodany do przypisu (`<ref>`); linki archiwalne rozwijane do oryginału; `\resHtwoLinks` linków; kategoria według domeny (`codebook/domains.yaml`).

**A4. Data statement.**
- regulaminy platform; licencja CC BY-SA Wikipedii;
- brak nazw użytkowników w analizach (RODO);
- surowe dane poza repozytorium (`data/` w `.gitignore`);
- posty usunięte są poza ramą.

**Częste błędy:** mylenie ramy (10 subredditów) z próbą H1 (4 subreddity); opis Wikipedii jako „artykuły” zamiast „rewizje i dodane linki”.

---

### 3. Pomiar: codebook i gold standard (inżynier pipelinu, około 350 słów, Rys. 1)

**A1. Konstrukt i zmienne.** Mierzymy funkcję powołania się na źródło, nie wiarygodność źródła. Zmienne (`codebook/codebook.md`):
- `source_types`: 9 kategorii, czyli `scientific`, `institutional`, `media`, `personal`, `social_blog`, `encyclopedia`, `other`, `unknown` i `none`;
- `cites_source`: wyliczana z typów;
- `edit_about_sources`: tylko Wikipedia;
- `consensus_stance`: 4 wartości (`supports`, `challenges`, `neutral`, `not_applicable`).

**A2. Reguły rozstrzygające.** R2, R3, R9, R10 i R14, każda jednym zdaniem (treść w `codebook/codebook.md`). Do jednej z nich dodajcie przykład z danych, sparafrazowany.

**A3. Procedura.**
- Dwie osoby kodowały pilotaż niezależnie.
- Druga runda przy α < 0,667, `\resPilotDisputes` sporów trafiło do arbitra.
- Gold podzielony na `dev` i `test`, część gold kodowana przez jedną osobę.

**A4. Zgodność.**
- `cites_source` na Reddicie: zgodność `\resPilotRedditCitesAgreement` przy α = `\resPilotRedditCitesAlpha`. Wyjaśnić paradoks rozpowszechnienia: prawie wszystkie posty mają powołanie, więc α spada mimo wysokiej zgodności (`\cite{feinstein1990,krippendorff2004}`).
- Typy źródeł: α MASI `\resPilotRedditMasiAlpha` (`\cite{passonneau2006}`).
- Przywołać `Rys.~\ref{fig:zgodnosc}`.

**A5. Odniesienie stanowiska (plan C) i ujawnienia.**
- Reguła R14 rozstrzygnęła `\resPlanCStanceAutoShare` postów; jej precyzja w kontroli na ślepo: `\resPlanCStanceRulePrecision`.
- Pozostałe posty: podpowiedzi AI sprawdzone przez JP (`\resPlanCAiChecked` postów, zmieniono `\resPlanCAiChanged`).
- Ujawnić, że:
  - JP znał podpowiedzi;
  - etykiety źródeł JP w pilotażu i gold to zatwierdzone etykiety wstępne AI (23.10), więc zgodność IS–JP nie jest niezależna;
  - pilotażu stanowiska dwóch osób nie było.

**Częste błędy:**
- przedstawianie niskiej α jako złej jakości bez wyjaśnienia paradoksu;
- przemilczenie 0 % poprawek;
- „gold standard kodowany przez dwie osoby”, bo nie w całości.

---

### 4. Walidacja instrumentów AI (inżynier pipelinu, około 450 słów, Rys. 2, Rys. 3, Tab. 2, Tab. 3)

To najważniejsza sekcja dla kryterium kursu („sprawdzenie wiarygodności instrumentu AI na danych odniesienia”).

**A1. Instrumenty źródeł i procedura.**
- Trzy instrumenty: reguły v1, model zero-shot i GLiNER (`\cite{zaratiana2024}`).
- Wszystkie zamrożone przed testem (commit `33ff729`), jeden przebieg na części testowej.
- Metryki: F1 dla `cites_source`, MASI dla typów, przedziały bootstrap.

**A2. Reddit.**
- GLiNER: F1 `\resTestGlinerRedditCitesF`, czułość `\resTestGlinerRedditCitesRecall`, MASI `\resTestGlinerRedditMasi`.
- Przewaga nad zero-shot: McNemar $p$ = `\resMcnemarRedditZeroshotGlinerP` (`\cite{mcnemar1947}`).
- Reguły v1 nie czytają linku: `\resErrorsVoneUrlShare` błędów.
- Przywołać `Rys.~\ref{fig:instrumenty}` i `Tab.~\ref{tab:test}`.
- Wniosek: GLiNER wybrany do H1-B.

**A3. Wikipedia i zależność od annotatora.**
- Wynik negatywny: F1 `\resTestGlinerWikipediaCitesF`, dlatego H2 mierzymy po domenach linków, nie modelem.
- MASI wobec IS `\resTestGlinerRedditMasiIS` a wobec JP `\resTestGlinerRedditMasiJP`. Wyższa zgodność z JP może wynikać z tego, że etykiety JP powstały z podpowiedzi AI.

**A4. Instrument stanowiska.**
- `stance_v1`: NLI zero-shot (`\cite{laurer2024}`).
- Warunek trafności z preregistracji: F1 `challenges` ≥ 0,5 i κ ≥ 0,4 (`\cite{cohen1960}`) na teście.
- Próba wzbogacona dała `\resStanceTestChallengesPosts` postów `challenges` w teście.
- Strojenie progów na `dev` (`\resHoneADevPosts` postów; progi `\resHoneAThresholds`), commit zamrażający `7ad9409`.
- Jeden test na `\resHoneATestPosts` postach, warunek liczony na `\resHoneAReviewedPosts` sprawdzonych przez człowieka.

**A5. Wynik testu stanowiska.**
- F1 `\resHoneATestChallengesF`, κ `\resHoneATestKappa`; warunek `\resHoneAGate`.
- Interpretacja: precyzja `\resHoneATestChallengesPrecision` przy czułości `\resHoneATestChallengesRecall`. Gdy model wskazuje podważanie, zwykle ma rację, ale większość takich postów pomija.
- Na wszystkich wierszach κ wynosi `\resHoneATestAllRowsKappa`.
- Przywołać `Tab.~\ref{tab:stance}` i `Rys.~\ref{fig:stance}`.

**A6. Kontrole dodatkowe (eksploracyjne) i ujawnienia.**
- Ślepe drugie kodowanie AI potwierdziło `\resControlStanceAgreement` etykiet stanowiska (κ `\resControlStanceKappa`). To stabilność, nie trafność: ten sam model może dwa razy popełnić ten sam błąd.
- Przy źródłach AI zgadzało się z etykietami IS (kodowanymi bez AI) w `\resControlSourcesIsExact` postów (n = `\resControlSourcesIsExactN`).
- Przebieg próbny potoku na etykietach AI przed prawdziwym testem, bez zmian instrumentu i progów.
- Audyt H1-B (J = czułość + swoistość − 1, próg z preregistracji 0,2):
  - konsensus J = `\resAuditConsensusJ` (`\resAuditConsensusValid`, na `\resAuditConsensusPositives` pozytywach);
  - alternatywne J = `\resAuditAlternativeJ` (`\resAuditAlternativeValid`, na `\resAuditAlternativePositives`).

**Częste błędy:**
- przedstawianie kontroli wariantu A jako niezależnej walidacji przez człowieka;
- pominięcie, że F1 0,96 dotyczy tylko `cites_source` na Reddicie;
- brak odwołania do Rys. 2 i Tab. 2.

---

### 5. Wyniki: H1 (inżynier analityk, około 350 słów, Rys. 4, Tab. 4)

**A1. H1-A.**
- Stan: `\resHoneAStatus`.
- Zgodnie z regułą z preregistracji trendu nie liczyliśmy.
- To wynik negatywny co do pomiaru, nie dowód, że zjawiska nie ma.

**A2. H1-B: model i wynik.**
- Ważona regresja logistyczna udziału na rok, z efektami stałymi subredditu, na `\resHoneBCiting` postach z powołaniem. $p$ jednostronne w kierunku hipotezy.
- Konsensus: OR `\resHoneBConsensusOr`, $p$ = `\resHoneBConsensusP`; tylko opis, bo J ≤ 0,2.
- Alternatywne: OR `\resHoneBAlternativeOr`, $p$ = `\resHoneBAlternativeP`.
- Przywołać `Tab.~\ref{tab:h1}`.

**A3. Wrażliwości.** Lata 2005–2020, tylko r/science, tylko r/conspiracy (Tab. 4). Wniosek się nie zmienia.

**A4. Surowe udziały a skład próby.**
- Udział konsensusu: `\resHoneBConsensusShareTwothousandsix` w 2006 r., `\resHoneBConsensusShareLateLow`–`\resHoneBConsensusShareLateHigh` w latach 2016–2018. Na pierwszy rzut oka to kierunek hipotezy.
- Ale udział r/conspiracy w próbie rośnie z `\resHoneConspiracyShareTwothousandeight` do `\resHoneConspiracyShareTwothousandeighteen` (`Rys.~\ref{fig:h1}`).
- Dekompozycja (eksploracyjna): zmiana `\resHoneBAlternativeShiftTotal`, z czego skład `\resHoneBAlternativeShiftComposition`, a wewnątrz subredditów `\resHoneBAlternativeShiftWithin`.

**Częste błędy:**
- „zaufanie się nie zmieniło” (pkt 4: brak TOST);
- opis wskaźnika konsensusu jak testu;
- pominięcie, że dekompozycja jest eksploracyjna.

---

### 5. Wyniki: H2 (inżynier analityk, około 300 słów, Rys. 5, Tab. 5)

**A1. Test z preregistracji.**
- OR `\resHtwoOr` na rok, $p$ = `\resHtwoP`.
- Model z efektami stałymi strony korzysta tylko ze stron, na których pojawił się choć jeden link alternatywny: `\resHtwoModelLinks` z `\resHtwoLinks` linków.
- Ten sam wynik przed przeglądem domen: `\resHtwoBeforeReviewOr`, $p$ = `\resHtwoBeforeReviewP`.

**A2. Na czym opiera się wynik.**
- Tylko `\resHtwoAlternativeLinks` linków alternatywnych, na `\resHtwoAlternativePages` stronach.
- Preregistrowane wrażliwości są nieistotne: bez strony COVID-19 $p$ = `\resHtwoWithoutCovidP`, bez roku 2020 (Tab. 5).
- Permutacja lat ($p$ = `\resHtwoPermutationP`) jest **eksploracyjna**. Ramka zestawia ją z wrażliwościami, ale w Tab. 5 stoi w części eksploracyjnej, więc tak ją opiszcie.

**A3. Sprawdzenie pomiaru (eksploracyjne).**
- `\resHtwoOfficialLinks` linków to oficjalne konta WHO i GIS w serwisach społecznościowych; link WHO dodano `\resHtwoWhoRepeats` razy.
- Według właściciela konta (`codebook/owners.yaml`) zostają `\resHtwoByOwnerLinks` linki, test dokładny $p$ = `\resHtwoExactP`.
- Przywołać `Rys.~\ref{fig:h2}` i `Tab.~\ref{tab:h2}`.

**A4. Werdykt.** Formalnie potwierdzona, merytorycznie artefakt klasyfikacji po domenie. Analizy po właścicielu są eksploracyjne, więc nie zastępują testu z preregistracji, tylko pokazują, na czym on stoi.

**Częste błędy:** „H2 obalona”, bo formalnie nie jest; pominięcie małej liczby zdarzeń (10 linków).

---

### 6. Dyskusja i ograniczenia (lead i analityk, około 450 słów, 4–5 akapitów)

**A1. Co dane rozstrzygają.**
- W obrębie subredditów nie ma wzrostu źródeł alternatywnych (H1-B).
- H2 nie świadczy o zmianie zachowań redaktorów Wikipedii.

**A2. Czego nie rozstrzygają.** H1-A (instrument nie przeszedł walidacji); wskaźnik konsensusu tylko opisowy; brak testu równoważności.

**A3. Lekcja o pomiarze.**
- Domena to nie wydawca (konta WHO w serwisach społecznościowych).
- Skład próby zmienia się w czasie (r/conspiracy).
- Walidacja przed testem zmieniła odczytanie obu hipotez.
- Precyzja bez czułości nie wystarcza do mierzenia trendu.

**A4. Ograniczenia** (wszystkie, najlepiej w jednym akapicie):
- odniesienie stanowiska z podpowiedzi AI sprawdzonych przez jedną osobę znającą podpowiedzi, przy 0 % poprawek;
- brak pilotażu stanowiska dwóch osób;
- etykiety JP w gold wspomagane AI;
- przebieg próbny przed testem;
- część gold kodowana przez jedną osobę;
- korelacja w czasie to nie przyczynowość;
- zmiany populacji w obrębie subredditów;
- tylko 8 stron Wikipedii i 10 linków alternatywnych.

**A5 (krótko). Dalsze prace.**
- Instrument stanowiska trenowany na etykietach ludzi.
- Niezależna zgodność dwóch osób.
- Preregistracja v2 (`docs/hipotezy_v2.md`) z analizą mocy i testem równoważności.

---

### 7. Odtwarzalność, dane i użycie AI (inżynier danych i wszyscy, około 200 słów)

**A1. Odtwarzalność.**
- Repozytorium `github.com/igor-sosnowicz/digital-media-analysis`.
- Polecenia `make` od danych do pakietu wyników, np. `make hypotheses CONFIRMATORY=1` i `make preprint-package`.
- Preregistracja i jej datowane zmiany w `docs/hipotezy.md`; commit zamrażający `7ad9409`.
- Lokalne modele otwarte z przypiętymi rewizjami.

**A2. Dane.** Odwołanie do data statement z sekcji 2; co jest w repozytorium (identyfikatory, etykiety), a czego nie ma (surowe teksty).

**A3. Użycie AI.** Wszystkie punkty z ramki, bez skracania: asystent kodu Claude.
- kod i testy;
- etykiety wstępne źródeł JP, zatwierdzone przez JP;
- podpowiedzi etykiet stanowiska, audytu, przyczyn błędów i domen, sprawdzone przez JP;
- ślepa kontrola etykiet;
- przebieg próbny;
- pakiet wyników, punkty do tekstu i ta instrukcja.

Zdanie „tekst artykułu napisali autorzy” wolno zostawić tylko wtedy, gdy to prawda.

## 7. Tytuł, autorzy, słowa kluczowe, literatura

W `report/preprint.tex`:
- **Tytuł** (`\title{[Tytuł]}`): lead badawczy. Dobrze, gdy mówi o wyniku lub metodzie, np. o walidacji pomiaru przed testem trendu, a nie tylko o temacie. Najwyżej około 15 słów.
- **Autorzy** (`\author{Jan Poręba \and Igor Sosnowicz}`): dopiszcie pozostałe osoby zespołu, każdą przez `\and`.
- **Słowa kluczowe:** 4–6, jedna linia tuż po `\end{abstract}`:
  ```latex
  \noindent\textbf{Słowa kluczowe:} ..., ..., ...
  ```
- **Literatura do wprowadzenia** (2–3 pozycje o zaufaniu do nauki w sieci i o dezinformacji):
  1. Szukajcie w Google Scholar; wybierajcie artykuły recenzowane, najlepiej nowsze niż 2015 r.
  2. Każdą pozycję sprawdźcie w samym źródle: autorzy, rok, tytuł, czasopismo, tom, strony. Nie bierzcie opisów bibliograficznych z czatów AI, bo bywają zmyślone.
  3. Dopiszcie przed `\end{thebibliography}` w tym samym formacie co istniejące pozycje:
     ```latex
     \bibitem{nazwisko2020} I.~Nazwisko. Tytuł. \textit{Czasopismo}, tom(numer):strony, rok.
     ```
  4. Cytujcie `\cite{nazwisko2020}` we wprowadzeniu. Pozycja, której nikt nie cytuje, i tak pojawi się na liście, więc usuńcie niecytowane.

## 8. Kompilacja na Overleafie i limit stron

Lokalnie nie ma LaTeX-a, więc kompilujemy na Overleafie.

1. Odśwież paczkę (bierze aktualne `preprint.tex`, `numbers.tex` i tylko potrzebne tabele i rysunki):
   ```bash
   make check-preprint ZIP=data/preprint_overleaf.zip
   ```
2. Overleaf: **New Project → Upload Project →** wskaż `data/preprint_overleaf.zip`.
3. **Menu (lewy górny róg) → Compiler: pdfLaTeX**, Main document: `preprint.tex`. Kliknijcie **Recompile** dwa razy, żeby uzupełniły się odwołania `\ref`.
4. Jeśli pojawią się błędy (czerwona ikona przy Recompile), Overleaf pokazuje numer linii. Najczęstsze przyczyny:
   - goły `%` lub `_` w tekście;
   - niedomknięty nawias `{`;
   - literówka w nazwie makra (`Undefined control sequence`).
5. Sprawdźcie liczbę stron w podglądzie PDF. **Cel: najwyżej 7 stron z bibliografią** (limit kursu to 8, zostawiamy zapas).
6. Jeśli jest za długo, tnijcie w tej kolejności:
   1. tekst sekcji, które przekraczają limit słów z pkt 6;
   2. powtórzenia liczb, które są już w tabelach (w tekście zostawcie tylko najważniejsze);
   3. z Tab. 4 kolumny r/science i r/conspiracy (liczby zostają w tekście jako makra);
   4. Rys. 1 (zgodność w pilotażu) zastąpcie jednym zdaniem z makrami.

   Tabel i rysunków nie zmieniajcie ręcznie na Overleafie. Zmiany 3 i 4 robi się w skryptach (`scripts/13_report_tables.py`, `scripts/18_preprint_package.py`): poproście o to asystenta albo JP.
7. **Jedno źródło prawdy:** na Overleafie nie edytujcie `numbers.tex`, `tables/` ani `figures/`. Tekst wraca do repozytorium według pkt 3.

## 9. Kontrola końcowa

1. W repozytorium, z ostatecznym `report/preprint.tex`:
   ```bash
   make check-preprint STRICT=1 ZIP=data/preprint_overleaf.zip
   ```
   Musi wypisać **„Preprint gotowy do oddania.”**. Skrypt sprawdza:
   - czy każde użyte makro jest zdefiniowane w `numbers.tex`;
   - czy żadne makro w tekście ani tabeli nie ma wartości zastępczej;
   - czy nie zostały ramki `\punkty{}` ani `\dopisania{}`;
   - czy istnieją wszystkie tabele i rysunki.
2. Wgrajcie tę paczkę na Overleafa jako nowy projekt, skompilujcie i przeczytajcie PDF. Najlepiej, żeby czytała osoba, która danej sekcji nie pisała. Lista kontrolna:
   - [ ] w PDF-ie nie ma „[czeka …]”, „nie testowano” w tekście, „??” (zepsute `\ref`), „[?]” (zepsute `\cite`) ani „[Tytuł]”;
   - [ ] nie ma sklejonych słów po makrach („1341linków”);
   - [ ] każdy rysunek i każda tabela są przywołane w tekście (lista etykiet w pkt 4);
   - [ ] streszczenie ma najwyżej 200 słów;
   - [ ] H1 i H2 brzmią jak w `docs/hipotezy.md`;
   - [ ] przy każdej analizie wiadomo, czy jest preregistrowana, czy eksploracyjna;
   - [ ] wszystkie ujawnienia z pkt 4 są w tekście (sekcje 3, 4, 6, 7);
   - [ ] nigdzie nie ma „dowodu braku trendu” ani wniosków przyczynowych;
   - [ ] liczby w streszczeniu zgadzają się z wynikami (są makrami);
   - [ ] najwyżej 7 stron;
   - [ ] w tekście nie ma nazw użytkowników.
3. Opcjonalnie: definicje `\punkty` i `\dopisania` oraz komentarze o ramkach w preambule można usunąć, gdy żadna ramka nie została.
4. PDF do oddania: na Overleafie **Download PDF**. Nazwę pliku i miejsce oddania sprawdźcie w zasadach kursu (`AMC-3.pdf`).

## 10. Commit, push, PR

Każda osoba po swojej sekcji:
```bash
git pull origin jan-samples
```
```bash
git add report/preprint.tex
```
```bash
git commit -m "Writes the H2 results section of the preprint"
```
```bash
git push origin jan-samples
```
(W opisie commitu nazwijcie swoją sekcję.)

Na koniec JP tworzy PR z `jan-samples` do `main`, przyciskiem w aplikacji albo na GitHubie (poprzednie PR-y, #4 i #6, są zamknięte). Commit zamrażający `7ad9409` musi zostać w historii, więc przy scalaniu nie róbcie squash ani rebase (wybierzcie „Create a merge commit”).

## 11. Red teaming i slajd

- [`zarzuty_red_teaming.md`](zarzuty_red_teaming.md): przewidywane zarzuty z odpowiedziami i aktualnymi liczbami. Każda osoba powinna umieć odpowiedzieć na zarzuty dotyczące swojej sekcji.
- [`notatka_slajd_pierwszy_wynik.md`](notatka_slajd_pierwszy_wynik.md): układ slajdu, główne zdanie i notatki prelegenta.
- Pytania, które padną na pewno, i kto odpowiada:

  | Pytanie | Kto |
  |---|---|
  | Dlaczego odniesienie stanowiska nie jest niezależne i co znaczy 0 % poprawek? | inżynier pipelinu |
  | Co znaczy „H2 to artefakt”, skoro test jest istotny? | inżynier analityk |
  | Dlaczego α jest niska przy wysokiej zgodności? | inżynier pipelinu |
  | Co zrobiliście przed testem, a co po nim? | lead badawczy |
  | Czy brak trendu w H1-B to brak zjawiska? | inżynier analityk |

## 12. Zadania opcjonalne (nie zmieniają wyników)

**Zadanie 7: 14 rozbieżności z kontroli (8 w stanowisku, 4 w audycie, 2 w źródłach).**
1. Otwórzcie `annotations/sheets/control/human_check.xlsx` (poza gitem).
2. Lista wierszy do sprawdzenia: `annotations/control/control_disagreements.csv` (kolumny: `unit_id`, `reference` czyli etykieta z arkusza, `blind` czyli etykieta ze ślepego kodowania, `task`).
3. Dla każdego wiersza wpiszcie, która etykieta jest poprawna według codebooka.
4. Wynik może trafić do sekcji 6 jako jedno zdanie. Etykiet ani testu nie zmieniamy.

**Zadanie 8: pilotaż stanowiska dwóch osób.** Daje jedyną niezależną zgodność ludzi dla stanowiska, ale **po teście**, więc tylko opisowo.
1. IS i JP osobno kodują puste arkusze `stance_pilot_{IS,JP}.xlsx` (bez podpowiedzi, z kopii w `data/sheets_backup_2026-10-26/`), bez rozmowy o postach.
2. Datowany wpis w `docs/hipotezy.md`: pilotaż wykonany po jedynym teście, eksploracyjny.
3. Import i przeliczenie pakietu:
   ```bash
   make import-stance PHASE=pilot
   ```
   ```bash
   make preprint-package
   ```
   Makro `\resHoneAPilotKappa` pokaże wtedy κ zamiast „nie zakodowano”, a zdania w sekcjach 3 i 6 trzeba dopasować.

Bez tego pilotażu w tekście zostaje ograniczenie „brak pilotażu stanowiska dwóch osób”.

## 13. Czego nie robić

- **Nie uruchamiać ponownie testu stanowiska** (`make validate-stance SPLIT=test FROZEN=1`). Jedyny test jest wykorzystany.
- Nie zmieniać progów `stance_v1`, warunku trafności ani `codebook/domains.yaml` bez datowanego wpisu w `docs/hipotezy.md`. Każda taka zmiana byłaby już tylko eksploracyjna.
- Nie wpisywać liczb ręcznie i nie edytować `report/numbers.tex`.
- Nie wpisywać `verified = 1` za kogoś. To podpis osoby, która sprawdziła wiersze.
- Nie pobierać nowych danych (v2) bez osobnej decyzji zespołu.
- Nie wklejać tekstu z AI do preprintu.

## 14. Harmonogram (propozycja)

| Dzień | Lead badawczy | Inżynier danych | Inżynier pipelinu | Inżynier analityk |
|---|---|---|---|---|
| 1 | literatura, tytuł, słowa kluczowe | sekcja 2 | sekcja 3 | sekcja 5: H2 |
| 2 | szkic wprowadzenia | sekcja 7 (A1–A2) | sekcja 4 | sekcja 5: H1 |
| 3 | wprowadzenie, streszczenie; dyskusja z analitykiem | pierwsza pełna kompilacja, liczba stron | poprawki sekcji 3–4 | dyskusja z leadem |
| 4 | cięcia do 7 stron | kontrola końcowa (pkt 9) | lektura sekcji 5–6 | lektura sekcji 2–4; PR (JP) |

Jeśli zespół ma mniej osób niż ról, jedna osoba bierze dwie role. Kolejność pisania sekcji się nie zmienia.
