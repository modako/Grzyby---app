# Prompty dla Claude Code – aplikacja dla grzybiarzy

Oct 5, 2026 · @Adam2

## Jak używać

Wklejaj prompty do Claude Code po kolei, jeden etap na sesję. Kolejny etap zaczynaj dopiero wtedy, gdy poprzedni działa.

1. Utwórz pusty folder projektu, np. `grzyby-app`, i uruchom w nim Claude Code.
2. Pobierz raport z researchu jako Markdown i zapisz go w projekcie jako `docs/research.md`. Każdy etap się do niego odwołuje.
3. Po każdym etapie Claude Code zatrzyma się i poda raport: co zrobił, jak to sprawdzić i co nie działa. Wklej mi ten raport, a sprawdzę go przed następnym etapem.
4. Gdy Claude Code o coś pyta (konto, instalacja, wybór), odpowiadaj mu bezpośrednio. Prompty każą mu tłumaczyć wszystko prostym językiem.

Przygotuj: darmowe konto GitHub, telefon z Androidem (albo emulator) i darmowe konto Expo. Node.js i Pythona Claude Code pomoże zainstalować.

## Decyzje techniczne

Aplikacja powstaje od razu na Androida i iOS z jednego kodu (Expo / React Native). Testujemy na Androidzie, a iOS dochodzi w etapie 6 prawie bez dodatkowej pracy.

| Obszar | Wybór | Dlaczego |
| --- | --- | --- |
| Aplikacja | Expo + React Native + TypeScript | jeden kod na Androida i iOS; build w chmurze (EAS), więc iOS nie wymaga Maca |
| Mapa | MapLibre (`@maplibre/maplibre-react-native`) | darmowa, bez kluczy, obsługuje mapy offline; wymaga „development build” zamiast Expo Go |
| Obliczenia | Python, uruchamiany codziennie przez GitHub Actions | bez własnego serwera i bez kosztów; wynik to statyczne pliki, które aplikacja pobiera |
| Las na mapie | heksagony H3 (ok. 0,7 km²) w obrębie lasów | równa siatka, łatwa do kolorowania i dołączania danych |
| Pogoda | Open-Meteo (darmowe do użytku niekomercyjnego) | prognoza na 16 dni, wilgotność gleby, parowanie (ET₀) |
| Dane o lasach | BDL Lasów Państwowych, GDOŚ, OpenStreetMap | gatunek, wiek i siedlisko drzewostanu oraz granice parków, rezerwatów i poligonów |
| Region startowy | lubuskie + wielkopolskie | najwyższa lesistość kraju; Puszcza Notecka, Barlinecka i Gorzowska |

Najważniejszy trik: potencjał lasu (H) liczy się raz, a codziennie zmienia się tylko pogoda (W) dla kilkuset punktów siatki. Aplikacja łączy jedno z drugim sama, więc codzienny plik ma kilkadziesiąt kilobajtów, a nie megabajty.

## Etap 0: setup projektu i specyfikacja

Cel: repozytorium, plik `CLAUDE.md` z zasadami projektu i `docs/SPEC.md` z modelem prognozy. Na tym etapie nie powstaje jeszcze kod aplikacji.

