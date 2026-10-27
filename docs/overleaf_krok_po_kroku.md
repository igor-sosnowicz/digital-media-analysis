# Preprint na Overleafie krok po kroku (stan 27.10.2026)

Instrukcja do pkt 8 w [`instrukcja_dokonczenia.md`](instrukcja_dokonczenia.md). Opisuje, jak wgrać aktualną wersję preprintu na Overleafa, skompilować ją, aktualizować i pobrać tekst z powrotem do repozytorium.

**Co trafia na Overleafa:** paczka `data/preprint_overleaf.zip` z 12 plikami:
- `preprint.tex`: tekst z ramkami;
- `numbers.tex`: makra z wynikami;
- `tables/`: 5 tabel;
- `figures/`: 5 rysunków.

Wszystkie pliki są w UTF-8 i nie wymagają dodatkowych pakietów spoza standardowej instalacji Overleafa.

## Krok 1. Zbuduj aktualną paczkę

Wybierz **jeden** z trzech sposobów.

### Sposób A: z repozytorium przez `make` (zalecany)

1. Otwórz terminal (Git Bash albo PowerShell) w katalogu repozytorium `digital-media-analysis`.
2. Przełącz się na właściwą gałąź:
   ```bash
   git switch jan-samples
   ```
3. Pobierz najnowsze zmiany:
   ```bash
   git pull origin jan-samples
   ```
4. Zbuduj paczkę:
   ```bash
   make check-preprint ZIP=data/preprint_overleaf.zip
   ```
5. Na końcu wydruku powinna być linia `Paczka Overleaf: data/preprint_overleaf.zip (12 plików)`. Linia „9 ramek … do zastąpienia tekstem” jest na tym etapie normalna.

### Sposób B: z repozytorium bez `make`

Jeśli `make` nie działa, po krokach A2–A3 uruchom:
```bash
uv run scripts/24_check_preprint.py --zip data/preprint_overleaf.zip
```

### Sposób C: bez Pythona, z GitHuba

1. Otwórz `github.com/igor-sosnowicz/digital-media-analysis`.
2. Nad listą plików przełącz gałąź z `main` na **`jan-samples`**. To ważne, bo na `main` nie ma aktualnej wersji.
3. **Code → Download ZIP** i rozpakuj pobrany plik.
4. Wejdź do katalogu `report/`. Zaznacz `preprint.tex`, `numbers.tex` oraz katalogi `tables` i `figures`, kliknij prawym przyciskiem i wybierz **Wyślij do → Folder skompresowany (zip)** (Windows) albo **Kompresuj** (macOS).

   Pliki muszą leżeć w głównym katalogu archiwum, a nie w podkatalogu `report/`. Ta paczka ma więcej tabel i rysunków niż potrzeba, ale to niczemu nie szkodzi.

## Krok 2. Zaloguj się na Overleafa

1. Wejdź na `www.overleaf.com` i zaloguj się na swoje konto (albo je załóż). Konto uczelniane działa tak samo.
2. Darmowy plan wystarcza do kompilacji tego preprintu.

## Krok 3. Utwórz projekt z paczki

1. Na liście projektów kliknij zielony przycisk **New Project** (lewy górny róg).
2. Wybierz **Upload Project**.
3. W okienku przeciągnij plik zip albo kliknij **Select a .zip file** i wskaż:
   - sposób A i B: `digital-media-analysis\data\preprint_overleaf.zip`;
   - sposób C: zip utworzony w kroku 1.C.4.
4. Overleaf rozpakuje archiwum i otworzy projekt. Po lewej, w drzewie plików, powinny być `preprint.tex`, `numbers.tex` oraz foldery `tables` i `figures`.
5. Zmień nazwę projektu, żeby się nie pomylić: kliknij nazwę projektu na górnym pasku i wpisz np. `AMC preprint – 27.10 – [Twoje inicjały]`.

## Krok 4. Ustaw kompilację

