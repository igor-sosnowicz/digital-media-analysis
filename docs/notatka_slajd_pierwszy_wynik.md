# Slajd „Pierwszy wynik na pełnych danych” (blok 4): propozycja

Stan na 27.10.2026: wyniki końcowe preregistracji v1 po jedynym teście `stance_v1` (commit zamrażający `7ad9409`) i przeglądzie domen, sprzed rozbudowy eksperymentu (v2). Liczby pochodzą z `report/numbers.tex`, wygenerowanego przez `make preprint-package`. Przed zajęciami warto uruchomić to polecenie jeszcze raz, żeby slajd i preprint miały te same liczby.

Oznaczenia hipotez: **H1.1 = H1-A** (stanowisko wobec konsensusu naukowego, test główny H1), **H1.2 = H1-B** (typy źródeł na Reddicie), **H2** (źródła alternatywne w Wikipedii).

## Główny przekaz (jedno zdanie na górze slajdu)

Na pełnych danych żadna z hipotez nie ma merytorycznego potwierdzenia:
- H1.1 jest niemierzalna: instrument stanowiska nie spełnił preregistrowanego warunku trafności;
- H1.2 daje wynik negatywny;
- H2 jest istotna formalnie, ale wynik okazał się artefaktem pomiaru.

Propozycja tytułu: **„Trend w źródłach to głównie zmiana składu próby, nie zmiana zachowań”**.

## Układ slajdu (16:9, trzy kolumny i pasek u dołu)

| Kolumna | Treść | Wykres |
|---|---|---|
| **1. Dane i pomiar** | Reddit: 62 636 postów w ramce, 6240 w próbie H1 (2005–2020). Wikipedia: 1453 rewizje i 1341 dodanych linków (H2). Instrument: GLiNER, wybrany na części `dev` i przetestowany raz na części testowej. | 2 liczby i 1 kafelek: F1 dla `cites_source` na Reddicie 0,96 [0,92; 0,99], w Wikipedii 0,26 [0,06; 0,51] |
| **2. H1.2: źródła na Reddicie** | Brak trendu wewnątrz subredditów. Źródła konsensusowe: OR/rok 1,03 [0,99; 1,06], p = 0,93. Alternatywne: 0,99 [0,97; 1,01], p = 0,85. Zmiana udziałów w całej próbie wynika ze składu: r/conspiracy to 2 % postów w 2008 r. i 58 % w 2018 r. | `report/figures/slide_h1.png` (H1-B bez panelu H1-A, 16:9) |
| **3. H2: Wikipedia** | OR/rok 1,47 [1,09; 1,99], p = 0,006, ale z 1341 linków tylko 10 to źródła „alternatywne”. 6 z nich to transmisje WHO na Periscope, 2 to konto GIS na Twitterze. Według właściciela treści test dokładny daje p = 0,21. Wniosek: H2 bez potwierdzenia, to artefakt klasyfikacji domen. | `report/figures/preprint_h2.png` |
| **Pasek: H1.1** | Wynik walidacji (opisany niżej) | `report/figures/preprint_stance_confusion.png` (mała macierz pomyłek) albo sama ramka |

Rozkład wyniku H1.2 na skład i zachowania, do jednego zdania albo małej tabelki: udział źródeł konsensusowych zmienił się o −3,7 pp, z czego −6,5 pp to zmiana składu próby, a +2,7 pp to zmiana wewnątrz subredditów. Dla źródeł alternatywnych: +7,6 pp = +7,3 pp ze składu i +0,2 pp wewnątrz subredditów.

## H1.1: co dokładnie powiedzieć

Ramka u dołu slajdu, wyróżniona innym kolorem, z napisem **„Wynik negatywny co do pomiaru”**.

