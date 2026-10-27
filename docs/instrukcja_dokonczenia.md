# Instrukcja dokończenia preprintu (stan 27.10.2026)

Ta instrukcja zastępuje listę z 26.10 ([`do_dokonczenia_preprint.md`](do_dokonczenia_preprint.md)). Etapy 0–5 planu ([`plan_dokonczenia.md`](plan_dokonczenia.md)) są zrobione, a wyniki wypchnięte na gałąź `jan-samples` (ostatni commit `59b9762`). **Nic nie trzeba już przeliczać.** Zostały tylko prace ludzi: tekst, kompilacja, kontrola i oddanie.

## 1. Stan w skrócie

| Element | Stan |
|---|---|
| Dane, codebook, gold, walidacja instrumentów źródeł | gotowe |
| H1-A (`stance_v1`) | jedyny test wykonany: F1 `challenges` 0,33, κ 0,24; warunek trafności niespełniony, więc H1-A jest niemierzalne tym instrumentem |
| H1-B | konsensus tylko opisowo (J = 0,20); źródła alternatywne trafne (J = 0,59), bez trendu (OR 0,988, p = 0,85) |
| H2 | OR 1,47, p = 0,006, ten sam wynik przed przeglądem domen i po nim; według właściciela konta p = 0,205, czyli artefakt |
| Kontrola wariantu A | gotowa ([`kontrola_wariant_a_2026-10-27.md`](kontrola_wariant_a_2026-10-27.md)) |
| `report/numbers.tex`, tabele, rysunki | gotowe; żadne makro nie ma już wartości zastępczej |
| `report/preprint.tex` | 9 ramek `\punkty{}` z faktami i makrami czeka na tekst autorów |
| `make check-preprint` | jedyny zgłaszany problem: „9 ramek do zastąpienia tekstem” |

## 2. Co zostało: lista zadań

| # | Zadanie | Kto | Czas | Obowiązkowe? |
|---|---|---|---|---|
| 1 | Tekst 9 ramek | role z tabeli w pkt 3 | 2–3 dni | tak |
| 2 | Tytuł, autorzy, słowa kluczowe, 2–3 pozycje literatury | lead badawczy | 1 godz. | tak |
| 3 | Kompilacja na Overleafie i limit stron | jedna osoba | 1 godz. | tak |
| 4 | Kontrola końcowa (`STRICT=1`) i lektura PDF-u | jedna osoba plus drugi czytelnik | 1 godz. | tak |
| 5 | Commit, push i PR do `main` | JP (lub asystent na prośbę) | 15 min | tak |
| 6 | Przygotowanie do red teamingu i slajdu | wszyscy | 1 godz. | tak, przed turniejem |
| 7 | Sprawdzenie 14 rozbieżności z kontroli (`human_check.xlsx`) | dowolna osoba | 30 min | nie |
| 8 | Pilotaż stanowiska dwóch osób | IS i JP osobno | 2 × 30 min | nie (tylko opisowo) |

## 3. Zadanie 1: tekst 9 ramek

### Zasady (ważne dla oceny)

- **Tekst piszecie sami.** Kurs sprawdza preprint Pangramem i ocenia wkład indywidualnie. Asystent AI przygotował tylko punkty, nie zdania. Nie wklejajcie tekstu z czatów AI.
- **Każda liczba to makro**, np. `\resHtwoOr`. Nie przepisujcie liczb ręcznie z PDF-u ani z dokumentów. Pliku `report/numbers.tex` nie edytujecie, bo generuje go `make preprint-package`.
- Gdy po makrze stoi spacja i dalszy tekst, piszcie `\resHtwoLinks{} linków`. Bez `{}` LaTeX zje spację.
- Przy każdej analizie piszecie, czy była **preregistrowana**, czy **eksploracyjna**.
- **Wynik negatywny to pełny wynik** (zasady kursu). H1-A „niemierzalne” i H2 „artefakt” opisujecie wprost, bez łagodzenia i bez wyolbrzymiania.
- Korelacja w czasie to nie przyczynowość; ma to paść w dyskusji.
- Ujawnienia AI nie wolno skracać ani łagodzić: etykiety JP wspomagane przez AI, odniesienie stanowiska z podpowiedzi AI sprawdzonych przez JP, przebieg próbny przed testem.

