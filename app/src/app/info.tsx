/** Sources, attributions, data dates, colour key and safety notes. */
import { Linking, ScrollView, StyleSheet, Text, View } from "react-native";

import { DATA_BASE_URL } from "../config";
import { useData } from "../data/DataProvider";
import { Button } from "../ui/Button";
import { dateTime } from "../ui/format";
import { Legend } from "../ui/Legend";
import { colors, font, space } from "../ui/theme";

const SOURCES = [
  { name: "Open-Meteo.com", text: "Prognoza pogody i dane archiwalne (ECMWF, NOAA GFS), licencja CC BY 4.0.", url: "https://open-meteo.com" },
  { name: "Bank Danych o Lasach, Lasy Państwowe", text: "Drzewostany: gatunek, wiek, siedlisko, stałe zakazy wstępu.", url: "https://www.bdl.lasy.gov.pl" },
  { name: "Generalna Dyrekcja Ochrony Środowiska", text: "Granice parków narodowych i rezerwatów (nie stanowią prawnego ustalenia granic).", url: "https://www.gov.pl/web/gdos" },
  { name: "© autorzy OpenStreetMap", text: "Lasy poza Lasami Państwowymi, tereny wojskowe i podkład mapy (ODbL). Podkład: OpenFreeMap.", url: "https://www.openstreetmap.org/copyright" },
];

export default function InfoScreen() {
  const { daily, dailyFetchedAt, refresh, refreshing, offline, cells } = useData();
  return (
    <ScrollView contentContainerStyle={styles.content}>
      <View style={styles.warning}>
        <Text style={styles.warningText}>
          Aplikacja nie rozpoznaje grzybów i nie ocenia ich jadalności. W razie wątpliwości skonsultuj się z grzyboznawcą.
        </Text>
      </View>

      <Text style={styles.h2}>Kolory na mapie</Text>
      <Legend />
      <Text style={styles.body}>
        Indeks Grzybowy (0–100) łączy pogodę z ostatnich tygodni i prognozę z potencjałem lasu (gatunek, wiek i
        siedlisko drzewostanu). Szare miejsca to zakaz wstępu lub zbioru: parki narodowe, rezerwaty, tereny
        wojskowe, uprawy leśne i stałe zakazy z Banku Danych o Lasach. Przerywana brązowa obwódka oznacza las
        poza Lasami Państwowymi, który może być prywatny.
      </Text>

      <Text style={styles.h2}>Model we wczesnej fazie</Text>
      <Text style={styles.body}>
        To pierwsza wersja modelu, oparta na badaniach z innych krajów. Będzie kalibrowana na prawdziwych
        wypadach. Test na sezonie 2025 pokazał, że indeks bywa za niski w październiku i spada do zera przy
        upałach. Traktuj kolory jako podpowiedź, nie pewnik.
      </Text>

      <Text style={styles.h2}>Aktualność danych</Text>
      <Text style={styles.body}>Prognoza policzona: {daily ? dateTime(daily.generated_at) : "–"}</Text>
      <Text style={styles.body}>Pobrana na telefon: {dailyFetchedAt ? dateTime(dailyFetchedAt) : "–"}</Text>
      <Text style={styles.body}>Komórek lasu: {cells.length.toLocaleString("pl-PL")} · wersja modelu {daily?.params_version ?? "–"}</Text>
      {offline ? <Text style={[styles.body, { color: colors.private }]}>Brak internetu: pokazuję ostatnie zapisane dane.</Text> : null}
      <Button label={refreshing ? "Odświeżam…" : "Odśwież dane teraz"} kind="secondary" onPress={() => refresh(true)} />

      <Text style={styles.h2}>Źródła danych</Text>
      {SOURCES.map((s) => (
        <View key={s.name} style={styles.source}>
          <Text style={styles.sourceName} onPress={() => Linking.openURL(s.url)}>{s.name}</Text>
          <Text style={styles.small}>{s.text}</Text>
        </View>
      ))}
      <Text style={styles.small}>Dane aplikacji: {DATA_BASE_URL}</Text>
      <Text style={styles.small}>Aplikacja prywatna, niekomercyjna.</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: space.l, gap: space.s, paddingBottom: 48 },
  warning: { backgroundColor: "#fff4d6", borderColor: "#c99500", borderWidth: 2, borderRadius: 10, padding: space.m },
  warningText: { fontSize: font.m, fontWeight: "700", color: colors.ink, lineHeight: 22 },
  h2: { fontSize: font.l, fontWeight: "800", color: colors.ink, marginTop: space.l },
  body: { fontSize: font.m, color: colors.ink, lineHeight: 22 },
  source: { gap: 2 },
  sourceName: { fontSize: font.m, fontWeight: "700", color: colors.accent, textDecorationLine: "underline" },
  small: { fontSize: font.s, color: colors.ink2 },
});
