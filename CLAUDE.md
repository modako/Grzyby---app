# CLAUDE.md: aplikacja dla grzybiarzy

## Cel

Aplikacja mobilna (Android + iOS z jednego kodu) dla grzybiarzy w Polsce. Pokazuje na mapie, **gdzie** (potencjał lasu z danych o drzewostanach) i **kiedy** (prognoza pogodowa na 14 dni) warto jechać na grzyby, z twardą maską miejsc, gdzie zbierać nie wolno. Na start do prywatnego użytku właściciela, później może publiczna. Testy na Androidzie.

## Zasady współpracy

- **Rozmawiaj z właścicielem po polsku**, prostym językiem. Właściciel nie jest programistą: tłumacz, co robisz, i podawaj krok po kroku, co ma kliknąć lub zainstalować.
- **Kod, nazwy plików, zmiennych i komentarze w kodzie: po angielsku.** Interfejs aplikacji: po polsku.
- **Po każdym etapie zatrzymaj się i napisz raport** po polsku: co zrobione, jak to przetestować, co nie działa, jakie decyzje podjąłeś. **Nie zaczynaj kolejnego etapu bez zgody właściciela.**
- **Zasada danych:** zanim użyjesz zewnętrznego API lub usługi (BDL, GDOŚ, Open-Meteo, OSM, GUS, GBIF), sprawdź, jak naprawdę działa (GetCapabilities, DescribeFeatureType, przykładowe zapytanie, aktualna dokumentacja). **Nie zgaduj nazw warstw ani pól.**
- Parametry modelu nie są zakodowane na sztywno w wielu miejscach: jedno źródło prawdy to tabela w `docs/SPEC.md` (rozdział 7), odzwierciedlona 1:1 w pliku konfiguracyjnym pipeline. Każda zmiana parametru podbija `params_version`.
- Decyzje, które zmieniają model albo kontrakt danych, zapisuj w `docs/SPEC.md`.

## Zasady bezpieczeństwa (nienaruszalne)

1. Aplikacja **NIGDY nie ocenia jadalności grzyba** i **nie rozpoznaje grzybów ze zdjęcia** (zdjęcia w dzienniku są tylko pamiątką).
2. Obszary bez prawa wstępu lub zbioru (parki narodowe, rezerwaty, poligony i tereny wojskowe, uprawy leśne do ok. 4 m, zakazy wstępu) są **zawsze szare** i **nigdy nie dostają koloru zielonego** (ani żółtego czy czerwonego), niezależnie od prognozy.
3. Lasy prywatne: osobna flaga „prywatny, może być zakaz” (ostrzeżenie, nie szary).
4. Stałe ostrzeżenie w aplikacji: „Aplikacja nie rozpoznaje grzybów i nie ocenia ich jadalności. W razie wątpliwości skonsultuj się z grzyboznawcą”.
5. Dane z dziennika grzybobrań nie wychodzą z telefonu bez świadomego eksportu przez właściciela.

## Stack

| Część | Technologia |
|---|---|
| Pipeline (`pipeline/`) | Python 3.11+: geopandas, shapely, h3, requests, numpy (+ pandas, pyproj, pyogrio); testy: pytest |
| Aplikacja (`app/`) | Expo (najnowszy stabilny SDK) + TypeScript + expo-router + `@maplibre/maplibre-react-native` (wymaga development build, nie Expo Go); build w chmurze przez EAS |
| Automatyzacja | GitHub Actions, codziennie ok. 04:00 czasu polskiego (cron w UTC) |
| Publikacja danych | statyczne pliki (np. GitHub Pages); bez własnego serwera |
| Pogoda | Open-Meteo (Forecast + Archive/ERA5-Land), darmowe do użytku niekomercyjnego, limit 10 000 wywołań/dobę, atrybucja CC BY 4.0 |
| Lasy i maska | BDL Lasów Państwowych (WFS/WMS/SHP), GDOŚ (WFS/SHP), OpenStreetMap (ODbL) |
| Podkład mapy | darmowe kafelki wektorowe bez klucza (np. OpenFreeMap); nie obciążać tile.openstreetmap.org |

**Architektura (ADR-001 w `docs/SPEC.md`):** potencjał lasu H (per komórka H3 rozdz. 8 i gatunek grzyba) liczy się rzadko i jest plikiem statycznym. Codziennie liczy się tylko składowa pogodowa W per punkt siatki 0,1° i dzień, w wariantach `W_myc` i `W_frost`. Aplikacja liczy `IG = W · (0,4 + 0,6·H)` po swojej stronie.