### Jak zamienić ramkę

1. Otwórzcie `report/preprint.tex` (w repozytorium albo na Overleafie, zob. pkt 5).
2. Nad każdą ramką są komentarze `% …` z tezami i budżetem stron. Mogą zostać, bo nie trafiają do PDF-u.
3. Zastąpcie **cały blok** od `\punkty{rola}{` do zamykającego `}` własnymi akapitami. Makra i odwołania (`Tab.~\ref{tab:h2}`, `Rys.~\ref{fig:h1}`, `\cite{laurer2024}`) przenieście do swojego tekstu.

Przed:
```latex
\punkty{wyniki H2, inżynier analityk}{
\item Test z preregistracji: OR \resHtwoOr{} na rok, $p$ = \resHtwoP{} ...
...
}
```
Po (struktura, treść własna):
```latex
Preregistrowany test H2 ... OR \resHtwoOr{} ... ($p$ = \resHtwoP) ... (Tab.~\ref{tab:h2}).

... \resHtwoOfficialLinks{} ... (Rys.~\ref{fig:h2}) ...
```

### Ramki, role i budżet

Kolejność pisania: najpierw sekcje 2–5, potem dyskusja, na końcu wprowadzenie i streszczenie (one zależą od wyników).

| Ramka (sekcja) | Rola | Strony | Na co uważać |
|---|---|---|---|
| Streszczenie | lead badawczy | 0,3 | do 200 słów; pytanie, dane, trzy wyniki (H1-A niemierzalne, H1-B bez trendu, H2 artefakt) i jedna lekcja |
| 1. Wprowadzenie | lead badawczy | 0,6 | H1 i H2 dosłownie jak w `docs/hipotezy.md`; wkład w 4 punktach; trzeba dobrać 2–3 pozycje literatury (zadanie 2) |
| 2. Dane i próba | inżynier danych | 0,8 | odwołanie do Tab. 1; data statement (regulaminy, CC BY-SA, RODO, dane poza repozytorium) |
| 3. Codebook i gold | inżynier pipelinu | 0,9 | paradoks rozpowszechnienia przy niskiej α (`\cite{feinstein1990}`); ujawnić etykiety JP wspomagane AI; brak pilotażu stanowiska dwóch osób |
| 4. Walidacja | inżynier pipelinu | 1,3 | najdłuższa sekcja; warunek trafności zapisany przed testem i commit `7ad9409`; precyzja 0,80 przy czułości 0,21; kontrola wariantu A jako **eksploracyjna** |
| 5. Wyniki H1 | inżynier analityk | 1,0 | H1-A: trendu nie liczono (reguła z preregistracji); H1-B: efekt składu (r/conspiracy) |
| 5. Wyniki H2 | inżynier analityk | 0,8 | „formalnie potwierdzona, merytorycznie artefakt”; analiza po właścicielu konta jest eksploracyjna |
| 6. Dyskusja | lead i analityk | 0,7 | co dane rozstrzygają, czego nie; pełna lista ograniczeń z ramki; dalsze prace (v2) |
| 7. Odtwarzalność i AI | inżynier danych i wszyscy | 0,3 | ujawnienie AI zgodne z punktami w ramce; zdanie „tekst napisali autorzy” tylko wtedy, gdy to prawda |

Punkty w ramkach zawierają wszystkie fakty i makra, których potrzeba. Dodatkowe uzasadnienia są w [`preprint_szkic.md`](preprint_szkic.md) (tezy i dowody), [`podsumowanie_wynikow.md`](podsumowanie_wynikow.md) i [`zarzuty_red_teaming.md`](zarzuty_red_teaming.md).

## 4. Zadanie 2: tytuł, autorzy, literatura

