# Grzyby: prognoza dla grzybiarzy

Prywatna aplikacja mobilna (Android + iOS), która pokazuje na mapie lasy w Polsce pokolorowane według **Indeksu Grzybowego** (0–100):

- 🟢 **≥ 60**: jedź,
- 🟡 **35–59**: warto, jeśli blisko,
- 🔴 **< 35**: nie warto,
- ⬜ **szary**: brak wstępu lub zakaz zbioru (park narodowy, rezerwat, poligon, uprawa leśna).

Indeks łączy **potencjał lasu** (gatunek, wiek i siedlisko drzewostanu z Banku Danych o Lasach) z **pogodą** z ostatnich tygodni i prognozą na 14 dni (Open-Meteo). Region startowy: województwo łódzkie (kolejne będą dochodzić z czasem).

> Aplikacja **nie rozpoznaje grzybów i nie ocenia ich jadalności**. W razie wątpliwości skonsultuj się z grzyboznawcą.

## Co gdzie jest

| Folder | Zawartość |
|---|---|
| `docs/research.md` | raport z researchu (lasy, model, dane, prawo, konkurencja) |
| `docs/research_z_przypisami.md` | ten sam raport z przypisami i listą źródeł |
| `docs/SPEC.md` | specyfikacja modelu prognozy i wszystkie parametry |
| `docs/PROMPTY.md` | plan pracy: prompty dla kolejnych etapów |
| `CLAUDE.md` | zasady projektu dla Claude Code |
| `pipeline/` | obliczenia w Pythonie (od etapu 1) |
| `app/` | aplikacja mobilna Expo (od etapu 3) |
| `data/` | wygenerowane dane (nie trafiają do repozytorium, poza `data/samples/`) |

## Status

Etap 0 (setup i specyfikacja) zrobiony, etap 1 (dane o lasach, łódzkie) zrobiony, etap 2 (pogoda) w toku. Plan wszystkich etapów jest w `CLAUDE.md`.

## Jak zbudować dane o lasach (etap 1)

```bash
pip install -r pipeline/requirements.txt
python -m pipeline.build_static      # pobiera BDL (z cache), liczy heksagony, zapisuje data/static/ i podgląd
python -m pytest pipeline/tests      # testy funkcji przydatności
```

Wynik:

| Plik | Co zawiera |
|---|---|
| `data/static/cells.geojson` | heksagony lasu z potencjałem H dla 9 gatunków, flagami prawnymi i opisem drzewostanu |
| `data/static/cells_meta.json` | środki heksagonów i przypisany punkt siatki pogodowej 0,1° (dla etapu 2) |
| `data/static/attribution.json` | źródła danych, licencje i daty pobrania |
| `data/preview/preview.html` | mapa podglądowa do otwarcia w przeglądarce |

Region ustawia `pipeline/config/region.yaml`, parametry modelu `pipeline/config/model_params.yaml` (lustro tabeli z `docs/SPEC.md`). Dane OpenStreetMap przygotowuje automat na GitHubie (`.github/workflows/osm-extract.yml`), bo środowisko w chmurze nie łączy się z serwerami OSM.

## Pogoda i publikacja danych (etap 2)

Wszystko liczy się samo na GitHubie (zakładka **Actions**):

| Automat | Kiedy | Co robi |
|---|---|---|
| `daily-weather` | codziennie ok. 04:00 czasu polskiego, po każdym scaleniu zmian i ręcznie | pobiera pogodę z Open-Meteo (dni −30…+14), liczy składową W i publikuje `daily/latest.json` |
| `static-forest-data` | po zmianach w danych o lasach i raz w miesiącu | przelicza heksagony lasu (etap 1) i publikuje `static/` |
| `soil-climatology` | codziennie w nocy, aż skończy | jednorazowo pobiera 10 lat wilgotności gleby (ERA5-Land), w porcjach mieszczących się w darmowym limicie |
| `backtest` | po zmianach w modelu | liczy indeks za VIII–X 2025 i zapisuje wykresy w `docs/backtest/` |

Opublikowane pliki trafiają na gałąź `gh-pages`, z której GitHub Pages serwuje je pod stałym adresem.

Lokalnie (testy):

```bash
python -m pytest pipeline/tests                       # model W, kontrakt IG, funkcje przydatności
python -m pipeline.build_daily --estimate-only        # ile wywołań API zużyje jeden bieg
```

Kontrakt IG dla aplikacji: `docs/contract/ig_cases.json`.

## Źródła danych i atrybucje

Open-Meteo (CC BY 4.0), © autorzy OpenStreetMap (ODbL), Bank Danych o Lasach (Lasy Państwowe), Generalna Dyrekcja Ochrony Środowiska. Szczegóły i daty pobrania pojawią się w `data/static/attribution.json` (etap 1).
