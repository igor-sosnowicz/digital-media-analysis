# Protokół anotacji AI (A1), wersja 1 (31.10.2026)

Protokół z propozycji `docs/propozycja_poprawy_eksperymentu.md` (rozdz. 4.2–4.3). Wersja 1 służy przećwiczeniu na 253 jednostkach zakodowanych przez IS bez pomocy AI (pilotaż 53, gold 200).

## Anotator

- Model: Claude Opus 5.5 w sesji Claude Code (bez API, bez lokalnych LLM).
- Jeden przebieg = jedna sesja (albo jeden agent bez wcześniejszego kontekstu). Przebieg B nie widzi etykiet przebiegu A.
- Anotator zna cel badania (nie da się tego ukryć w tej samej sesji); raportujemy to jako ograniczenie.

## Instrukcja

- Instrukcją jest codebook `codebook/codebook.md` (v2.2) w całości: konstrukt, jednostki, definicje kategorii z przykładami i reguły R1–R13.
- Kodowane zmienne:
  - `source_types` (Reddit i Wikipedia), wiele kategorii albo `none`;
  - `edit_about_sources` (tylko Wikipedia).

  `cites_source` jest wyliczane (R13).
- Przy wątpliwości: najlepsza etykieta i `uncertain = 1` (R12).
- Linków się nie otwiera; kategorię ustala się z domeny i tekstu (jednostki analizy w codebooku).

## Co widzi anotator

- Reddit: subreddit, tytuł, treść i link posta, jeśli prowadzi poza wątek. Wikipedia: nazwa strony i opis zmiany.
- To te same pola, które widzieli ludzie w arkuszach (`annotation_sheets.CONTENT_COLUMNS`).
- Każda jednostka ma losowy kod zamiast identyfikatora. Kolejność jest losowa (ziarno 20261031 dla przebiegu A, 20261032 dla B).
- Anotator **nie** widzi: identyfikatora jednostki, roku, podziału, wag, sygnału, etykiet ludzi, preannotacji ani wyników instrumentów.
- Klucz (kod → jednostka) jest zapisany osobno i otwierany dopiero przy ocenie.

## Zapis

- Plik etykiet bez tekstu: kod, `source_types` (kody rozdzielone średnikiem), `edit_about_sources`, `uncertain`.
- Po zakończeniu przebiegu etykiet się nie zmienia. Ewentualna zmiana instrukcji = nowa wersja protokołu i nowy przebieg całości.

## Ocena (dopiero po przebiegu)

- Zgodność z etykietami IS: F1 `cites_source`, średnie MASI dla `source_types`, F1 `edit_about_sources`.
- Niezależność błędów (N6): κ wskaźników błędu anotatora i instrumentów (GLiNER, zero-shot, reguły v1) na jednostkach, dla których są predykcje.
- Stabilność (K1): κ przebiegów A i B, gdy powstanie przebieg B.
