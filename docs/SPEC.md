# SPEC: Indeks Grzybowy (IG)

Wersja specyfikacji: **0.3** (etap 2: pogoda, W, kontrakt IG) · wersja parametrów modelu: **`params_version = "0.2.0"`** (0.2.0: parametry lasów spoza LP i maski z BDL, etap 1)

Źródło: `docs/research.md`, sekcje 1.3, 2.2 i 2.4 (wersja z przypisami: `docs/research_z_przypisami.md`).

> **Uwaga: wszystkie liczby w tym dokumencie to wartości startowe do kalibracji.**
> Nie ma opublikowanego, zwalidowanego modelu owocnikowania dla Polski. Progi pochodzą z badań zagranicznych (Niemcy, Hiszpania, Szwajcaria, Japonia) i z metodologii czeskiego ČHMÚ. Zmienią się po kalibracji na własnych wypadach (etap 4).
>
> Oznaczenia w kolumnie „Źródło”:
> - **[R]**: wartość wprost z `docs/research.md`,
> - **[P]**: propozycja dopisana w etapie 0, bo research podaje tylko kierunek (np. „młodsze”, „starsze”) albo nic. Przy kalibracji traktuj [P] z mniejszym zaufaniem niż [R].

---

## 1. Przegląd

```
IG(komórka, gatunek g, dzień d) = W_v(g)(punkt, d) · (0,4 + 0,6 · H_g(komórka))
```

- **H** (potencjał siedliskowy, 0–1): statyczny, per komórka lasu H3 i gatunek grzyba. Liczony rzadko (raz w roku albo przy zmianie danych BDL).
- **W** (składowa pogodowa, 0–100): dynamiczna, per punkt siatki pogodowej i dzień. Liczona codziennie w dwóch wariantach `v`:
  - `W_myc`: grzyby mikoryzowe (borowik, podgrzybek, koźlarz, maślak, kurka, rydz) oraz kania,
  - `W_frost`: gatunki odporne na przymrozki (opieńka, gąska), z łagodniejszą karą za przymrozek.
- **IG** (0–100): liczony **w aplikacji** z H i W.
- **Maska prawna** ma pierwszeństwo przed wszystkim: komórka zakazana jest zawsze szara, niezależnie od IG.

### 1.1 Decyzja architektoniczna (ADR-001)

**Kontekst.** Potencjał lasu zależy od drzewostanu, który zmienia się powoli. Pogoda zmienia się codziennie, ale jest gładka przestrzennie (siatka ok. 0,1°, czyli ok. 7 × 11 km). Komórek lasu H3 jest kilkadziesiąt tysięcy, a punktów pogodowych kilkaset.

**Decyzja.**
1. H per komórka i gatunek liczymy rzadko w pipeline i publikujemy jako plik statyczny (etap 1).
2. Codziennie liczymy tylko W per punkt siatki pogodowej 0,1° i dzień, w dwóch wariantach: `W_myc` i `W_frost` (etap 2).
3. Każda komórka ma przypisany jeden punkt pogodowy (`cells_meta.json`).
4. Aplikacja łączy: `IG = W · (0,4 + 0,6·H)`.

**Skutek.** Codzienny plik `latest.json` ma kilkadziesiąt kB zamiast megabajtów, a GitHub Actions wystarcza bez własnego serwera. Koszt: H i W nie mogą wchodzić ze sobą w interakcje inne niż powyższy wzór (np. „wilgotne siedliska mniej wrażliwe na suszę” wymagałoby zmiany kontraktu).

---

## 2. Gatunki grzybów, drzewa, wiek i siedlisko

### 2.1 Tabela z researchu (sekcja 1.3, przepisana wiernie)

| Gatunek | Drzewa żywicielskie / siedlisko | Wiek drzewostanu | Typowe miesiące w Polsce |
|---|---|---|---|
| Borowik szlachetny (*Boletus edulis*) | wiele gatunków iglastych i liściastych (sosna, świerk, buk, dąb); unika gleb wapiennych | wg LP Szczecinek woli drzewostany młodsze | VI–XI, szczyt VIII–IX |
| Podgrzybek brunatny (*Imleria badia*) | sosna, świerk; lasy iglaste i mieszane, często mszyste runo | starsze, dojrzewające i dojrzałe drzewostany (LP) | VI–XI, szczyt IX–X |
| Koźlarze (*Leccinum* spp.) | mikoryza z brzozą; także topola, osika, grab | skraje lasów, młodsze brzeziny | VI–X |
| Maślak zwyczajny (*Suillus luteus*) | sosna | młode sośniny (LP) | V–XI |
| Maślak żółty (*Suillus grevillei*) | wyłącznie modrzew | — | VI–X (źródła wtórne) |
| Kurka (*Cantharellus cibarius*) | sosna, świerk, także dąb i grab; mech lub iglasta ściółka | wysokie bory | VI–X |
| Rydz (*Lactarius deliciosus*) | sosna, gleby piaszczyste; mleczaj świerkowy – świerk | często młodsze sośniny | VIII–XI (źródła wtórne) |
| Kania (*Macrolepiota procera*) | polany, prześwietlone i trawiaste miejsca; unika wilgotnych i zakwaszonych gleb (LP) | luki i skraje | VII–X |
| Opieńki (*Armillaria* spp.) | pniaki, martwe i osłabione drzewa (saprotrof/pasożyt) | zręby, drzewostany po szkodach | IX–XI, szczyt X |
| Gąska zielonka (*Tricholoma equestre*) | bory sosnowe na piaskach | — | IX–XI (Encyklopedia Leśna) |
| Gąska niekształtna (*T. portentosum*) | bory iglaste, gleby kwaśne i piaszczyste, sosna i świerk | — | IX–XI |