1. Kliknij **Menu** (lewy górny róg edytora).
2. W części **Settings** ustaw:
   - **Compiler: pdfLaTeX**;
   - **Main document: preprint.tex**. W sposobie C to ważne, jeśli do paczki trafił też `raport.tex`.
   - **TeX Live version:** zostaw domyślną.
3. Zamknij menu.

## Krok 5. Skompiluj i sprawdź wynik

1. Kliknij **Recompile** (zielony przycisk nad podglądem PDF).
2. Pierwsza kompilacja trwa kilkanaście sekund. Potem kliknij **Recompile** jeszcze raz, żeby uzupełniły się numery tabel i rysunków w odwołaniach.
3. Co powinieneś zobaczyć w PDF-ie:
   - tytuł „[Tytuł]” i autorów;
   - 9 ramek z napisem „Do napisania własnymi słowami (…)” i punktami, w których zamiast makr są już liczby;
   - 5 tabel i 5 rysunków;
   - bibliografię na końcu.
4. Ikona obok **Recompile** (Logs and output files) pokazuje liczbę błędów i ostrzeżeń:
   - **ostrzeżenia** (żółte), np. `Overfull \hbox` albo `Float too large`, nie blokują kompilacji; można je zignorować do czasu cięć;
   - **błędy** (czerwone) oznaczają, że coś trzeba poprawić (tabela w kroku 10). Bez zmian w plikach paczka powinna kompilować się bez błędów.
5. Liczba stron jest pod podglądem PDF albo w pasku przewijania. Na tym etapie, z ramkami zamiast tekstu, nie jest jeszcze miarodajna.

## Krok 6. Praca nad tekstem na Overleafie

1. W drzewie plików kliknij `preprint.tex`.
2. Znajdź swoją sekcję: **Ctrl+F** i np. `\section{Wyniki}`. Możesz też kliknąć dwukrotnie w PDF-ie, a edytor przeskoczy do odpowiedniej linii.
3. Zamień ramkę `\punkty{…}{…}` na swój tekst według pkt 6 instrukcji. Po każdym większym fragmencie kliknij **Recompile** (skrót **Ctrl+Enter**).
4. **Nie edytuj** `numbers.tex` ani plików w `tables/` i `figures/`. Zmiany w nich znikną przy następnej aktualizacji z repozytorium.
5. Liczba słów: **Menu → Word Count** liczy cały dokument. Streszczenie policz osobno: zaznacz jego tekst w PDF-ie i wklej do dowolnego licznika słów.
6. Overleaf zapisuje zmiany automatycznie. Historia jest w **History** (górny pasek).

## Krok 7. Udostępnienie projektu zespołowi (opcjonalnie)

1. Kliknij **Share** (prawy górny róg).
2. Wpisz adres e-mail osoby i wybierz uprawnienia: **Can edit** albo **Can view**.
3. Liczba współpracowników w darmowym planie jest ograniczona; ile osób można dodać, Overleaf pokazuje w tym samym okienku. Jeśli limit nie wystarcza, każdy pracuje we własnym projekcie z tej samej paczki (tak zakłada pkt 3 instrukcji), a tekst łączy się w repozytorium.

## Krok 8. Przeniesienie tekstu z powrotem do repozytorium

Repozytorium jest jedynym źródłem prawdy, a kurs ocenia wkład po commitach, więc tekst z Overleafa musi wrócić do `report/preprint.tex`.

### Sposób zalecany: kopiowanie swojej sekcji

1. W repozytorium pobierz najnowsze zmiany:
   ```bash
   git pull origin jan-samples
   ```
2. Na Overleafie zaznacz w `preprint.tex` tekst swojej sekcji, od linii po `\section{…}` do linii przed następnym `\section{…}`, i skopiuj go (**Ctrl+C**).
3. Otwórz `report/preprint.tex` w edytorze (np. VS Code), zaznacz ten sam fragment (z ramką `\punkty`) i wklej (**Ctrl+V**).
4. Sprawdź, czy liczba ramek spadła o jedną:
   ```bash
   make check-preprint
   ```
5. Commit i push według pkt 10 instrukcji.

### Sposób alternatywny: cały plik