```text
Zaczynamy projekt: aplikacja mobilna dla grzybiarzy w Polsce (Android + iOS, na start testy na Androidzie). Na razie tylko do mojego prywatnego użytku, później może publiczna.

Kontekst: nie jestem programistą. Rozmawiaj ze mną po polsku i tłumacz prostym językiem, co robisz i co mam kliknąć albo zainstalować. Kod, nazwy plików, zmiennych i komentarze w kodzie pisz po angielsku. Interfejs aplikacji będzie po polsku.

W docs/research.md jest raport z researchu (lasy, model prognozy, źródła danych, prawo, konkurencja). Przeczytaj go cały, zanim cokolwiek zrobisz.

Zadania w tym etapie (bez pisania aplikacji):

1. Załóż strukturę monorepo:
   - pipeline/  (Python: pobieranie danych, obliczenia indeksu)
   - app/       (Expo / React Native, powstanie w etapie 3)
   - data/      (wygenerowane pliki, w .gitignore poza małymi plikami testowymi)
   - docs/
   Zainicjuj git, dodaj sensowny .gitignore i krótki README po polsku.

2. Utwórz CLAUDE.md z zasadami projektu:
   - cel aplikacji i plan etapów 0–6 (lista poniżej),
   - stack: Python 3.11+ (geopandas, shapely, h3, requests, numpy) w pipeline; Expo + TypeScript + @maplibre/maplibre-react-native w app; obliczenia codziennie przez GitHub Actions, wynik jako statyczne pliki,
   - region pilotażowy: woj. lubuskie + wielkopolskie,
   - zasady bezpieczeństwa: aplikacja NIGDY nie ocenia jadalności grzyba i nie rozpoznaje grzybów ze zdjęcia; obszary bez prawa wstępu lub zbioru (parki narodowe, rezerwaty, poligony, zakazy wstępu) są zawsze szare i nigdy nie dostają koloru zielonego,
   - zasada pracy: po każdym etapie zatrzymaj się i napisz raport (co zrobione, jak przetestować, co nie działa, jakie decyzje podjąłeś); nie zaczynaj kolejnego etapu bez mojej zgody,
   - zasada danych: zanim użyjesz zewnętrznego API lub usługi (BDL, GDOŚ, Open-Meteo), sprawdź, jak naprawdę działa (GetCapabilities, przykładowe zapytanie). Nie zgaduj nazw warstw ani pól.

3. Utwórz docs/SPEC.md: przepisz wiernie z docs/research.md (sekcja 2.4 i powiązane) model „Indeksu Grzybowego”: potencjał siedliskowy H, składowe M, L, T, S, wzór końcowy, progi kolorów (≥60 zielony, 35–59 żółty, <35 czerwony, szary = brak wstępu) oraz tabelę gatunek grzyba → drzewa, wiek drzewostanu i siedlisko (sekcja 1.3). Wszystkie liczby wpisz jako parametry w jednym miejscu (np. tabela parametrów z wartościami domyślnymi), bo później będziemy je kalibrować. Zaznacz wyraźnie, że to wartości startowe do kalibracji.

   Dodaj decyzję architektoniczną: H (per komórka lasu i gatunek grzyba) liczy się rzadko; codziennie liczy się tylko składowa pogodowa W per punkt siatki pogodowej (ok. 0,1°) i dzień, w dwóch wariantach: dla grzybów mikoryzowych oraz dla gatunków odpornych na przymrozki (opieńki, gąski). Aplikacja łączy IG = W · (0,4 + 0,6·H) po swojej stronie.

4. Plan etapów (wpisz do CLAUDE.md):
   0. Setup i specyfikacja
   1. Pipeline danych o lasach (BDL, GDOŚ, OSM) i potencjał H
   2. Pogoda (Open-Meteo), składowa W, codzienny cron w GitHub Actions
   3. Aplikacja mobilna MVP z mapą
   4. Dziennik grzybobrań i kalibracja
   5. Popularność lasów i „ukryte perełki”
   6. Powiadomienia, offline, dynamiczne zakazy, build iOS

5. Sprawdź, co mam zainstalowane (node, npm, python, git) i podaj mi listę braków z instrukcją instalacji krok po kroku dla mojego systemu.

Na koniec: raport po polsku i stop.
```

## Etap 1: dane o lasach i potencjał H

Cel: mapa heksagonów lasu dla lubuskiego i wielkopolskiego, z potencjałem per gatunek grzyba i maską „tu nie wolno”. Efekt sprawdzisz na podglądowej mapie w przeglądarce.