Kierunki z researchu (sekcja 1.3, „Wniosek dla modelu”): borowik = f(So/Św/Bk/Db, wiek 30–80 lat), podgrzybek = f(So/Św, wiek > 50 lat), maślak = f(So, wiek 5–25 lat), koźlarz = f(udział Brz), maślak żółty = f(udział Md). Źródła LP podają kierunek (młodsze/starsze), nie liczby. Liczy się też zwarcie i zasobność drzewostanu (hiszpańskie optimum pola przekroju ok. 40 m²/ha dla borowika); na razie poza modelem.

### 2.2 Gatunki w aplikacji (9 kluczy)

| Klucz (`species_id`) | Nazwa w UI | Obejmuje | Wariant W |
|---|---|---|---|
| `borowik` | Borowik | *Boletus edulis* | `W_myc` |
| `podgrzybek` | Podgrzybek | *Imleria badia* | `W_myc` |
| `kozlarz` | Koźlarz | *Leccinum* spp. | `W_myc` |
| `maslak` | Maślak | *Suillus luteus* + *S. grevillei* | `W_myc` |
| `kurka` | Kurka | *Cantharellus cibarius* | `W_myc` |
| `rydz` | Rydz | *Lactarius deliciosus* (+ mleczaj świerkowy) | `W_myc` |
| `kania` | Kania | *Macrolepiota procera* | `W_myc` [P] |
| `opienka` | Opieńka | *Armillaria* spp. | `W_frost` [R] |
| `gaska` | Gąska | *T. equestre* + *T. portentosum* | `W_frost` [R] |

Kania to saprotrof, nie grzyb mikoryzowy. Research nie mówi, jak ją traktować przy przymrozku, więc na start dostaje `W_myc` [P].

### 2.3 Informacje bezpieczeństwa (z researchu, nie są oceną jadalności)

Aplikacja **nigdy nie ocenia jadalności** i nie rozpoznaje grzybów. Research zawiera jednak dwa ostrzeżenia toksykologiczne:
- gąska zielonka: „jadalność sporna, powiązana z rabdomiolizą po wielokrotnym spożyciu dużych ilości” (NEJM, Bedry i in. 2001; Klimaszyk i Rzymski, Toxins 2018),
- opieńki: jadalne warunkowo, wymagają obgotowania.

**Do decyzji w etapie 3:** czy pokazywać te ostrzeżenia na karcie gatunku. Jeśli tak, to tylko jako ostrzeżenie z odesłaniem do grzyboznawcy, nigdy jako „jadalny/niejadalny”. Research proponuje też listę „nie zbieraj” z gatunków chronionych (Dz.U. 2014 poz. 1408), na później.

---

## 3. Potencjał siedliskowy H ∈ [0, 1]

### 3.1 Wzór

Dla każdego wydzielenia BDL `e` i gatunku grzyba `g`:

```
H_g(e) = suit_tree_g(e) · suit_age_g(wiek(e)) · suit_hab_g(siedlisko(e))
```

- `suit_tree_g(e) = u · tree_g(gatunek_panujący) + (1 − u) · tree_g(inne)`, gdzie `u` to udział gatunku panującego (`part_cd` w BDL, w dziesiątkach) [P]. BDL WFS nie podaje domieszek, więc reszta drzewostanu liczy się jako „inne”. Research mówi o „przydatności(gatunek panujący, domieszki)” bez wzoru.
- Do H wchodzą tylko wydzielenia z `area_type = D-STAN` (drzewostan). Zręby, bagna, drogi, łąki itd. nie są lasem w sensie modelu.
- `suit_age_g(a)`: funkcja odcinkowo-liniowa przez węzły z tabeli 3.3 (poza skrajnymi węzłami wartość stała).
- `suit_hab_g(s)`: wartość z tabeli 3.4; siedlisko spoza tabeli → `hab_default`.
- **Uprawa leśna** (młodnik do ok. 4 m): `H_g = 0` dla wszystkich gatunków [R]; i tak obowiązuje stały zakaz wstępu. BDL WFS nie ma wysokości ani opisu „uprawa”, więc rozpoznajemy ją po wieku gatunku panującego: `spec_age ≤ crop_age_max` (10 lat) [P].

Agregacja do komórki H3 (rozdzielczość 8, ok. 0,7 km²) [P]:

```
H_g(komórka) = Σ_e pow(e ∩ komórka, bez obszarów zakazanych) · H_g(e) / Σ_e pow(e ∩ komórka, bez obszarów zakazanych)
H_max(komórka) = max_g H_g(komórka)
```

**Decyzja [P]:** H liczymy **per wydzielenie, a potem uśredniamy** w komórce. Nie liczymy H ze średniego wieku komórki, bo średnia z 20 i 100 lat (60 lat) dałaby fałszywie wysokie H. Średni wiek, udziały gatunków i dominujące siedlisko liczymy osobno, tylko do opisu na karcie lasu. Alternatywa do kalibracji: zamiast średniej użyć kwantyla 75% (grzybiarz i tak idzie do najlepszego wydzielenia w komórce).

