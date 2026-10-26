# Co zostało do dokończenia przed preprintem (stan 26.10.2026)

Notatka do planowania pracy. Szczegóły kroków są w [`h1a_kroki.md`](h1a_kroki.md) (H1-A), [`podpowiedzi_ai.md`](podpowiedzi_ai.md) (weryfikacja etykiet AI) i [`preprint_szkic.md`](preprint_szkic.md) (sekcje i budżet stron). Tekst preprintu piszą członkowie zespołu, bo kurs sprawdza publikację Pangramem i ocenia wkład indywidualnie.

## 1. Stan obecny w skrócie

| Element | Stan | Wpływ na preprint |
|---|---|---|
| Dane i próby (Reddit 62 636 / 6240, Wikipedia 1453 rewizji / 1341 linków) | gotowe | sekcja 2 może być pisana już teraz |
| Codebook 2.2, gold standard, pilotaż (α niskie, paradoks częstości) | gotowe, ale gold częściowo kodowany przez jedną osobę | sekcja 3: brakuje `pilot2` IS i uzgodnienia sporów |
| Walidacja instrumentów źródeł (v1, zero-shot, GLiNER), test zamrożony | gotowe | sekcja 4 gotowa merytorycznie |
| H1-B (wynik negatywny, efekt składu) | gotowe, ale wskaźnik opisowy (brak audytu) | sekcja 5: brakuje audytu, żeby H1-B było testem, a nie opisem |
| H2 (p = 0,006, artefakt WHO/GIS) | gotowe, ale lista domen sklasyfikowana tylko przez AI | sekcja 5: brakuje przeglądu domen przez człowieka |
| **H1-A (H1.1), test główny H1** | **brak wyniku**: 0 z 217 wierszy zweryfikowanych | sekcje 4 i 5 mają makra „[czeka na H1-A]” |
| Etykiety AI dla Fazy A i B | gotowe, niezweryfikowane | muszą zostać sprawdzone przez ludzi, zanim trafią do wyników |
| Szkielet `report/preprint.tex`, makra, 5 tabel, 4 rysunki | gotowe | brak prozy w 10 ramkach `\dopisania{}` |

## 2. Prace konieczne (bez nich preprint ma lukę w teście głównym)

### 2.1. H1-A: od weryfikacji do wyniku

1. **Weryfikacja 4 arkuszy stanowiska.** IS: 97 wierszy, JP: 120 wierszy, około 1,5–2 godz. na osobę. Szczególnie: szukać przeoczonych `challenges`.
2. **Decyzja przed testem: co z małą liczbą postów `challenges`?** Według podpowiedzi AI w gold są 4 takie posty (1 w części `dev`, 3 w testowej). Do wyboru:
   - **(a) bez zmian:** test przy F1 opartym na 3 postach, z bardzo szerokim przedziałem ufności;
   - **(b) zmiana w preregistracji przed testem:** dodatkowa próba z r/conspiracy wzbogacona w posty podważające konsensus, z wagami włączenia (jak w audycie);
   - **(c) zgłosić z góry,** że warunek trafności jest niesprawdzalny, i raportować H1-A jako niemierzalne.

   Decyzję trzeba wpisać do sekcji „Zmiany” w `docs/hipotezy.md` **przed** testem. Po teście nie wolno już zmieniać warunku.
3. Potok (około 30 minut, uruchamiam ja):
   - import i zgodność;
   - strojenie progów na części `dev`;
   - **commit zamrażający** (potrzebna Twoja zgoda);
   - jeden test;
   - etykiety dla 6240 postów;
   - test potwierdzający;
   - `make preprint-package`.
4. **Sprawdzić**, że wyniki H1-B i H2 w teście potwierdzającym są identyczne jak teraz (`git diff`).

**Skutek dla preprintu:** wypełniają się makra `\resHoneA...`, Tab. 3, Tab. 4 i panel H1-A na Rys. 3. Werdykt wynika z tabeli w `h1a_kroki.md`, pkt 3, a każdy z trzech możliwych wyników jest do napisania.

### 2.2. Ujawnienie użycia AI: aktualizacja faktów

Sekcja 7 w `preprint_szkic.md` jest już nieaktualna. Trzeba dopisać, że asystent AI:
- przygotował wstępne etykiety stanowiska (Faza A), audytu, `pilot2` dla IS, propozycje rozstrzygnięć sporów, drugą klasyfikację domen i przyczyny błędów (Faza B);
- wszystkie te etykiety zweryfikowali ludzie;
- podajemy liczby: ile podpowiedzi sprawdzono i ile poprawiono (`<faza>_stance_ai_review.csv` i kolumny `ai_*` w arkuszach).

Trzeba też opisać konsekwencję: zgodność pilotażu stanowiska i audytu jest **zgodnością po podpowiedzi AI**, a nie niezależną.

