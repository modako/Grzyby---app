# Backtest: sierpień–październik 2025

Wygenerowane przez workflow `backtest` (GitHub Actions) skryptem `python -m pipeline.backtest`.
Parametry modelu 0.2.0. Dane: `backtest.json` (wszystkie składowe M, L, T, S, W i IG dzień po dniu).

## Jak to policzono

Open-Meteo nie przechowuje dawnych prognoz w darmowym archiwum ERA5, więc backtest używa
**pogody, która faktycznie wystąpiła** (reanaliza ERA5, a wilgotność gleby z ERA5-Land).
Każdy dzień to więc to, co aplikacja pokazałaby jako „dziś”, gdyby prognoza na dziś była
idealna. Backtest sprawdza zachowanie modelu (czy reaguje na deszcz, upał i chłód), a nie
trafność prognozy na 14 dni. Tę można sprawdzić później z Historical Forecast API
(prognozy archiwalne od 2022 r.).

Komórki: Lasy Spalskie (Spała), Puszcza Pilicka (Przedbórz), Lasy Załęczańskie (Wieluń),
Bory pod Łaskiem (dojrzałe bory sosnowe) i las liściasty na północ od Łodzi (dąb, sosna, brzoza).

## Co widać

| Las | Max IG | Kiedy | Dni zielone | Opad, po którym przyszedł szczyt |
|---|---|---|---|---|
| Lasy Załęczańskie (Wieluń) | 90 | 17.09 | 11 | 28 mm 5–7.09 → szczyt po 12 dniach |
| Bory pod Łaskiem | 85 | 17.09 | 8 | 25 mm 5–7.09 → po 12 dniach |
| Lasy Spalskie (Spała) | 65 | 25.09 | 1 | 14 + 16 mm 13 i 16.09 → po 9–12 dniach |
| Las liściasty pod Łodzią | 63 | 19.09 | 2 | 26 mm 11–13.09 → po 8 dniach |
| Puszcza Pilicka (Przedbórz) | 53 | 7.08 | 0 | wilgotny początek sierpnia |

- **Opóźnienie po deszczu działa:** wrześniowe szczyty przychodzą 8–12 dni po opadzie ≥ 20 mm. To zgodne z założeniem 7–14 dni, ale wynika z samej budowy wzoru (jądro opóźnienia ze szczytem w 10. dniu). Potwierdza poprawne liczenie, nie trafność.
- **Sierpień 2025 był gorący i suchy:** od ok. 10.08 do początku września IG spada do zera we wszystkich lasach (twardy zakaz: średnia 5 dni > 17,5 °C i opad < 1 mm/dobę).
- **Październik jest niski:** średnia temperatura dobowa ok. 8 °C daje składową T ≈ 0,3, więc nawet po deszczu 21–24 mm (22–24.10) IG nie przekracza 14–26.
- **Przymrozki:** w całym okresie były tylko pojedyncze mroźne noce (3.10, 20.10). Kara za przymrozek wymaga co najmniej 2 z 3 nocy, więc **ani razu nie zadziałała**. Spadek IG na początku października to efekt chłodu (składowa T), nie reguły przymrozku.
- Percentyl wilgotności gleby działa: zakres 0,01–0,98 w okresie.

## Co wygląda podejrzanie

1. **Skoki do zera w środku szczytu.** Twardy zakaz upału zrzuca IG z ok. 60 do 0 na 1–2 dni (np. las liściasty pod Łodzią 22–23.09, Spała 21.09). Owocniki nie znikają w jeden dzień, więc to artefakt progu. Propozycja do kalibracji: łagodne przejście zamiast progu albo wymóg kilku dni upału z rzędu.
2. **Za niski październik.** Research podaje szczyt podgrzybka w IX–X, a opieńki w X, a model prawie wygasza październik. Propozycja: szersze optimum temperatury (`t_width`) jesienią albo osobne T dla gatunków jesiennych.
3. **Reguła przymrozku nie jest sprawdzona** na prawdziwych danych tego sezonu (brak dwóch mroźnych nocy w ciągu 3 dni).
4. **Brak porównania z rzeczywistymi zbiorami.** To wymaga dziennika wypadów (etap 4) albo ręcznych relacji z sezonu 2025.

Zmiany parametrów zostawiamy na kalibrację (etap 4). Decyzję podejmuje właściciel.