Interpretacja zapisu z researchu: „H_gat = max po gatunkach grzybów z [...]” rozumiemy jako: iloczyn liczony **osobno dla każdego gatunku grzyba** (H_g), a **H_max = max po gatunkach**.

### 3.2 Przydatność drzew `tree_g` (gatunek drzewa → 0–1)

Kody drzew wg skrótów LP. W BDL pole `species_cd` ma kody wielkimi literami, czasem z podgatunkiem po kropce (`DB.B`, `BRZ.O`); mapujemy po prefiksie (`tree_code_map` w configu). Opis pól: `docs/DATA_SOURCES.md`.

| Drzewo | borowik | podgrzybek | koźlarz | maślak | kurka | rydz | kania | opieńka | gąska |
|---|---|---|---|---|---|---|---|---|---|
| So (sosna) | **1,0 [R]** | 1,0 | 0,2 | 1,0 | 1,0 | 1,0 | 0,7 | 0,7 | 1,0 |
| Św (świerk) | **1,0 [R]** | 1,0 | 0,2 | 0,1 | 1,0 | 0,8 | 0,6 | 1,0 | 0,7 |
| Jd (jodła) | 0,8 | 0,7 | 0,1 | 0,1 | 0,7 | 0,3 | 0,6 | 0,8 | 0,3 |
| Md (modrzew) | 0,5 | 0,5 | 0,1 | 1,0 | 0,5 | 0,2 | 0,6 | 0,7 | 0,2 |
| Bk (buk) | **1,0 [R]** | 0,4 | 0,2 | 0,1 | 0,8 | 0,1 | 0,6 | 1,0 | 0,1 |
| Db (dąb) | **1,0 [R]** | 0,4 | 0,3 | 0,1 | 0,8 | 0,1 | 0,8 | 1,0 | 0,1 |
| Brz (brzoza) | **0,6 [R]** | 0,3 | 1,0 | 0,1 | 0,5 | 0,1 | 0,8 | 0,8 | 0,1 |
| Gb (grab) | 0,6 | 0,2 | 0,6 | 0,1 | 0,6 | 0,1 | 0,6 | 0,8 | 0,1 |
| Os (osika) | 0,4 | 0,2 | 0,8 | 0,1 | 0,3 | 0,1 | 0,6 | 0,8 | 0,1 |
| Tp (topola) | 0,3 | 0,1 | 0,7 | 0,1 | 0,2 | 0,1 | 0,6 | 0,8 | 0,1 |
| Ol (olsza) | **0,1 [R]** | 0,1 | 0,2 | 0,1 | 0,1 | 0,1 | 0,3 | 0,6 | 0,1 |
| inne | 0,3 | 0,2 | 0,2 | 0,1 | 0,3 | 0,1 | 0,6 | 0,7 | 0,1 |

Wartości pogrubione z [R] pochodzą z przykładu dla borowika (sekcja 2.4.A). Pozostałe to **[P]**: kierunek z tabeli 2.1, liczby do kalibracji. Kania i opieńka mają słabą zależność od drzewa, bo research wiąże je z polanami/skrajami (kania) i z pniakami/martwym drewnem (opieńka). Tych cech nie ma w BDL.

### 3.3 Przydatność wieku `suit_age_g` (węzły: wiek w latach → wartość)

Interpolacja liniowa między węzłami, poza skrajnymi węzłami wartość stała.

| Gatunek | Węzły (wiek: wartość) | Źródło |
|---|---|---|
| borowik | 10: 0,3 · 15: 0,6 · 30: 1,0 · 80: 1,0 · 120: 0,7 | 15–30 = 0,6; 30–80 = 1,0; > 120 = 0,7 **[R]**; przejścia 15→30, 80→120 i wiek < 15 **[P]** |
| podgrzybek | 20: 0,3 · 50: 1,0 | „> 50 lat” [R], liczby przejścia [P] |
| koźlarz | 5: 0,5 · 10: 1,0 · 50: 1,0 · 80: 0,6 | „młodsze brzeziny” [R], liczby [P] |
| maślak | 5: 1,0 · 25: 1,0 · 40: 0,6 · 60: 0,3 | „5–25 lat” [R], spadek po 25 [P] |
| kurka | 20: 0,4 · 40: 1,0 | „wysokie bory” [R], liczby [P] |
| rydz | 10: 1,0 · 40: 1,0 · 60: 0,5 | „młodsze sośniny” [R], liczby [P] |
| kania | 0: 1,0 | brak zależności od wieku [P] (luki i skraje to nie wiek) |
| opieńka | 20: 0,4 · 60: 1,0 | „drzewostany po szkodach, zręby” [R], przybliżone wiekiem [P] |
| gąska | 15: 0,4 · 30: 1,0 | brak danych w research, liczby [P] |

Uprawa leśna (wiek ≤ `crop_age_max`, domyślnie 10 lat [P]) → H = 0 dla wszystkich gatunków, niezależnie od tabeli [R: „uprawa < 4 m = 0”]. Próg wieku jako zamiennik wysokości 4 m sprawdzimy w etapie 1 (może BDL ma wysokość albo opis „uprawa”).