W `report/preprint.tex`:
- `\title{[Tytuł]}`: wpisać tytuł (lead badawczy). Dobrze, gdy mówi o wyniku, np. o walidacji pomiaru, a nie tylko o temacie.
- `\author{Jan Poręba \and Igor Sosnowicz}`: dopisać pozostałe osoby z zespołu, jeśli są.
- Słowa kluczowe (budżet je przewiduje): jedna linia pod streszczeniem, np. `\noindent\textbf{Słowa kluczowe:} ...`.
- Literatura: w `thebibliography` dopisać 2–3 pozycje o zaufaniu do nauki i dezinformacji online jako `\bibitem{klucz} ...` i cytować je `\cite{klucz}` we wprowadzeniu. Każdą pozycję sprawdźcie w źródle (autorzy, rok, tytuł, czasopismo).

## 5. Zadanie 3: kompilacja na Overleafie

Lokalnie nie ma LaTeX-a, więc kompilujemy na Overleafie.

1. Odśwież paczkę (bierze aktualne `preprint.tex`, `numbers.tex` i tylko potrzebne tabele i rysunki):
   ```bash
   make check-preprint ZIP=data/preprint_overleaf.zip
   ```
2. Overleaf: **New Project → Upload Project →** `data/preprint_overleaf.zip`.
3. **Menu → Compiler: pdfLaTeX**, plik główny `preprint.tex`. Kompilujcie dwa razy (odwołania `\ref`).
4. Sprawdźcie liczbę stron w podglądzie PDF. **Cel: najwyżej 7 stron z bibliografią** (limit kursu to 8, zostawiamy zapas).
5. Jeśli jest za długo, tnijcie w tej kolejności:
   - skróćcie tekst sekcji, które przekraczają budżet z tabeli w pkt 3;
   - z Tab. 4 (`tables/preprint_h1.tex`) usuńcie kolumny r/science i r/conspiracy (liczby zostają w tekście jako makra);
   - Rys. 1 (zgodność w pilotażu) zastąpcie jednym zdaniem z makrami.

   Tabel i rysunków nie zmieniajcie ręcznie na Overleafie, tylko poproście o zmianę w skrypcie (`scripts/13_report_tables.py`, `scripts/18_preprint_package.py`).
6. **Jedno źródło prawdy.** Jeśli piszecie na Overleafie, na końcu pobierzcie `preprint.tex` (Menu → Download → Source) i nadpiszcie nim `report/preprint.tex` w repozytorium. Na Overleafie nie edytujcie `numbers.tex`, `tables/` ani `figures/`. Jeśli wyniki zmienią się w repozytorium, wgrajcie te pliki ponownie.

## 6. Zadanie 4: kontrola końcowa

1. W repozytorium, z ostatecznym `report/preprint.tex`:
   ```bash
   make check-preprint STRICT=1 ZIP=data/preprint_overleaf.zip
   ```
   Musi wypisać **„Preprint gotowy do oddania.”** Skrypt sprawdza:
   - czy każde użyte makro jest zdefiniowane w `numbers.tex`;
   - czy żadne makro w tekście ani tabeli nie ma wartości zastępczej;
   - czy nie zostały ramki `\punkty{}` ani `\dopisania{}`;
   - czy istnieją wszystkie tabele i rysunki.
2. Skompilujcie tę paczkę na Overleafie jeszcze raz i przeczytajcie PDF (najlepiej osoba, która go nie pisała). Lista kontrolna:
   - [ ] w PDF-ie nie ma napisów „[czeka …]”, „??” (zepsute `\ref`) ani „[Tytuł]”;
   - [ ] każdy rysunek i każda tabela są przywołane w tekście;
   - [ ] streszczenie ma najwyżej 200 słów;
   - [ ] przy każdej analizie wiadomo, czy jest preregistrowana, czy eksploracyjna;
   - [ ] H1 i H2 brzmią jak w `docs/hipotezy.md`;
   - [ ] ujawnienie AI zawiera wszystkie punkty z ramki sekcji 7;
   - [ ] najwyżej 7 stron.