1. **Co chcieliśmy mierzyć:** odsetek postów podważających konsensus naukowy (`challenges`) w czasie. Kierunek z preregistracji: wzrost.
2. **Warunek trafności z preregistracji:** F1 dla `challenges` ≥ 0,5 i κ ≥ 0,4 na części testowej, jeden test po zamrożeniu progów.
3. **Wynik jedynego testu** (216 postów, w tym 42 `challenges` dzięki próbie wzbogaconej z r/conspiracy): F1 0,33, κ 0,24. Warunek niespełniony, więc trendu H1.1 nie liczymy.
4. **Dlaczego:** model jest precyzyjny (0,80), ale wyłapuje tylko 21 % postów podważających naukę.
5. **Uczciwie o odniesieniu:** etykiety stanowiska to reguła codebooka i podpowiedzi AI. Sprawdził je JP, znając podpowiedzi. Ślepa druga kontrola AI potwierdziła 90 % z nich. Pilotażu dwóch osób nie zakodowano.

Unikamy w ramce sformułowań „widać wzrost” i podobnych. Dla H1.1 nie ma żadnej liczby trendu.

## Zastrzeżenia (drobnym drukiem albo w notatkach prelegenta)

- **Zgodność annotatorów w pilotażu jest niska według α** (`cites_source` na Reddicie: α = −0,03 przy zgodności 91 %). To paradoks częstości: prawie każdy post z linkiem cytuje źródło. Typy źródeł: MASI α = 0,34. Druga runda pilotażu (`pilot2`) jest w toku.
- **Każda jednostka gold ma etykietę jednej osoby** (IS albo JP), więc zgodność dwóch osób jest tylko w pilotażu. Przy analizie błędów 20 jednostek części `dev` ma etykiety prawdopodobnie niezgodne z codebookiem. JP zweryfikował przyczyny błędów, a wynik testu instrumentów się nie zmienia.
- **Pomiar w Wikipedii jest słaby** (F1 0,26). Dlatego H2 mierzymy po domenach linków, a nie instrumentem.
- **Korelacja to nie przyczynowość.** Brak trendu wewnątrz subredditów nie wyklucza zmian w populacji użytkowników. Mówi tylko, że wzrost w całej próbie to efekt składu.
- **Ujawnienie AI:** podpowiedzi etykiet (stanowisko, audyt, domeny) przygotował asystent AI. Sprawdził je ponownie, a potem wszystkie zatwierdził JP, nie zmieniając żadnej. Przebieg próbny na etykietach AI odbył się przed prawdziwym testem i jest ujawniony w preregistracji.

## Notatki prelegenta (około 1 minuty)

1. Pytanie badawcze i dane, jednym zdaniem (kolumna 1).
2. H1.2: najpierw wykres całej próby, potem w podziale na subreddity. „Trend znika, kiedy porównujemy podobne społeczności”.
3. H2: pokazać, że 6 z 10 „alternatywnych” linków to WHO. „Istotne statystycznie, nieistotne merytorycznie”.
4. H1.1: warunek trafności i wynik testu (F1 0,33 < 0,5). „Instrument nie widzi podważania nauki, więc o trendzie nie możemy nic powiedzieć”.
5. Następny krok: instrument stanowiska uczony na etykietach ludzi i niezależna zgodność dwóch osób; potem v2 (TOST, model z korektą błędnej klasyfikacji, więcej danych dla H2).

## Czego nie dawać na slajd

- Panelu H1-A z `preprint_h1.png` (nie ma w nim trendu): na slajd wziąć `slide_h1.png`.
- Tabel z wszystkimi instrumentami. Na slajd wystarczy GLiNER; porównanie z v1 i zero-shot wrzucić na slajd zapasowy (`preprint_instruments.png`).
- Wyników v2 (moc testów, TOST). Nie zostały jeszcze uruchomione na danych.

## Slajd zapasowy (do pytań)

- `report/figures/preprint_agreement.png`: zgodność w pilotażu i paradoks częstości.
- `report/figures/preprint_instruments.png`: v1, zero-shot i GLiNER. Test McNemara na Reddicie: GLiNER lepszy od v1 (66:6, p < 0,001).
- Analizy wrażliwości dla H2: bez COVID-19 OR 1,39, p = 0,105; bez 2020 r. OR 1,36, p = 0,138; eksploracyjnie z korektą Firtha OR 1,43 [0,96; 2,16], p = 0,040 (po poprawce testu z 30.10.2026; wcześniej podawano p = 0,006).