### 3.4 Przydatność siedliska `suit_hab_g` (typ siedliskowy lasu → 0–1)

Kody typów siedliskowych lasów nizinnych: Bs (bór suchy), Bśw (bór świeży), Bw (bór wilgotny), Bb (bór bagienny), BMśw (bór mieszany świeży), BMw (bór mieszany wilgotny), BMb (bór mieszany bagienny), LMśw (las mieszany świeży), LMw (las mieszany wilgotny), LMb (las mieszany bagienny), Lśw (las świeży), Lw (las wilgotny), Ol (ols), OlJ (ols jesionowy), Lł (las łęgowy).

| Siedlisko | borowik | podgrzybek | koźlarz | maślak | kurka | rydz | kania | opieńka | gąska |
|---|---|---|---|---|---|---|---|---|---|
| Bs | 0,6 | 0,7 | 0,4 | 1,0 | 0,6 | 1,0 | 0,6 | 0,3 | 1,0 |
| Bśw | **1,0 [R]** | 1,0 | 0,8 | 1,0 | 1,0 | 1,0 | 0,8 | 0,6 | 1,0 |
| Bw | 0,7 | 0,9 | 1,0 | 0,7 | 0,8 | 0,6 | 0,4 | 0,6 | 0,5 |
| Bb | **0,2 [R]** | 0,3 | 0,6 | 0,2 | 0,2 | 0,1 | 0,1 | 0,3 | 0,1 |
| BMśw | **1,0 [R]** | 1,0 | 0,8 | 0,8 | 1,0 | 0,7 | 1,0 | 0,8 | 0,6 |
| BMw | 0,7 | 0,9 | 1,0 | 0,6 | 0,8 | 0,5 | 0,4 | 0,8 | 0,4 |
| BMb | 0,2 | 0,3 | 0,6 | 0,2 | 0,2 | 0,1 | 0,1 | 0,4 | 0,1 |
| LMśw | **1,0 [R]** | 0,7 | 0,8 | 0,4 | 0,8 | 0,3 | 1,0 | 1,0 | 0,3 |
| LMw | 0,6 | 0,5 | 1,0 | 0,3 | 0,6 | 0,2 | 0,4 | 1,0 | 0,2 |
| LMb | 0,2 | 0,2 | 0,6 | 0,1 | 0,2 | 0,1 | 0,1 | 0,5 | 0,1 |
| Lśw | 0,7 | 0,4 | 0,6 | 0,2 | 0,6 | 0,2 | 1,0 | 1,0 | 0,2 |
| Lw | 0,4 | 0,3 | 0,8 | 0,1 | 0,4 | 0,1 | 0,4 | 0,9 | 0,1 |
| Ol, OlJ | **0,2 [R]** | 0,1 | 0,5 | 0,1 | 0,1 | 0,1 | 0,1 | 0,6 | 0,1 |
| Lł | 0,2 | 0,1 | 0,5 | 0,1 | 0,1 | 0,1 | 0,2 | 0,7 | 0,1 |
| inne / brak (`hab_default`) | 0,5 | 0,5 | 0,5 | 0,5 | 0,5 | 0,5 | 0,5 | 0,5 | 0,5 |

[R] tylko dla borowika (Bśw/BMśw/LMśw = 1,0; Bb/Ol = 0,2). Reszta [P]: borowe i piaszczyste dla maślaka, rydza i gąski; wilgotne dla koźlarza; żyźniejsze, prześwietlone dla kani (unika wilgotnych i zakwaszonych gleb [R]); żyzne lasy dla opieńki. Siedliska górskie (np. BG, LMG, LG) dostają `hab_default` aż do rozszerzenia regionu poza niż.

---

### 3.5 Lasy poza Lasami Państwowymi (etap 1)

BDL WFS zawiera tylko lasy Lasów Państwowych. W łódzkim duża część lasów to lasy prywatne i gminne. Bierzemy je z OpenStreetMap (`landuse=forest`, `natural=wood`), odejmując wszystko, co jest w BDL [P]:

```
H_g(las spoza LP) = Σ_drzewa udział · tree_g(drzewo) · non_lp.age_factor · hab_default
```

- Mieszanka drzew z tagu OSM `leaf_type`: iglasty → sosna; liściasty → dąb 50% + brzoza 50%; mieszany → sosna 50%, dąb 25%, brzoza 25%; brak tagu → sosna 60%, dąb 20%, brzoza 20% (parametr `non_lp.leaf_type_trees`).
- Wiek nieznany: czynnik `non_lp.age_factor = 0,7`. Siedlisko nieznane: `hab_default = 0,5`. Taki las ma więc H ≤ 0,35, czyli nigdy nie wygrywa z dobrze opisanym lasem państwowym. To celowe: mniej wiemy, mniej obiecujemy.
- Pomijamy płaty mniejsze niż `non_lp.min_area_m2` (0,5 ha).
- Komórka dostaje flagę **„prywatny, może być zakaz”**, gdy co najmniej 50% jej lasu leży poza BDL [P]. To przybliżenie: las spoza LP może też być gminny albo należeć do innego zarządcy.

## 4. Składowa pogodowa W ∈ [0, 100]