```text
Etap 1 według CLAUDE.md i docs/SPEC.md: pipeline danych o lasach i potencjał siedliskowy H. Region: woj. lubuskie + wielkopolskie.

1. Drzewostany z Banku Danych o Lasach (BDL):
   - Najpierw sprawdź usługę WFS https://wfs.bdl.lasy.gov.pl/geoserver/BDL/ows (GetCapabilities, DescribeFeatureType). Ustal, które warstwy zawierają wydzielenia i jakie pola opisują gatunek panujący, wiek, typ siedliskowy lasu i formę własności. Pokaż mi, co znalazłeś, zanim zaczniesz pobierać dużo danych.
   - Pobierz wydzielenia dla regionu (stronicowanie, ponawianie przy błędach, cache na dysku, żeby nie pobierać dwa razy).
   - Jeśli WFS nie daje potrzebnych pól albo nie działa: powiedz mi to. Wtedy alternatywy to SHP na wniosek (bdl.lasy.gov.pl/portal/wniosek, złożę go sam) albo tymczasowo poligony lasów z OpenStreetMap z typem liściastym/iglastym jako uproszczonym H.
   - Zapisz źródło i datę pobrania (wymóg BDL).

2. Maska prawna (obszary zakazane):
   - parki narodowe i rezerwaty przyrody z GDOŚ (WFS sdi.gdos.gov.pl/wfs albo SHP z gov.pl/web/gdos/dostep-do-danych-geoprzestrzennych; sprawdź, co działa),
   - tereny wojskowe z OSM (landuse=military, military=*),
   - uprawy leśne (młodniki do ok. 4 m) z BDL, jeśli da się je rozpoznać po wieku lub opisie (stały zakaz wstępu),
   - lasy prywatne oznacz osobną flagą „prywatny, może być zakaz” (nie szare, tylko ostrzeżenie).

3. Siatka H3 w rozdzielczości 8 na obszarze lasów regionu. Dla każdej komórki policz (ważone powierzchnią wydzieleń): udział gatunków drzew, średni wiek, dominujące siedlisko, procent powierzchni zakazanej. Komórka jest „zakazana”, gdy >50% jej lasu jest w masce.

4. H per gatunek grzyba wg docs/SPEC.md: borowik, podgrzybek, koźlarz, maślak, kurka, rydz, kania, opieńka, gąska. Do tego H_max = max po gatunkach. Funkcje przydatności pisz jako czyste funkcje z parametrami z jednego pliku konfiguracyjnego i dodaj do nich testy jednostkowe (pytest).

5. Wyjście (data/static/):
   - geometria komórek (preferuj PMTiles; jeśli to zbyt skomplikowane, uproszczony GeoJSON) z polami: id komórki, H per gatunek, H_max, flagi prawne, opis drzewostanu,
   - cells_meta.json ze środkami komórek i przypisaniem do punktu siatki pogodowej 0,1° (potrzebne w etapie 2),
   - attribution.json z atrybucjami źródeł.

6. Podgląd: wygeneruj jeden plik HTML (MapLibre GL JS albo folium) z komórkami pokolorowanymi wg H_max, szarymi obszarami zakazanymi i popupem z danymi komórki. Mam go otworzyć w przeglądarce.

7. Całość ma się uruchamiać jednym poleceniem (np. python -m pipeline.build_static). Opisz je w README.

Raport: liczba komórek, rozkład H_max, ile komórek zakazanych, rozmiar plików, problemy z danymi, decyzje i założenia. Dodaj trzy kontrolne miejsca, które mogę sam sprawdzić (np. komórka w Puszczy Noteckiej i w parku narodowym). Stop.
```

## Etap 2: pogoda i Indeks Grzybowy

Cel: codziennie o świcie GitHub sam pobiera pogodę, liczy indeks na 14 dni do przodu i publikuje mały plik dla aplikacji. Dodatkowo test na zeszłym sezonie: czy indeks reaguje na deszcz z opóźnieniem.