## 3. Prace zalecane (wzmacniają ocenę metodologii, 40% oceny preprintu)

| Zadanie | Co daje w preprincie | Nakład |
|---|---|---|
| B2: `pilot2` u IS i zgodność na 113 jednostkach | sekcja 3: mocniejsza miara zgodności, druga runda zgodna z regułą α < 0,667 | około 45 min (IS) |
| B3: uzgadnianie sporów (20 + nowe) | sekcja 3: opisana procedura rozstrzygania, przykłady niejasności codebooka (TED, dział wiadomości nature.com) | około 45 min (razem) |
| B1: audyt H1-B (180 postów × 2) | sekcja 5: H1-B jako test z warunkiem trafności i udziałami skorygowanymi o błąd; plan awaryjny, gdyby H1-A nie przeszło warunku | około 2 godz. na osobę |
| B4: przegląd domen H2 | sekcja 5: usuwa najbardziej oczywisty zarzut red teamingu; H2 w dwóch wersjach | około 1,5 godz. |
| B5: przyczyny błędów | sekcja 4: potwierdzony wykres Pareto; **sprawdzenie 20 jednostek z prawdopodobnie błędnym gold** | około 2,5 godz. |

**Skutek B5 do opisania w ograniczeniach:** jeśli zespół potwierdzi błędy w gold, część „błędów” instrumentów to błędy etykiet referencyjnych. Wynik testu jest zamrożony i się nie zmienia, ale trzeba to opisać jako ograniczenie gold standardu. Może to też tłumaczyć różnicę wyników GLiNER-a między annotatorami (MASI 0,29 dla IS, 0,61 dla JP).

## 4. Decyzje do podjęcia przez zespół

1. **Mała liczba `challenges`:** wariant (a), (b) czy (c), przed testem H1-A.
2. **Czy robimy niezależny pilotaż stanowiska bez podpowiedzi** (jedna osoba, 30 postów, około 30 minut)? Daje jedyną niezależną miarę zgodności dla H1-A.
3. **Czy w preprincie jest miejsce na v2** (TOST, korekta błędnej klasyfikacji, moc testów)? Proponuję nie: preprint v1 plus akapit „dalsze prace” w dyskusji. Analizy v2 wymagają pobrania nowych danych, a te pobieramy tylko za osobną zgodą.
4. **Budżet stron:** szkic ma 7,2 strony, a „Przed oddaniem” mówi „≤ 7”. Trzeba ujednolicić; limit kursu to 8.

## 5. Pisanie (członkowie zespołu, według ról w `preprint_szkic.md`)

| Sekcja | Można pisać teraz? | Czeka na |
|---|---|---|
| Streszczenie, 1. Wprowadzenie | wprowadzenie tak; streszczenie na końcu | werdykt H1-A |
| 2. Dane i próba | tak | – |
| 3. Pomiar | tak, ale zgodność do uzupełnienia | B2, B3 |
| 4. Walidacja | tak dla źródeł; stanowisko po potoku | H1-A (Tab. 3), B5 |
| 5. Wyniki | H2 i H1-B tak; H1-A po potoku | H1-A, B1, B4 |
| 6. Dyskusja i ograniczenia | szkic tak | wszystkie wyniki |
| 7. Odtwarzalność i AI | po aktualizacji faktów (pkt 2.2) | liczby poprawionych podpowiedzi |

Tekst używa makr z `report/numbers.tex`, więc nie trzeba czekać na końcowe liczby, żeby pisać.

## 6. Przed oddaniem

1. `make report-tables` i `make preprint-package`, potem kompilacja na Overleafie (spakowanie: `data/preprint_overleaf.zip` do odświeżenia).
2. Kontrola spójności: każda liczba w tekście to makro (mogę ją uruchomić).
3. Usunąć ramki `\dopisania{}` i napisy zastępcze. Makro `\resHoneAStatus` nie może mieć wartości „czeka…”.
4. Lista przewidywanych zarzutów na turniej red teamingu (M2) z odpowiedziami. Pewniaki:
   - H2 to artefakt;
   - H1-B to efekt składu próby;
   - niska α;
   - podpowiedzi AI w etykietach;
   - mało postów `challenges`;
   - jeden annotator w części gold.
5. Commit i push z wynikami. Commit zamrażający instrument przed testem musi być widoczny w historii.

## Proponowana kolejność

1. **Dzień 1:** decyzja z pkt 4.1, weryfikacja Fazy A, potok H1-A, aktualizacja pakietu.
2. **Dzień 2:** B2, B1, B4, a równolegle pisanie sekcji 2–4.
3. **Dzień 3:** B3, B5, pisanie sekcji 5–7 i streszczenia.
4. **Dzień 4:** kontrola spójności, Overleaf, lista zarzutów, oddanie.