Liczona dla każdego punktu siatki pogodowej (0,1°) i każdego dnia `d`. Okno danych: dni −30…+14 względem dnia uruchomienia. Wartości publikowane dla aplikacji: dni 0…+14.

Dane dzienne dla punktu: `P` (suma opadu, mm), `Tmean`, `Tmin` (°C), `ET0` (ewapotranspiracja FAO, mm), `SM` (wilgotność gleby 0–28 cm, m³/m³, średnia dobowa).

Konwencja indeksów [P]: `P_{d−i}` to opad dnia `d−i`. Składowe M i L patrzą wstecz od dnia `d−1` (deszcz dnia `d` nie wpływa jeszcze na grzyby dnia `d`). T patrzy na dni `d−4…d` (temperatura bieżąca ma znaczenie).

`sigmoid(x) = 1 / (1 + e^(−x))`

### 4.0 Dane pogodowe (etap 2, sprawdzone zapytaniami 2026-10-06)

- **Model główny: ECMWF IFS** (`models=ecmwf_ifs` w Open-Meteo Forecast API) dla wszystkich zmiennych: `precipitation_sum`, `temperature_2m_mean`, `temperature_2m_min`, `et0_fao_evapotranspiration` (dzienne) oraz `soil_moisture_0_to_7cm`, `soil_moisture_7_to_28cm` (godzinowe). Powód: IFS ma **te same warstwy gleby co ERA5-Land** (0–7 i 7–28 cm) i ten sam schemat powierzchni lądu (ECMWF), więc percentyl względem klimatologii ERA5-Land jest spójny. Domyślny model Open-Meteo ma warstwy 0–1, 1–3, 3–9, 9–27 cm i braki danych w ostatnich dniach prognozy, więc odpada.
- `past_days = 30`, `forecast_days = 15`: dni −30…+14, strefa czasowa Europe/Warsaw.
- Wilgotność 0–28 cm = średnia dobowa z `(7·SM₀₋₇ + 21·SM₇₋₂₈) / 28` (średnia ważona grubością warstw).
- Temperatura maksymalna nie jest pobierana, bo model jej nie używa (oszczędność wywołań).
- Braki w danych: opad → 0, pozostałe → wartość z poprzedniego dnia (liczba uzupełnień w logu).
- **Wywołania API** liczymy wzorem ze strony Open-Meteo: `max(1, max(v/10, dni/14 · v/10)) · lokalizacje`, gdzie v = zmienne × modele. Jedno dzienne uruchomienie dla 283 punktów to ok. **829 wywołań** (546 model główny + 283 przedział niepewności). Limit darmowy: 10 000 na dobę.

### 4.1 Wilgoć M ∈ [0, 1]

```
API_d      = Σ_{i=1..30} P_{d−i} · 0,9^i
Bilans14_d = Σ_{i=1..14} (P_{d−i} − ET0_{d−i})
SMpct_d    = percentyl SM_d względem klimatologii tego samego punktu i miesiąca kalendarzowego (0–1)
M          = 0,4 · sigmoid((API_d − 25) / 8) + 0,3 · sigmoid(Bilans14_d / 10) + 0,3 · SMpct_d
```

- Wagi 0,4/0,3/0,3, środek 25 i skala 8 dla API, skala 10 dla bilansu: [R].
- Okno bilansu `i = 1..14` (czyli bez dnia `d`): [P]. Research mówi „Σ z 14 dni”.
- Klimatologia SM [R, decyzja etapu 2]: ERA5-Land (`models=era5_land`, Archive API), lata **2016–2025**, tylko **IV–XI** (miesiące z S > 0), dla każdego punktu siatki. Przechowujemy kwantyle 0, 5, …, 100% dziennej wilgotności 0–28 cm per punkt i miesiąc (`data/climatology/sm_quantiles.json`); percentyl to interpolacja liniowa między kwantylami. Wymagane co najmniej 5 lat danych; bez klimatologii `SMpct = 0,5` (mediana) i M opiera się tylko na opadzie.
- Zgodność warstw: rozwiązana przez wybór ECMWF IFS w prognozie (4.0). Ryzyko szczątkowe: IFS (9 km) i ERA5-Land (ok. 9 km, inne wymuszenie) mogą mieć różny poziom średniej wilgotności. Do sprawdzenia: porównać 30 dni wstecz z IFS z ERA5-Land dla tych samych dni.
- Pobranie klimatologii kosztuje jednorazowo ok. **9 900 wywołań**, więc workflow `soil-climatology` rozkłada je na co najmniej 3 dni (≤ 4 500 na bieg, poniżej limitu godzinowego 5 000). Postęp: `data/climatology/progress.json`.

### 4.2 Wyzwalacz z opóźnieniem L ∈ [0, 1]

```
L = min(1, Σ_{k=1..Kmax} [P_{d−k} ≥ 10 mm] · min(1, P_{d−k} / 25) · K(k))
```

Jądro `K(k)` („gamma” ze szczytem ok. 10. dnia) to interpolacja liniowa między węzłami:

| k (dni po opadzie) | 1–3 | 5 | 8 | 10 | 14 | 21 | ≥ 28 |
|---|---|---|---|---|---|---|---|
| K(k) | 0 [P] | 0,3 [R] | 0,8 [R] | 1,0 [R] | 0,7 [R] | 0,2 [R] | 0 [P] |

