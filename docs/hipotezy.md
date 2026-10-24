# Preregistracja: hipotezy H1 i H2

*Wersja 1.0, 24.10.2026.* Ten dokument, sekcja `hypotheses` w `config.yaml`, `codebook/domains.yaml` i kod analizy (`src/digital_media_analysis/hypotheses.py`, `src/digital_media_analysis/wikipedia_refs.py`, `scripts/09_test_hypotheses.py`) zatwierdzamy commitem **przed** pierwszym uruchomieniem `scripts/09_test_hypotheses.py --confirmatory`. Skrypt odmawia uruchomienia potwierdzającego, gdy te pliki nie są zacommitowane. Każdą późniejszą zmianę zapisujemy w sekcji „Zmiany przed analizą potwierdzającą” z datą i powodem.

## Co było wiadomo przed analizą

- **Instrumenty** (walidacja na gold, zbiór testowy uruchomiony raz 24.10.2026, commit `33ff729`; `docs/plan_walidacji.md`):
  - na Reddicie GLiNER (`gliner_v1`) wykrywa powołanie z F1 0,96, `media` z F1 0,66, a `social_blog` z F1 0,70;
  - `scientific` i `institutional` mają w gold za mało przypadków, by je ocenić;
  - na Wikipedii żaden instrument nie jest wiarygodny.
- **Przypisy Wikipedii** (rozpoznanie wykonalności przy planowaniu, a potem lista domen do przeglądu z `scripts/08b_export_domain_review.py`):
  - moduł `wikipedia_refs` liczy w latach 2020–2026 1341 dodanych linków z 222 domen;
  - ok. 79% przypada na stronę COVID-19, a liczba linków spada z ok. 740 w 2020 r. do kilkunastu–kilkudziesięciu rocznie w latach 2024–2026;
  - kategorie domen w okresie łącznie: `institutional` 460, `media` 407, `scientific` 278, `other` 166, `encyclopedia` 10, `social_blog` 10 (pscp.tv 6, twitter.com 2, monbiot.com 1, video.google.com 1), niesklasyfikowane archiwa 10;
  - podziału tych liczb na lata nie liczyliśmy.
- **Rama Reddita:** znana jest liczba postów na subreddit i rok w wylosowanych dniach (`data/raw/reddit_frame/fetch_log.json`). Udział r/conspiracy w ramie rośnie od 2008 r.
- **Czego nie liczyliśmy:** przed tym dokumentem nie policzono żadnych rocznych udziałów ani trendów wskaźników H1 i H2.

## H1: w latach 2005–2018 w przestrzeni online maleje zaufanie do konsensusu naukowego

**Dane:**
- **Rama:** posty z ramy Reddita (`make reddit-frame`), bez usuniętych.
- **Subreddity:** z `hypotheses.h1.subreddits` (r/reddit.com, r/science, r/skeptic, r/conspiracy); polskie subreddity nie dotyczą nauki.
- **Okres główny:** 2005–2018.
- **Próba analityczna:** `scripts/08_label_h1_sample.py`, losowanie proste do 150 postów z każdego subredditu i roku 2005–2020, ziarno 20261024. Waga posta to `day_weight` × (posty subredditu i roku w ramie) / (posty wylosowane).

**Wskaźniki:**

| | Wskaźnik | Jednostki | Instrument | Oczekiwany kierunek |
|---|---|---|---|---|
| **H1-A, główny** | udział postów `challenges` | posty dotyczące nauki (`consensus_stance` ≠ `not_applicable`) | `stance_v1` | wzrost |
| H1-A, poboczny | udział postów `supports` | jak wyżej | `stance_v1` | spadek |
| H1-B, poboczny | udział postów powołujących się na `scientific` lub `institutional` | posty z powołaniem | `gliner_v1` | spadek |
| H1-B, poboczny | udział postów powołujących się na `social_blog`, `unknown` lub `personal` | posty z powołaniem | `gliner_v1` | wzrost |

**Warunki trafności (zapisane z góry):**
- **H1-A:** testujemy tylko wtedy, gdy `stance_v1`, strojony na `dev` i uruchomiony raz na `test` (`scripts/07b_validate_stance.py`), osiąga na teście F1 ≥ 0,5 dla `challenges` i κ ≥ 0,4. Inaczej raportujemy, że H1-A nie da się zmierzyć tym instrumentem.
  - Zgodność annotatorów co do stanowiska mierzymy na rundzie `pilot2` (30 postów kodowanych przez obie osoby).
  - Jeśli H1-A nie spełni warunku, testem potwierdzającym H1 staje się wskaźnik źródeł konsensusu z H1-B.
- **H1-B, wskaźnik konsensusu:** przed analizą potwierdzającą przechodzi audyt (`--audit-annotators` w skrypcie 08, do 30 postów z każdej warstwy przewidzianej kategorii). Jeśli czułość + swoistość − 1 ≤ 0,2, wskaźnik raportujemy tylko opisowo.

**Model:**
- ważona regresja logistyczna: wynik ~ rok (od początku okresu) + efekty stałe subredditu;
- wagi przeskalowane do średniej 1;
- błędy standardowe grupowane po wylosowanym dniu;
- miarą efektu jest iloraz szans na rok z 95% przedziałem;
- test jednostronny w oczekiwanym kierunku, α = 0,05.

H1 uznajemy za potwierdzoną, gdy wskaźnik główny ma p < 0,05 w oczekiwanym kierunku. Wskaźniki poboczne raportujemy bez poprawki na wielokrotne testowanie i opisujemy jako poboczne.