```text
Etap 2 według CLAUDE.md i docs/SPEC.md: pogoda, składowa W i automatyzacja.

1. Punkty siatki pogodowej: unikalne punkty 0,1° z data/static/cells_meta.json (tylko te, które zawierają las).

2. Open-Meteo Forecast API (sprawdź aktualną dokumentację parametrów na open-meteo.com):
   - dane dzienne dla dni od -30 do +14 (past_days + forecast_days): suma opadu, temperatura średnia, minimalna i maksymalna, ewapotranspiracja ET₀,
   - wilgotność gleby z warstw najbliższych 0–28 cm (godzinowe uśrednione do doby),
   - wiele współrzędnych w jednym zapytaniu, pauzy między zapytaniami; pilnuj darmowego limitu (10 000 wywołań na dobę, użytek niekomercyjny) i policz, ile wywołań zużywa jedno uruchomienie.
   - Do percentyla wilgotności gleby potrzebna jest klimatologia: pobierz raz (i zapisz) dane historyczne z Open-Meteo Archive API (ERA5-Land) dla każdego punktu, ok. 10 lat, i licz percentyl względem tego samego miesiąca. Uważaj na spójność głębokości warstw między prognozą a ERA5-Land; jeśli nie da się jej zachować, zaproponuj rozwiązanie i zapisz decyzję w SPEC.md.

3. Oblicz M, L, T, S i W dokładnie wg docs/SPEC.md, w dwóch wariantach: W_myc (grzyby mikoryzowe) i W_frost (opieńki, gąski: łagodniejsza kara za przymrozek). Dla dni +8…+14 dodaj przedział niepewności (np. min–max z kilku modeli dostępnych w Open-Meteo); jeśli to zbyt kosztowne w wywołaniach, zaproponuj prostsze rozwiązanie.

4. Wyjście: data/daily/latest.json (oraz kopia z datą w nazwie):
   { generated_at, dates: [...], points: { point_id: { w_myc: [...], w_frost: [...], w_low: [...], w_high: [...], rain: [...], tmean: [...] } } }
   Liczby zaokrąglaj, plik ma być mały. Zapisz w nim też wersję parametrów modelu.

5. Funkcja pomocnicza (Python) liczy IG = W · (0,4 + 0,6·H) dla dowolnej komórki i gatunku. Taka sama logika trafi później do aplikacji, więc opisz ją w SPEC.md jako kontrakt i dodaj przypadki testowe (wejście → oczekiwany wynik), które wykorzystamy w testach aplikacji.

6. Backtest: dla 5 komórek (różne lasy) policz IG dzień po dniu za VIII–X 2025 z danych historycznych i zrób wykres PNG: opad (słupki) + IG (linia). Chcę zobaczyć, czy indeks rośnie ok. 7–14 dni po dużym deszczu i spada po przymrozkach. Opisz, co widać i co wygląda podejrzanie.

7. GitHub Actions: workflow codziennie ok. 04:00 czasu polskiego (pamiętaj, że cron jest w UTC) plus ręczne uruchamianie. Publikacja latest.json i plików statycznych z etapu 1 pod stałym adresem URL. Dane nie są wrażliwe: zaproponuj najprostsze darmowe rozwiązanie (np. GitHub Pages; jeśli repo z kodem ma zostać prywatne, osobne publiczne repo tylko na dane). Przeprowadź mnie krok po kroku przez to, co muszę kliknąć na GitHubie.

Raport: liczba wywołań API na uruchomienie, czas działania, rozmiar latest.json, wykresy backtestu z interpretacją, adres URL z danymi, problemy. Stop.
```

## Etap 3: aplikacja mobilna MVP

Cel: pierwsza wersja na telefon z mapą kolorowych lasów, suwakiem dni i kartą lasu. Instalujesz ją na Androidzie z pliku APK.

```text
Etap 3 według CLAUDE.md i docs/SPEC.md: aplikacja mobilna MVP w app/.

Stack: Expo (najnowszy stabilny SDK) + TypeScript + expo-router + @maplibre/maplibre-react-native. MapLibre wymaga development build (expo-dev-client), nie Expo Go: przygotuj konfigurację EAS i przeprowadź mnie przez zbudowanie i instalację APK na moim Androidzie krok po kroku. Kod ma od początku działać też na iOS (bez rozwiązań tylko dla Androida), ale testujemy na Androidzie.

Podkład mapy: darmowe kafelki wektorowe bez klucza (np. OpenFreeMap). Nie używaj intensywnie tile.openstreetmap.org. Atrybucje OSM, Open-Meteo, BDL i GDOŚ muszą być widoczne.

Ekrany (UI po polsku, prosty i czytelny w terenie: duże przyciski, czytelny w słońcu):

1. Mapa (ekran główny):
   - komórki lasu z etapu 1 pokolorowane wg IG: zielony ≥60, żółty 35–59, czerwony <35, szary = zakaz (nigdy nie kolorowany inaczej),
   - IG liczony w aplikacji: W z latest.json (punkt pogodowy komórki) × (0,4 + 0,6·H) wg kontraktu ze SPEC.md; dodaj testy z przypadkami testowymi z etapu 2,
   - suwak dni: dziś … +14, z wyraźnym oznaczeniem, że dni +8…+14 są niepewne,
   - filtr gatunku: „wszystkie” (H_max) albo konkretny gatunek,
   - legenda, przycisk „moja lokalizacja” (expo-location, pytanie o zgodę po polsku).

2. Karta lasu (po kliknięciu komórki):
   - IG dziś, najlepszy dzień w najbliższych 14 dniach i okno dni z IG ≥60,
   - wykres IG na 14 dni z opadem w tle,
   - gatunki grzybów posortowane wg H z krótkim uzasadnieniem (np. „sosna 60 lat → podgrzybek”),
   - opis drzewostanu, status prawny (zakaz / prywatny / OK), miejsce na „popularność” (wypełnimy w etapie 5),
   - przycisk „Nawiguj” otwierający Google Maps / Apple Maps do środka komórki.

3. Ustawienia / Info: źródła danych i atrybucje, data ostatniej aktualizacji, opis kolorów oraz ostrzeżenie: „Aplikacja nie rozpoznaje grzybów i nie ocenia ich jadalności. W razie wątpliwości skonsultuj się z grzyboznawcą”.

Dane: pobieranie latest.json i plików statycznych z adresu z etapu 2, cache na urządzeniu (działa bez internetu na ostatnich danych, z informacją „dane z dnia …”), odświeżanie przy starcie, jeśli dane są starsze niż 12 h.

Wydajność: kilkadziesiąt tysięcy komórek ma się płynnie przewijać na średnim telefonie z Androidem. Jeśli GeoJSON jest za ciężki, użyj PMTiles lub kafelków wektorowych i łączenia danych przez feature-state / wyrażenia stylu. Sprawdź i opisz, co działa w MapLibre React Native.

Raport: zrzuty ekranu (z emulatora, jeśli możesz), instrukcja instalacji na telefonie, znane problemy, co trzeba poprawić przed etapem 4. Stop.
```