(węzeł 3 → 0; między 3 a 5 liniowo; `Kmax = 28`.)

- Próg dziennego opadu 10 mm i nasycenie przy 25 mm: [R].
- Uproszczenie: kilka deszczowych dni z rzędu sumuje się (z ograniczeniem do 1). Research podaje też praktyczny wyzwalacz „≥ 20 mm w 1–3 dni lub ≥ 30–40 mm w 14 dni” (sekcja 2.2). Obecny wzór go nie odwzorowuje wprost: kilka dni po 8 mm nie daje żadnego wkładu do L, choć wchodzi do M przez API. Do sprawdzenia w backteście (etap 2).

### 4.3 Temperatura T ∈ [0, 1]

```
T5    = średnia z Tmean_{d−4..d}
P5    = średnia z P_{d−4..d}
T     = exp(−((T5 − T_opt) / T_width)²)          T_opt = 14, T_width = 5
jeśli T5 > 17,5 i P5 < 1 mm   → T = 0             (twardy zakaz suszy i upału)
jeśli Tmin < 0 °C w ≥ 2 z dni d−2..d → T = T · frost_mult
       frost_mult = 0,3 dla W_myc, 0,7 dla W_frost
```

- Wszystkie liczby: [R]. Okno `d−4..d` dla T5 i P5 oraz `d−2..d` dla „ostatnich 3 nocy”: [P].
- Ograniczenie do kalibracji: w tym wzorze kara za przymrozek znika po 2–3 dniach bez mrozu. W Bielefeld pierwszy silny mróz kończył sezon. Możliwe, że kara powinna działać dłużej (np. do końca sezonu dla `W_myc`).

### 4.4 Sezon S(miesiąc)

| Miesiąc | I–III | IV | V | VI | VII | VIII | IX | X | XI | XII |
|---|---|---|---|---|---|---|---|---|---|---|
| S | 0 [P] | 0,1 | 0,3 | 0,5 | 0,7 | 1,0 | 1,0 | 0,9 | 0,4 | 0 [P] |

Wartości IV–XI: [R] (analogia do współczynnika ČHMÚ). Ten sam S dla obu wariantów [P]. Opieńki i gąski mają szczyt w X–XI, więc to kandydat do osobnego S w kalibracji.

### 4.5 Wynik W

```
W_v = 100 · S · T_v · (0,5 · M + 0,5 · L)        v ∈ {myc, frost}
```

Wagi 0,5/0,5: [R]. `W_frost ≥ W_myc` zawsze, bo jedyną różnicą jest łagodniejszy `frost_mult`.

### 4.6 Niepewność dni +8…+14

Dla dni +8…+14 publikujemy przedział `w_low`, `w_high` [R] = min i max `W_myc` z trzech modeli: **ECMWF IFS** (główny), **GFS** (`gfs_seamless`) i **ECMWF AIFS** (`ecmwf_aifs025_single`) [decyzja etapu 2]. ICON odpada, bo prognozuje tylko 7 dni. Dla modelu dodatkowego podmieniamy opad, temperatury i ET₀ w dniach prognozy, a wilgotność gleby i historia (dni −30…−1) zostają z IFS. Ansamble byłyby dokładniejsze, ale kosztują wielokrotnie więcej wywołań. Dla dni 0…+7 `w_low = w_high = W_myc`. Przedział liczymy tylko dla `W_myc`.

### 4.7 Plik dzienny `latest.json` (kontrakt dla aplikacji)

```
{ generated_at, params_version, dates: [15 dni od dziś], uncertain_from_day: 8,
  models: {main, band}, sm_climatology_points, attribution,
  points: { "<lat>_<lon>": { w_myc: [15 × int], w_frost: [...], w_low: [...], w_high: [...],
                             rain: [15 × mm, 1 miejsce po przecinku], tmean: [15 × °C] } } }
```

Identyfikator punktu jak w `cells_meta.json` (np. `51.6_20.1`). W zaokrąglone do liczb całkowitych (połówki w górę). Kopia z datą: `daily/RRRR-MM-DD.json` (90 dni wstecz).

---

## 5. Indeks Grzybowy IG i kolory: kontrakt aplikacji

```
IG_g = W_{v(g)} · (0,4 + 0,6 · H_g)          v(g) z tabeli 2.2
IG_all = max_g IG_g                          (filtr „wszystkie gatunki”)
```

- Słaby las nie dostanie zielonego, ale bardzo dobry las przy złej pogodzie też nie [R].
- **IG_all [P]:** prompt etapu 3 mówi o „H_max”. Liczymy max po gatunkach z IG, nie z H, bo opieńka i gąska używają innego W. Bez przymrozku `W_frost = W_myc`, więc wtedy `IG_all = W · (0,4 + 0,6 · H_max)`, czyli dokładnie wariant z H_max.
- Zaokrąglenie [P]: IG zaokrąglamy do liczby całkowitej (połówki w górę), a kolor ustalamy z wartości zaokrąglonej, żeby wyświetlana liczba zawsze zgadzała się z kolorem.

| Kolor | Warunek | Znaczenie |
|---|---|---|
| szary | komórka zakazana (rozdział 6) | „brak wstępu / zakaz zbioru”, **zawsze**, niezależnie od IG |
| zielony | IG ≥ 60 | „jedź” |
| żółty | 35 ≤ IG ≤ 59 | „warto, jeśli blisko” |
| czerwony | IG < 35 | „nie warto” |