Tylko wtedy, gdy na Overleafie pracowała jedna osoba nad całym tekstem:
1. **Menu → Download → Source** pobiera zip projektu.
2. Wyjmij z niego `preprint.tex` i nadpisz nim `report/preprint.tex`.
3. Przed commitem sprawdź, że nie nadpisujesz cudzych sekcji dodanych w repozytorium w międzyczasie:
   ```bash
   git diff report/preprint.tex
   ```

## Krok 9. Aktualizacja projektu na Overleafie po zmianach w repozytorium

Gdy w repozytorium zmienią się wyniki, tabele, rysunki albo sekcje innych osób:

**Najprościej: nowy projekt.** Powtórz kroki 1–5. Własny tekst, który nie trafił jeszcze do repozytorium, najpierw przenieś według kroku 8, bo nowy projekt go nie zawiera.

**Albo podmiana pojedynczych plików:**
1. Zbuduj paczkę (krok 1) i rozpakuj ją na dysku.
2. Na Overleafie kliknij w drzewie plików ikonę **Upload** (strzałka w górę).
3. Wskaż zmieniony plik, np. `numbers.tex`, i potwierdź nadpisanie (**Overwrite**).
4. Pliki z `tables/` i `figures/` wgrywaj do odpowiedniego folderu: najpierw kliknij folder w drzewie, potem **Upload**.
5. `preprint.tex` podmieniaj tylko wtedy, gdy na Overleafie nie masz własnych niezapisanych w repozytorium zmian.

## Krok 10. Najczęstsze problemy

| Objaw | Przyczyna | Rozwiązanie |
|---|---|---|
| `File 'numbers.tex' not found` | pliki w podkatalogu archiwum (np. `report/`) | zip musi mieć `preprint.tex` w głównym katalogu; zbuduj paczkę sposobem A albo B |
| `File 'tables/….tex' not found` albo brak rysunku | niepełna paczka | zbuduj paczkę ponownie i utwórz nowy projekt |
| `Undefined control sequence` przy `\res…` | literówka w nazwie makra albo stary `numbers.tex` | porównaj nazwę z `report/numbers.tex`; wgraj aktualny `numbers.tex` |
| `Missing $ inserted` | goły `_` albo `^` w tekście | pisz `\_`, a nazwy w `\kod{…}` |
| tekst urywa się po `%` | `%` rozpoczyna komentarz | pisz `\%` |
| `Runaway argument` albo `File ended while scanning` | niedomknięty nawias `{` | sprawdź nawiasy w ostatnio zmienionym akapicie |
| „??” w miejscu numeru tabeli | jedna kompilacja, literówka w `\ref` albo zła etykieta | **Recompile** drugi raz; porównaj etykietę z listą w pkt 4 instrukcji |
| „[?]” w miejscu cytowania | brak `\bibitem` o tym kluczu | dodaj pozycję albo popraw klucz |
| sklejone słowa, np. „1341linków” | brak `{}` po makrze | `\resHtwoLinks{} linków` |
| polskie znaki jako krzaczki | plik zapisany w innym kodowaniu | zapisuj w UTF-8 (w VS Code: prawy dolny róg, „UTF-8”) |
| `Compilation timed out` | duże rysunki lub chwilowe obciążenie serwera | spróbuj ponownie; nie podmieniaj rysunków na większe |

Jeśli błąd jest niezrozumiały, otwórz **Logs and output files** i przeczytaj pierwszy błąd od góry: kolejne zwykle z niego wynikają. Overleaf pokazuje numer linii; zacznij od niej.

## Krok 11. Pobranie PDF-u do oddania

1. Upewnij się, że projekt na Overleafie ma ostateczną wersję z repozytorium. Najpewniej: nowy projekt z paczki zbudowanej z `STRICT=1` (pkt 9 instrukcji).
2. Kliknij **Recompile** dwa razy.
3. Kliknij ikonę **Download PDF** nad podglądem.
4. Sprawdź liczbę stron (najwyżej 7) i przejdź przez listę kontrolną z pkt 9 instrukcji.
