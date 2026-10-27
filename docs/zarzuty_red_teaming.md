# Przewidywane zarzuty na turniej red teamingu (M2) i odpowiedzi

Każda odpowiedź wskazuje dowód: makro z `report/numbers.tex`, tabelę, rysunek albo plik. Liczby w nawiasach pochodzą z przebiegu próbnego z 27.10 albo z wcześniejszych wyników i trzeba je podmienić na makra po prawdziwym przebiegu.

| # | Zarzut | Odpowiedź | Dowód |
|---|---|---|---|
| 1 | **„H2 jest istotna, więc hipoteza się potwierdza.”** | Test z preregistracji daje p = 0,006, ale z 1341 linków tylko 10 to źródła „alternatywne”, w tym 8 to oficjalne konta WHO i GIS, a jeden link WHO dodano 6 razy. Według właściciela treści test dokładny daje p = 0,21. To artefakt klasyfikacji domen, nie zmiana zachowań. | `\resHtwoOr`, `\resHtwoOfficialLinks`, `\resHtwoExactP`; Rys. 4; Tab. 5 |
| 2 | **„Zmiana udziałów źródeł na Reddicie to spadek zaufania.”** | W obrębie subredditów nie ma trendu. Zmiana w całej próbie to zmiana składu: udział r/conspiracy rośnie z 2 % do 58 %. Dekompozycja to analiza eksploracyjna i tak ją opisujemy. | `\resHoneBConsensusOr`, `\resHoneBAlternativeShiftComposition`; Rys. 3; Tab. 4 |
| 3 | **„Instrument stanowiska nie działa, więc badanie nic nie mówi o H1.”** | To wynik negatywny co do pomiaru, równorzędny z potwierdzeniem (zasady kursu, 4.3). Warunek trafności zapisaliśmy przed testem. Macierz pomyłek pokazuje dlaczego: model jest precyzyjny, ale nie wyłapuje podważania nauki (czułość ~0,2). | `\resHoneAGate`, `\resHoneATestChallengesRecall`; Tab. 3; rys. macierzy pomyłek |
| 4 | **„Za mało przypadków `challenges`, żeby ocenić instrument.”** | Dlatego dołożyliśmy próbę wzbogaconą r/conspiracy z wagami włączenia (wpis z 26.10, przed testem). Na teście jest ~40 postów `challenges` zamiast 3. | `\resEnrichedPosts`, `\resStanceTestChallengesPosts`; `docs/hipotezy.md` |
| 5 | **„Walidujecie AI na etykietach AI.”** | Odniesienie to podpowiedzi AI sprawdzone przez człowieka (`verified = 1`), a reguły codebooka sprawdzane na ślepo. Podajemy, ile podpowiedzi ludzie poprawili. Warunek trafności rozstrzygają wiersze sprawdzone przez ludzi, a wynik na wszystkich wierszach to wrażliwość. Ograniczenie opisujemy w sekcji 6. | `\resPlanCAiChanged`, `\resPlanCStanceRulePrecision`, `\resHoneATestAllRowsKappa`; wpis z 27.10 |
| 6 | **„Widzieliście wynik testu przed testem.”** | Tak: przebieg próbny na etykietach AI, ujawniony w preregistracji przed prawdziwym testem. Instrument, siatkę strojenia i progi warunku zostawiamy bez zmian; każda późniejsza zmiana byłaby analizą eksploracyjną. Historia commitów pokazuje kolejność. | `docs/przebieg_probny_2026-10-27.md`; wpis z 27.10; commit zamrażający przed testem |
| 7 | **„Zgodność annotatorów jest bardzo niska.”** | Dla `cites_source` to paradoks częstości: zgodność 91 % przy α ≈ 0, bo prawie każdy post z linkiem cytuje źródło. Dla stanowiska podajemy niezależną zgodność na pilotażu bez podpowiedzi. | `\resPilotRedditCitesAgreement`, `\resPilotRedditCitesAlpha`, `\resHoneAPilotKappa`; Rys. 1 |
| 8 | **„Wskaźnik źródeł konsensusu nie jest trafny.”** | Audyt to sprawdził: J na granicy reguły (~0,20), więc zgodnie z preregistracją wskaźnik jest tylko opisowy. Wskaźnik źródeł alternatywnych przechodzi audyt (J ~0,59). | `\resAuditConsensusJ`, `\resAuditAlternativeJ` |
| 9 | **„Część gold kodowała jedna osoba, a jej etykiety bywają błędne.”** | Analiza błędów wskazała 20 jednostek części `dev` z prawdopodobnie błędnym gold. Ludzie to sprawdzili, a my podajemy to jako ograniczenie. Test instrumentów jest zamrożony i się nie zmienia. | Pareto przyczyn; `docs/podpowiedzi_ai.md` |
| 10 | **„Korelacja w czasie to nie przyczynowość.”** | Zgadzamy się i tak piszemy. Efekty stałe usuwają zmianę składu między subredditami, ale nie zmianę populacji w ich obrębie. | sekcja 6 |
| 11 | **„Wikipedia: instrument ma F1 0,26, więc pomiar nie działa.”** | Dlatego H2 mierzymy po domenach linków, nie instrumentem tekstowym. Wynik instrumentu na Wikipedii raportujemy jako negatywny. | `\resTestGlinerWikipediaCitesF`; Tab. 2 |
| 12 | **„Domeny sklasyfikowało AI.”** | Przegląd człowieka (plan C: domeny priorytetowe i każda zmiana kategorii) i H2 w dwóch wersjach: przed przeglądem i po nim. | `domain_review.csv`; wpis do preregistracji po przeglądzie |
| 13 | **„Rola AI w badaniu jest niejasna.”** | Sekcja 7 wylicza fakty: kod i testy, podpowiedzi etykiet sprawdzone przez ludzi, reguły, przebieg próbny, pakiet wyników. Tekst napisali autorzy. Instrumenty pomiaru to lokalne modele otwarte. | sekcja 7; historia commitów |

## Do uzupełnienia po prawdziwym przebiegu

1. Podmienić liczby z nawiasów na makra po `make finish-results`.
2. Jeśli warunek trafności H1-A przejdzie, zarzut 3 zastąpić zarzutami o trend: kierunek, wrażliwości, skład subredditów.
3. Jeśli J konsensusu po weryfikacji przekroczy 0,2, zarzut 8 zmienia się: wskaźnik konsensusu staje się zastępczym testem H1.