**Analizy wrażliwości:**
- tylko r/science (2006–2018);
- tylko r/conspiracy (2008–2018);
- okres 2005–2020;
- dla H1-B roczne udziały skorygowane o błąd instrumentu metodą Rogana–Gladena, z czułością i swoistością z gold (`test`) i audytu.

**Zagrożenia:**
- Efekty stałe usuwają zmianę składu między subredditami, ale nie zmianę populacji w obrębie subredditu.
- Niezróżnicowany błąd pomiaru osłabia trendy, więc test jest raczej zachowawczy.
- Rok 2005 to wyłącznie ogólny r/reddit.com.
- Źródła (H1-B) są tylko pośrednią miarą zaufania.

## H2: w latach 2020–2026 użytkownicy częściej odwołują się do alternatywnych źródeł wiedzy

**Dane:**
- linki dodane do przypisów (`<ref>`) w rewizjach z lat 2020–2026 ośmiu stron z `wikipedia_pages` (`src/digital_media_analysis/wikipedia_refs.py`);
- link liczy się jako dodany, gdy występuje częściej niż w poprzedniej rewizji;
- linki archiwalne rozwijamy do adresu oryginału;
- jednostką analizy jest dodany link.

**Wskaźnik:** udział linków do domen alternatywnych (kategoria `social_blog` w `codebook/domains.yaml`: media społecznościowe, serwisy wideo, blogi i newslettery), z oczekiwanym wzrostem.

**Warunek trafności:** przed analizą potwierdzającą ktoś przegląda ręcznie wszystkie domeny (`scripts/08b_export_domain_review.py`, plik `annotations/hypotheses/domain_review.csv`), a rozbieżności poprawiamy w `codebook/domains.yaml`.

**Model:**
- ważona regresja logistyczna: wynik ~ rok + efekty stałe strony;
- błędy grupowane po rewizji;
- test jednostronny, α = 0,05.

**Analizy wrażliwości:** bez strony COVID-19; bez roku 2020; tylko linki z domen sklasyfikowanych.

**Moc i interpretacja:** przy 10 linkach alternatywnych na ok. 1340 test ma bardzo małą moc. Wynik „brak wykrywalnego wzrostu” z szerokim przedziałem jest pełnoprawnym wynikiem; nie zmieniamy definicji wskaźnika po zobaczeniu danych.

**Wskaźnik opisowy (bez testu):** roczny udział opisów zmian z powołaniem na `social_blog`, `unknown` lub `personal` w ręcznym gold Wikipedii. Instrumenty na Wikipedii są niewiarygodne, więc nie etykietujemy nimi całej ramy.

**Ograniczenia:**
- Kategoria domeny nie rozpoznaje „ekspertów niezależnych” publikujących na zwykłych stronach.
- 2026 to rok niepełny.
- Osiem stron wybranych tematycznie nie reprezentuje całej Wikipedii.

## Kolejność prac

1. Commit tego dokumentu, `config.yaml`, `codebook/domains.yaml` i kodu analizy.
2. Przegląd domen (H2) oraz audyt kategorii H1-B.
3. Kodowanie stanowiska:
   - `pilot2` przez obie osoby, z pomiarem zgodności;
   - posty gold przez obie osoby, każda swoje;
   - import przez `scripts/04b_import_stance_labels.py`.
4. Strojenie `stance_v1` na `dev`, `TUNED = True`, commit, jeden przebieg na `test`.
5. `scripts/08_label_h1_sample.py`, potem `scripts/09_test_hypotheses.py --confirmatory`.

Zmiany w `codebook/domains.yaml` po przeglądzie domen i progi `stance_v1` po strojeniu to przewidziane zmiany przed analizą potwierdzającą. Commitujemy je przed nią i zapisujemy poniżej.

## Zmiany przed analizą potwierdzającą

**24.10.2026, przed pierwszym przebiegiem potwierdzającym.** Na prośbę zespołu przebieg potwierdzający uruchamiamy, zanim ludzie wykonają kodowanie zaplanowane w punktach 2–4 kolejności prac. Skutki, zapisane przed zobaczeniem wyników:

1. **Przegląd domen (H2):** listę domen sklasyfikował asystent AI przygotowujący instrument; nie przejrzał jej człowiek. Wynik H2 jest potwierdzający z tym zastrzeżeniem. Przegląd ręczny (`domain_review.csv`) pozostaje do zrobienia; jeśli zmieni kategorię domen alternatywnych, powtarzamy H2 i raportujemy obie wersje.
2. **Audyt kategorii (H1-B):** nie wykonano, więc warunku trafności nie da się sprawdzić. Zgodnie z regułą traktujemy go jako niespełniony: wskaźnik źródeł konsensusu raportujemy tylko opisowo. Korekta Rogana–Gladena korzysta wyłącznie z gold (`test`), gdzie przypadków `scientific` i `institutional` jest bardzo mało.
3. **H1-A:** brak ludzkich etykiet stanowiska, więc `stance_v1` nie jest nastrojony ani zwalidowany i H1-A czeka. H1 nie ma na razie testu potwierdzającego: zastępczy wskaźnik konsensusu z H1-B wymaga audytu (punkt 2). Oba wskaźniki H1-B raportujemy jako poboczne. Test H1-A wykonamy po kodowaniu stanowiska, bez zmian w tym dokumencie poza strojeniem progów.