**„Kiedy jechać”:** dla dni +1…+14 aplikacja pokazuje dzień z maksymalnym IG i okno dni z IG ≥ 60. Dni +8…+14 oznaczone jako niepewne (przedział z `w_low`/`w_high`).

### 5.1 Przykłady kontraktowe (do testów pipeline i aplikacji)

Funkcja kontraktowa (Python: `pipeline/ig.py`, w aplikacji ta sama logika w TypeScript):

```
ig_g      = W[wariant(g)] · (0,4 + 0,6 · H_g)        wariant: opienka, gaska → frost; reszta → myc
IG        = zaokr(ig_g)                               zaokr(x) = floor(x + 0,5)  (= Math.round w JS)
IG_all    = IG gatunku z największym ig_g
kolor     = szary, jeśli komórka zakazana; inaczej zielony ≥ 60, żółty ≥ 35, czerwony < 35 (z wartości zaokrąglonej)
```

**Pełny zestaw przypadków testowych:** `docs/contract/ig_cases.json` (16 przypadków: progi kolorów, zaokrąglenia, wariant frost, filtr „wszystkie”, zakaz). Testy pipeline (`pipeline/tests/test_ig.py`) i aplikacji (etap 3) czytają ten sam plik. Przykłady:

| W | H | IG (dokładnie) | IG (zaokr.) | Kolor (bez zakazu) |
|---|---|---|---|---|
| 80 | 1,0 | 80,0 | 80 | zielony |
| 80 | 0,0 | 32,0 | 32 | czerwony |
| 100 | 0,5 | 70,0 | 70 | zielony |
| 50 | 0,5 | 35,0 | 35 | żółty |
| 75 | 0,6 | 57,0 | 57 | żółty |
| 85,7 | 0,5 | 59,99 | 60 | zielony |
| 90 | 1,0 | 90,0 | 90 | **szary, jeśli komórka zakazana** |

---

## 6. Maska prawna

Komórka jest **zakazana (szara)**, gdy > `ban_share_threshold` = 50% [R z promptu etapu 1] powierzchni lasu w komórce leży w masce:

| Warstwa | Źródło | Efekt |
|---|---|---|
| Parki narodowe | GDOŚ (WFS/SHP) | zakaz (szary) |
| Rezerwaty przyrody | GDOŚ (WFS/SHP) | zakaz (szary) |
| Tereny wojskowe | OSM: `landuse=military`, `military=*` | zakaz (szary) |
| Uprawy leśne do ok. 4 m | BDL: `spec_age ≤ crop_age_max` | zakaz (szary), H = 0 |
| Ostoje zwierząt, drzewostany nasienne, powierzchnie doświadczalne | BDL: `prot_categ` ∈ `OCH OSTOJ`, `OCH NAS`, `OCH BADAW` | zakaz (szary) |
| Rezerwaty wg BDL | BDL: `forest_fun = REZ` | zakaz (szary), zapasowo obok GDOŚ |
| Lasy poza Lasami Państwowymi | OSM minus BDL (rozdz. 3.5) | **flaga „prywatny, może być zakaz”**: ostrzeżenie, nie szary |
| Okresowe zakazy wstępu, zagrożenie pożarowe | WMS BDL | etap 6: ostrzeżenie, a jeśli da się sprawdzić automatycznie, to szary |

- **Otuliny** parków narodowych i rezerwatów **nie** wchodzą do maski. W plikach GDOŚ są w tej samej warstwie co park/rezerwat i różnią się tylko dopiskiem „ - otulina” w nazwie (23 z 46 obiektów w warstwie parków, 420 z 2146 w rezerwatach). Otulina to strefa buforowa, nie zakaz wstępu ani zbioru. Szczegóły odczytu: `data/manual/gdos/SOURCES.md`.
- Parki krajobrazowe i obszary Natura 2000 **nie** oznaczają zakazu zbioru grzybów i nie wchodzą do maski [P, do potwierdzenia w etapie 1].
- Stały zakaz obejmuje też drzewostany nasienne, ostoje zwierząt, źródliska i powierzchnie doświadczalne (art. 26 ustawy o lasach). BDL oznacza trzy z nich w `prot_categ` i te maskujemy. Innych kategorii ochronności (`OCH WOD` wodochronne, `OCH GLEB` glebochronne, `OCH MIAST` w obrębie miast, `OCH CENNE`) nie maskujemy, bo wstęp do nich jest dozwolony. Źródlisk BDL nie oznacza.
- Komórka liczy udział zakazu z sumy: powierzchnia wydzieleń z zakazem (cała) + część pozostałego lasu leżąca w parkach, rezerwatach i terenach wojskowych.
- GDOŚ zastrzega, że granice nie stanowią prawnego ustalenia; karta lasu powinna o tym wspominać.

---

## 7. Tabela parametrów (jedno miejsce, wartości startowe)

To jedyne źródło prawdy dla liczb w modelu. W etapie 1–2 trafi 1:1 do pliku konfiguracyjnego pipeline (np. `pipeline/config/model_params.yaml`), a każda zmiana podbija `params_version`.