## Etap 4: dziennik grzybobrań i kalibracja

Cel: zapisujesz każdy wypad, a aplikacja porównuje prognozę z tym, co faktycznie znalazłeś. Z czasem model dopasuje się do Twoich lasów. To najważniejszy etap dla skuteczności.

```text
Etap 4 według CLAUDE.md i docs/SPEC.md: dziennik grzybobrań i kalibracja modelu.

1. Dziennik w aplikacji (dane tylko na telefonie, expo-sqlite):
   - nowy wypad: data, komórka lasu (z GPS albo wybrana na mapie), czas zbierania w godzinach, liczba grzybów per gatunek (szybkie przyciski +/- dla 9 gatunków ze SPEC.md), zero też jest ważną informacją, notatka, opcjonalnie zdjęcie (tylko do pamiątki, bez rozpoznawania),
   - przy zapisie automatycznie zachowaj „snapshot” prognozy: IG, W, H i wersję parametrów modelu dla tej komórki i dnia,
   - lista wypadów, edycja, usuwanie,
   - moje miejscówki: ulubione komórki, widoczne na mapie z własną ikoną.

2. Ekran „Skuteczność prognozy”:
   - wykres punktowy: IG w dniu wypadu vs grzyby na godzinę,
   - korelacja rang (Spearman) i liczba wypadów, z jasnym komunikatem, że poniżej ok. 30 wypadów wynik jest tylko orientacyjny,
   - podsumowanie: średnio grzybów/h przy zielonym, żółtym i czerwonym kolorze.

3. Eksport i import: CSV / JSON przez systemowe „Udostępnij” (kopia zapasowa i dane do kalibracji). Import z pliku do przywrócenia dziennika na nowym telefonie.

4. Kalibracja w pipeline (pipeline/calibrate.py):
   - wejście: wyeksportowany CSV,
   - regresja Poissona lub ujemna dwumianowa (liczba grzybów, offset = log czasu zbierania) na składowych M, L, T, S i H,
   - wynik: proponowane nowe parametry + porównanie błędu starego i nowego modelu (walidacja krzyżowa, żeby nie przeuczyć na kilkudziesięciu wypadach),
   - parametry NIE podmieniają się automatycznie: generuje się raport, a ja decyduję, czy je przyjąć (nowa wersja parametrów w configu).
   Dołącz sztuczny zbiór testowy (ok. 50 wypadów), żeby pokazać, że skrypt działa.

5. Prywatność: żadne dane z dziennika nie wychodzą z telefonu bez mojego eksportu.

Raport: zrzuty ekranu, instrukcja eksportu i uruchomienia kalibracji, wynik na danych testowych. Stop.
```

## Etap 5: popularność i ukryte perełki

Cel: każdy las dostaje szacunek „presji grzybiarzy”, a aplikacja pokazuje listę lasów z dobrym potencjałem i małą liczbą ludzi. To oszacowanie z danych, nie pomiar.