## Region pilotażowy

Województwo **łódzkie** (decyzja właściciela z 2026-10-06: tam mieszka; kolejne województwa będą dochodzić z czasem). Pierwotny plan z researchu zakładał lubuskie + wielkopolskie. Region ustawia `pipeline/config/region.yaml`; dodanie województwa ma być zmianą w tym pliku.

## Struktura repozytorium

```
pipeline/   Python: pobieranie danych, obliczenia H i W, kalibracja
app/        Expo / React Native (od etapu 3)
data/       wygenerowane pliki (w .gitignore); małe pliki testowe w data/samples/; ręcznie pobrane źródła w data/manual/
docs/       research.md, research_z_przypisami.md, SPEC.md, PROMPTY.md, DATA_SOURCES.md
```

## Plan etapów

0. **Setup i specyfikacja**: struktura repo, CLAUDE.md, `docs/SPEC.md`.
1. **Pipeline danych o lasach** (BDL, GDOŚ, OSM) i potencjał H: siatka H3, maska prawna, podgląd HTML.
2. **Pogoda** (Open-Meteo), składowa W, backtest, codzienny cron w GitHub Actions, publikacja danych.
3. **Aplikacja mobilna MVP z mapą**: kolory IG, suwak dni, karta lasu, APK na Androida.
4. **Dziennik grzybobrań i kalibracja**: zapis wypadów, skuteczność prognozy, `pipeline/calibrate.py`.
5. **Popularność lasów i „ukryte perełki”**: indeks presji P.
6. **Powiadomienia, offline, dynamiczne zakazy, build iOS**, rozszerzenie regionu.

Pełne prompty etapów: `docs/PROMPTY.md`. Status etapów:

| Etap | Status |
|---|---|
| 0 | zrobiony |
| 1 | zrobiony (łódzkie) |
| 2 | w toku (gałąź `claude/etap-2-pogoda`) |
| 3–6 | nie rozpoczęte |

## Repozytorium

- Główne repozytorium: **`modako/grzyby---app`**, gałąź `main` (od 2026-10-06; projekt przeniesiony na prośbę właściciela razem z historią).
- `modako/Claude-Adam` (gałąź `claude/new-session-5aqwhf`) to stara kopia z etapów 0–1. Nie rozwijamy jej dalej.

## Uwagi o środowisku

- Praca toczy się w sesjach Claude Code w chmurze (kontener tworzony na nowo w każdej sesji). Wszystko, co ma przetrwać, musi być w repo (commit + push).
- Dostęp do sieci (stan na 2026-10-05, po dodaniu domen do dozwolonych w ustawieniach środowiska):
  - działa: `wfs.bdl.lasy.gov.pl`, `api.open-meteo.com`, `archive-api.open-meteo.com`, `tiles.openfreemap.org`, `www.gov.pl`, PyPI, npm;
  - `sdi.gdos.gov.pl`: serwer GDOŚ sam odrzuca chmurę (filtr Incapsula, 403). Pliki parków narodowych i rezerwatów pobrał ręcznie właściciel: `data/manual/gdos/` (opis w `SOURCES.md`). Nie próbuj pobierać ich automatycznie;
  - `download.geofabrik.de`, `overpass-api.de`: połączenie zrywane po stronie serwera. Dane OSM (lasy, tereny wojskowe) wyciąga workflow `.github/workflows/osm-extract.yml` na GitHub Actions i commituje do `data/manual/osm/`. Uruchamia się sam po zmianie `pipeline/config/region.yaml`;
  - `cdnjs.cloudflare.com`, `unpkg.com`, `mapserver.bdl.lasy.gov.pl`: nie są na liście dozwolonych (pakiety JS bierzemy z npm).
- **Open-Meteo: produkcyjnie tylko z GitHub Actions** (prośba właściciela). Z chmury Claude archiwum Open-Meteo szybko zwraca „Daily API request limit exceeded” (wspólny adres IP). Lokalnie wolno najwyżej pojedyncze zapytania testowe.
- Właściciel pracuje **tylko na telefonie**: kroki na GitHubie opisuj dla aplikacji GitHub albo przeglądarki w telefonie; zmiany trafiają do `main` przez Pull Request, który właściciel scala przyciskiem „Merge”.
- Pliki źródłowe pobierane ręcznie trzymamy w `data/manual/` (wyjątek w `.gitignore`), razem ze źródłem, datą pobrania i sumą kontrolną.