| Parametr | Wartość | Źródło | Gdzie |
|---|---|---|---|
| `params_version` | `"0.2.0"` | — | wszędzie |
| `h3_resolution` | 8 | prompt | H |
| `crop_age_max` | 10 lat | [P] | H, maska |
| `ban_share_threshold` | 0,5 | prompt | maska |
| `hab_default` | 0,5 | [P] | H |
| `tree_g(*)` | tabela 3.2 | [R]/[P] | H |
| `age_nodes_g` | tabela 3.3 | [R]/[P] | H |
| `hab_g(*)` | tabela 3.4 | [R]/[P] | H |
| `h_cell_aggregation` | `"area_weighted_mean"` | [P] | H |
| `min_cell_forest_m2` | 10 000 (1 ha) | [P] | H |
| `tree_code_map` | prefiks kodu BDL → grupa drzew | DATA_SOURCES | H |
| `non_lp.leaf_type_trees` | rozdz. 3.5 | [P] | H |
| `non_lp.age_factor` | 0,7 | [P] | H |
| `non_lp.min_area_m2` | 5 000 | [P] | H |
| `bdl_ban_prot_categ` | `OCH OSTOJ`, `OCH NAS`, `OCH BADAW` | art. 26 | maska |
| `bdl_ban_forest_fun` | `REZ` | [P] | maska |
| `weather_grid_deg` | 0,1 | [R] | W |
| `api_window_days` | 30 | [R] | M |
| `api_decay` | 0,9 | [R] | M |
| `api_center_mm` | 25 | [R] | M |
| `api_scale_mm` | 8 | [R] | M |
| `balance_window_days` | 14 | [R] | M |
| `balance_scale_mm` | 10 | [R] | M |
| `sm_depth_cm` | 0–28 | [R] | M |
| `sm_climatology_years` | 10 | prompt | M |
| `m_weights` (API, bilans, SM) | 0,4 / 0,3 / 0,3 | [R] | M |
| `trigger_min_mm` | 10 | [R] | L |
| `trigger_sat_mm` | 25 | [R] | L |
| `lag_kernel_nodes` | 3: 0 · 5: 0,3 · 8: 0,8 · 10: 1,0 · 14: 0,7 · 21: 0,2 · 28: 0 | [R], węzły 3 i 28 [P] | L |
| `lag_max_days` | 28 | [P] | L |
| `t_window_days` | 5 | [R] | T |
| `t_opt` | 14 °C | [R] | T |
| `t_width` | 5 °C | [R] | T |
| `heat_dry_t5` | 17,5 °C | [R] | T |
| `heat_dry_p5_mm` | 1 mm/dobę | [R] | T |
| `frost_tmin` | 0 °C | [R] | T |
| `frost_nights_min` / `frost_nights_window` | 2 / 3 | [R] | T |
| `frost_mult_myc` | 0,3 | [R] | T |
| `frost_mult_frost` | 0,7 | [R] | T |
| `season_s` | I–III 0 · IV 0,1 · V 0,3 · VI 0,5 · VII 0,7 · VIII 1,0 · IX 1,0 · X 0,9 · XI 0,4 · XII 0 | [R], I–III i XII [P] | S |
| `w_weights` (M, L) | 0,5 / 0,5 | [R] | W |
| `ig_base` / `ig_h_weight` | 0,4 / 0,6 | [R] | IG |
| `color_green_min` | 60 | [R] | IG |
| `color_yellow_min` | 35 | [R] | IG |
| `forecast_days` | 14 | [R] | W |
| `uncertain_from_day` | +8 | [R] | W, UI |

---

## 8. Otwarte kwestie (do rozstrzygnięcia w kolejnych etapach)

1. ~~**Etap 1:** rzeczywiste nazwy warstw i pól BDL~~ Rozstrzygnięte: `docs/DATA_SOURCES.md`. WFS nie daje własności, wysokości ani domieszek.
2. **Etap 1:** czy parki krajobrazowe, Natura 2000 lub użytki ekologiczne mają lokalne zakazy zbioru (domyślnie nie maskujemy).
3. ~~**Etap 2:** uzgodnienie warstw gleby~~ Rozstrzygnięte: ECMWF IFS w prognozie (4.0). Zostaje sprawdzenie różnicy poziomów IFS vs ERA5-Land.
4. ~~**Etap 2:** `w_low`/`w_high`~~ Rozstrzygnięte: IFS + GFS + AIFS (4.6).
5. **Etap 2 (backtest):** czy L reaguje na serie umiarkowanych opadów (4.2) i czy kara za przymrozek nie znika za szybko (4.3).
6. **Etap 3:** czy pokazywać ostrzeżenia toksykologiczne (2.3).
7. **Etap 4 (kalibracja):** wszystkie wartości [P] w pierwszej kolejności; ewentualnie osobne S dla opieniek i gąsek.
8. **Wnioski z backtestu VIII–X 2025** (`docs/backtest/README.md`): (a) twardy zakaz upału daje 1–2-dniowe skoki IG do zera w środku szczytu, więc warto rozważyć łagodne przejście; (b) październik wychodzi bardzo nisko (T ≈ 0,3 przy 8 °C), co kłóci się z sezonem podgrzybka i opieńki, więc warto rozważyć szersze `t_width` jesienią; (c) reguła przymrozku nie została sprawdzona na danych (brak 2 mroźnych nocy w 3 dniach).