3. Opcjonalnie: definicje `\punkty` i `\dopisania` w preambule można usunąć, gdy żadna ramka nie została.

## 7. Zadanie 5: commit, push, PR

```bash
git add report/preprint.tex
git commit -m "Replaces the point boxes in the preprint with the authors' text"
git push origin jan-samples
```

Commit robi każda osoba ze swoim tekstem (kurs ocenia wkład po historii commitów). PR z `jan-samples` do `main` tworzy JP przyciskiem w aplikacji albo na GitHubie (poprzednie PR-y, #4 i #6, są zamknięte). Commit zamrażający `7ad9409` musi zostać w historii, więc nie róbcie squash ani rebase przy scalaniu.

## 8. Zadanie 6: red teaming i slajd

- [`zarzuty_red_teaming.md`](zarzuty_red_teaming.md): przewidywane zarzuty z odpowiedziami i aktualnymi liczbami. Każda osoba powinna umieć odpowiedzieć na zarzuty dotyczące swojej sekcji.
- [`notatka_slajd_pierwszy_wynik.md`](notatka_slajd_pierwszy_wynik.md): układ slajdu, główne zdanie i notatki prelegenta.
- Najtrudniejsze pytania, które padną na pewno:
  - dlaczego odniesienie stanowiska nie jest niezależne;
  - co znaczy „H2 to artefakt”;
  - dlaczego α jest niska przy wysokiej zgodności;
  - co zrobiliście przed testem, a co po nim.

## 9. Opcjonalne (nie zmieniają wyników)

**Zadanie 7: 14 rozbieżności z kontroli (8 w stanowisku, 4 w audycie, 2 w źródłach).** Arkusz `annotations/sheets/control/human_check.xlsx` (poza gitem), wiersze z `annotations/control/control_disagreements.csv`. Wynik może trafić do ograniczeń jako jedno zdanie. Nie zmienia etykiet ani testu.

**Zadanie 8: pilotaż stanowiska dwóch osób.** Daje jedyną niezależną zgodność ludzi dla stanowiska, ale **po teście**, więc tylko opisowo. Kroki:
1. IS i JP osobno kodują puste arkusze `stance_pilot_{IS,JP}.xlsx` (bez podpowiedzi, z kopii w `data/sheets_backup_2026-10-26/`).
2. Datowany wpis w `docs/hipotezy.md`: pilotaż wykonany po jedynym teście, eksploracyjny.
3. `make import-stance PHASE=pilot` i `make preprint-package`; makro `\resHoneAPilotKappa` zamieni wtedy „nie zakodowano” na κ.

Jeśli go nie robicie, w tekście zostaje „nie zakodowano” i ograniczenie „brak pilotażu stanowiska dwóch osób”.

## 10. Czego nie robić

- **Nie uruchamiać ponownie testu stanowiska** (`make validate-stance SPLIT=test FROZEN=1`). Jedyny test jest wykorzystany.
- Nie zmieniać progów `stance_v1`, warunku trafności ani `codebook/domains.yaml` bez datowanego wpisu w `docs/hipotezy.md`. Każda taka zmiana byłaby już tylko eksploracyjna.
- Nie wpisywać liczb ręcznie i nie edytować `report/numbers.tex`.
- Nie wpisywać `verified = 1` za kogoś. To podpis osoby, która sprawdziła wiersze.
- Nie pobierać nowych danych (v2) bez osobnej decyzji zespołu.

## Harmonogram (propozycja)

| Dzień | Co |
|---|---|
| 1 | sekcje 2, 3, 4 (inżynier danych, inżynier pipelinu); tytuł i literatura (lead) |
| 2 | sekcje 5 i 6 (analityk, lead); pierwsza kompilacja na Overleafie i liczba stron |
| 3 | wprowadzenie, streszczenie, sekcja 7; cięcia do 7 stron |
| 4 | kontrola końcowa, commit, PR, przygotowanie do red teamingu |