```text
Etap 5 według CLAUDE.md, docs/SPEC.md i docs/research.md (sekcja 4): popularność lasów i „ukryte perełki”.

1. Indeks presji P (0–100) per komórka, liczony w pipeline (statycznie, np. raz na kwartał):
   - 40%: liczba mieszkańców w zasięgu ok. 30 i 60 minut jazdy. Źródło ludności: siatka kilometrowa GUS (sprawdź aktualną dostępność i licencję). Czas dojazdu: zaproponuj najprostszą sensowną metodę (np. odległość po sieci dróg OSM albo uproszczenie odległością w linii prostej z korektą) i opisz jej ograniczenia,
   - 25%: dostępność: parkingi leśne i drogi publiczne w pobliżu (OSM), infrastruktura turystyczna z BDL, jeśli jest dostępna w WFS,
   - 15%: gęstość obserwacji grzybów z GBIF dla Polski na km² lasu (użyj tylko rekordów CC0 i CC BY i zapisz licencje),
   - 20%: ręczna lista regionów uznanych za popularne w mediach (z tabeli regionalnej w docs/research.md, kolumna „Popularny vs mało znany”), jako poligony lub obszary nadleśnictw w pliku konfiguracyjnym, który mogę edytować.
   Wagi w configu. Klasy: „popularny” (P ≥ 60), „umiarkowany”, „mało znany” (P < 30).

2. „Ukryte perełki”: komórki (lub skupiska sąsiednich komórek, żeby nie pokazywać pojedynczych heksagonów) z wysokim H_max, niskim P i bez zakazów. Ranking zapisany w pliku statycznym.

3. W aplikacji:
   - na karcie lasu: popularność (klasa + krótkie „dlaczego”, np. „2 parkingi, 180 tys. osób w 30 min”),
   - nowy ekran „Perełki”: lista posortowana wg połączenia potencjału, prognozy na najbliższe dni i odległości ode mnie, z przyciskiem „Pokaż na mapie”,
   - opcjonalna warstwa mapy „popularność”,
   - wyraźny dopisek: „oszacowanie na podstawie danych, nie liczba osób w lesie”.

4. Porównaj wynik z listą hipotez z docs/research.md (sekcja 1.2: Bory Stobrawskie, Puszcza Barlinecka itd.) dla regionu pilotażowego: które wyszły jako perełki, które nie i dlaczego.

Raport: top 20 perełek z krótkim uzasadnieniem, ograniczenia metody, zrzuty ekranu. Stop.
```

## Etap 6: powiadomienia, offline, zakazy i iOS

Cel: aplikacja sama informuje o dobrych warunkach, działa w lesie bez zasięgu, pokazuje bieżące zakazy wstępu i zagrożenie pożarowe oraz ma build na iPhone'a. Po tym etapie można rozszerzać region na całą Polskę.

```text
Etap 6 według CLAUDE.md i docs/SPEC.md: powiadomienia, offline, dynamiczne zakazy i build iOS.

1. Powiadomienia (expo-notifications + zadanie w tle, np. expo-background-task; sprawdź aktualne API Expo):
   - ustawienia: promień od mojej lokalizacji lub tylko ulubione lasy, próg IG, gatunki,
   - raz dziennie po pobraniu nowych danych: jeśli w najbliższych 1–3 dniach jakiś las spełnia warunki, wyślij lokalne powiadomienie, np. „Sobota: borowiki – zielono w 4 lasach w promieniu 50 km”,
   - bez własnego serwera; opisz ograniczenia zadań w tle na Androidzie i iOS.

2. Tryb offline w lesie:
   - pobieranie regionu mapy (podkład + komórki + ostatnie dane) do pamięci telefonu, z rozmiarem do pobrania podanym przed startem,
   - zapis śladu GPS wypadu i przycisk „wróć do auta” (zapamiętana pozycja parkingu); wszystko tylko na telefonie,
   - wyraźna informacja o wieku danych.

3. Dynamiczne warstwy z BDL:
   - okresowe zakazy wstępu do lasu i stopień zagrożenia pożarowego jako warstwy WMS na mapie (sprawdź aktualne adresy i nazwy warstw przez GetCapabilities),
   - na karcie lasu ostrzeżenie, jeśli komórka leży w strefie zakazu lub wysokiego zagrożenia pożarowego; jeśli da się to sprawdzić automatycznie (np. GetFeatureInfo), uwzględnij to w kolorze szarym.

4. iOS:
   - sprawdź, czy wszystko działa na iOS (uprawnienia lokalizacji i powiadomień, teksty zgód po polsku, nawigacja do Apple Maps),
   - przygotuj build przez EAS i wyjaśnij mi opcje: symulator (wymaga Maca), instalacja na iPhonie (wymaga płatnego konta Apple Developer), TestFlight. Nic nie kupuj ani nie wysyłaj do sklepów bez mojej zgody.

5. Rozszerzenie regionu: przygotuj pipeline tak, żeby dodanie kolejnych województw było zmianą w configu. Oszacuj liczbę wywołań Open-Meteo i rozmiar danych dla całej Polski i powiedz, czy zmieści się w darmowym limicie.

6. Lista kontrolna przed ewentualną wersją publiczną (tylko dokument, bez wdrażania): licencja Open-Meteo do użytku komercyjnego (plan obejmujący API historyczne), atrybucje (CC BY 4.0, ODbL, BDL, GDOŚ), licencje danych GBIF, RODO i polityka prywatności, zgłoszenia od użytkowników zaokrąglane do siatki ok. 7 km z opóźnieniem, publikacja skuteczności prognozy.

Raport: co działa na Androidzie i iOS, instrukcje, koszty (jeśli jakieś są), lista kontrolna. Stop.
```


## Etap 2 (wersja zaktualizowana przez właściciela, 2026-10-06)

Ta wersja zastępuje prompt etapu 2 powyżej.

```text
Etap 2 według CLAUDE.md i docs/SPEC.md: pogoda, składowa W i automatyzacja.

Ważne: z mojego środowiska część zewnętrznych serwerów zrywa połączenie (tak było z OSM). Dlatego każde wywołanie Open-Meteo (prognoza, archiwum ERA5-Land, backtest) uruchamiaj w GitHub Actions, a nie lokalnie. Najpierw sprawdź, czy Open-Meteo odpowiada z Twojego środowiska. Jeśli tak, możesz testować lokalnie, ale produkcyjnie i tak liczy Actions. Pracuję tylko na telefonie: nic nie każ mi robić w ustawieniach na komputerze, a kroki na GitHubie opisz na aplikację GitHub albo przeglądarkę w telefonie.

1. Punkty siatki pogodowej: unikalne punkty 0,1° z data/static/cells_meta.json (tylko te z lasem, bez komórek całkowicie zakazanych).
2. Open-Meteo: prognoza dni -30..+14 (opad, Tśr, Tmin, Tmax, ET0, wilgotność gleby 0-28 cm uśredniona do doby), wiele współrzędnych w zapytaniu, pauzy, ponawianie 429/5xx. Policz wywołania przed pierwszym pełnym biegiem. Klimatologia ERA5-Land ok. 10 lat w data/climatology/, percentyl względem miesiąca, zgodność warstw gleby (decyzja w SPEC.md).
3. M, L, T, S, W wg SPEC.md w wariantach W_myc i W_frost; przedział niepewności dni +8..+14 (min-max z kilku modeli) albo prostszy sposób.
4. Wyjście: data/daily/latest.json + kopia z datą: { generated_at, params_version, dates, points: { point_id: { w_myc, w_frost, w_low, w_high, rain, tmean } } }.
5. Funkcja IG = W · (0,4 + 0,6·H) jako kontrakt w SPEC.md + przypadki testowe w JSON (dla aplikacji w etapie 3) + pytest.
6. Backtest w Actions: 5 komórek, VIII-X 2025, PNG opad (słupki) + IG (linia); czy IG rośnie 7-14 dni po deszczu i spada po przymrozkach; jak obejść brak archiwalnych prognoz.
7. Workflow: codziennie ok. 04:00 czasu polskiego (zmiana czasu), ręczne uruchamianie, publikacja latest.json i plików statycznych pod stałym URL (GitHub Pages; przy prywatnym repo osobne publiczne repo na dane), permissions w pliku, uruchamianie po scaleniu (właściciel tylko klika Merge w aplikacji GitHub).

Raport po polsku: wywołania API na uruchomienie, czas, rozmiar latest.json, wykresy backtestu z interpretacją, URL z danymi, co kliknąć na telefonie, problemy. Stop.
```
