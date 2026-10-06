/** Forest card: IG today, best day, green window, 14-day chart, species, stand, legal status. */
import { useLocalSearchParams } from "expo-router";
import { Linking, Platform, ScrollView, StyleSheet, Text, useWindowDimensions, View } from "react-native";

import { useData } from "../../data/DataProvider";
import { bestDay, cellSeries, greenWindows } from "../../model/forecast";
import { SPECIES, SPECIES_LABEL } from "../../model/params";
import type { Cell } from "../../model/types";
import { Button } from "../../ui/Button";
import { dayLabel, habitatText, mainTree, shortDate, treesText } from "../../ui/format";
import { IgChart } from "../../ui/IgChart";
import { colors, font, igColor, space } from "../../ui/theme";

function openNavigation(cell: Cell) {
  const [lng, lat] = cell.center;
  const url = Platform.select({
    ios: `maps:0,0?q=Las@${lat},${lng}`,
    default: `geo:${lat},${lng}?q=${lat},${lng}(Las)`,
  });
  Linking.openURL(url).catch(() =>
    Linking.openURL(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`),
  );
}

function legalStatus(cell: Cell): { label: string; color: string; detail: string } {
  if (cell.banned)
    return {
      label: "Zakaz wstępu lub zbioru",
      color: colors.grey,
      detail: `${cell.ban_reasons.join(", ") || "obszar chroniony"} (${Math.round(cell.ban_share * 100)}% lasu w komórce).`,
    };
  if (cell.private_maybe)
    return {
      label: "Może być las prywatny",
      color: colors.private,
      detail: `${Math.round(cell.non_lp_share * 100)}% lasu poza Lasami Państwowymi. Sprawdź tablice na miejscu: właściciel może zakazać wstępu.`,
    };
  return {
    label: "Wstęp dozwolony",
    color: colors.green,
    detail: cell.ban_reasons.length
      ? `Las państwowy. Częściowo: ${cell.ban_reasons.join(", ")} (${Math.round(cell.ban_share * 100)}% lasu) – omijaj te miejsca.`
      : "Las państwowy, bez stałych zakazów według BDL, GDOŚ i OSM. Okresowe zakazy (np. pożarowe) dojdą w etapie 6.",
  };
}

export default function CellScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { cellById, daily, species } = useData();
  const { width } = useWindowDimensions();
  const cell = id ? cellById.get(id) : undefined;

  if (!cell || !daily) {
    return (
      <View style={styles.center}>
        <Text style={styles.muted}>Nie znaleziono tej komórki lasu.</Text>
      </View>
    );
  }

  const series = cellSeries(cell, daily, species);
  const weather = daily.points[cell.pt];
  const status = legalStatus(cell);
  const ranked = [...SPECIES].sort((a, b) => cell.h[b] - cell.h[a]);
  const tree = mainTree(cell.trees);
  const reason = [tree, cell.age != null ? `${cell.age} lat` : null, habitatText(cell.habitat)]
    .filter(Boolean)
    .join(", ");

  return (
    <ScrollView contentContainerStyle={styles.content}>
      <View style={[styles.statusBox, { borderColor: status.color }]}>
        <Text style={[styles.statusLabel, { color: status.color }]}>{status.label}</Text>
        <Text style={styles.body}>{status.detail}</Text>
      </View>

      {series && weather ? (
        <>
          <View style={styles.todayRow}>
            <View style={[styles.igBadge, { backgroundColor: igColor[series[0].color] }]}>
              <Text style={styles.igValue}>{series[0].ig}</Text>
              <Text style={styles.igCaption}>IG dziś</Text>
            </View>
            <View style={{ flex: 1, gap: 6 }}>
              <Text style={styles.body}>
                {species ? SPECIES_LABEL[species] : `Najlepiej: ${SPECIES_LABEL[series[0].species]}`}
              </Text>
              {(() => {
                const b = bestDay(series);
                const s = series[b];
                return (
                  <Text style={styles.body}>
                    Najlepszy dzień: <Text style={styles.strong}>{dayLabel(daily.dates[b], b)}</Text> (IG {s.ig}
                    {s.high > s.low ? `, ${s.low}–${s.high}` : ""})
                  </Text>
                );
              })()}
              {(() => {
                const w = greenWindows(series);
                return (
                  <Text style={styles.body}>
                    {w.length
                      ? `Zielone okno: ${w.map(([a, b]) => (a === b ? shortDate(daily.dates[a]) : `${shortDate(daily.dates[a])}–${shortDate(daily.dates[b])}`)).join(", ")}`
                      : "Brak dni z IG ≥ 60 w ciągu 14 dni."}
                  </Text>
                );
              })()}
            </View>
          </View>
          <Text style={styles.h2}>Prognoza na 14 dni</Text>
          <IgChart width={width - space.l * 2} series={series} rain={weather.rain} dates={daily.dates}
            uncertainFrom={daily.uncertain_from_day} />
          <Text style={styles.note}>
            Punkty: IG na każdy dzień. Szare paski w dniach +8…+14: rozrzut między modelami pogody. Niebieskie słupki: opad.
          </Text>
        </>
      ) : (
        <Text style={styles.body}>Brak prognozy dla tej komórki.</Text>
      )}

      <Text style={styles.h2}>Gatunki według potencjału lasu</Text>
      {ranked.map((sp, i) => (
        <View key={sp} style={styles.speciesRow}>
          <Text style={styles.speciesName}>{SPECIES_LABEL[sp]}</Text>
          <View style={styles.track}>
            <View style={[styles.fill, { width: `${Math.round(cell.h[sp] * 100)}%` }]} />
          </View>
          <Text style={styles.speciesValue}>{cell.h[sp].toFixed(2).replace(".", ",")}</Text>
          {i < 3 && reason ? <Text style={styles.reason}>{reason} → {SPECIES_LABEL[sp].toLowerCase()}</Text> : null}
        </View>
      ))}

      <Text style={styles.h2}>Drzewostan</Text>
      <Text style={styles.body}>{treesText(cell.trees) ?? "Brak danych z Banku Danych o Lasach (las spoza Lasów Państwowych)."}</Text>
      {cell.age != null ? <Text style={styles.body}>Średni wiek: {cell.age} lat</Text> : null}
      {cell.habitat ? <Text style={styles.body}>Siedlisko: {habitatText(cell.habitat)}</Text> : null}
      <Text style={styles.body}>Las w komórce: {cell.forest_ha.toFixed(1).replace(".", ",")} ha</Text>

      <Text style={styles.h2}>Popularność</Text>
      <Text style={styles.muted}>Szacunek liczby grzybiarzy pojawi się w etapie 5.</Text>

      <Button label="Nawiguj" onPress={() => openNavigation(cell)} style={{ marginTop: space.l }}
        accessibilityHint="Otwiera mapy w telefonie z trasą do środka tego fragmentu lasu" />
      <Text style={styles.note}>Komórka {cell.id} · punkt pogodowy {cell.pt}</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: space.l, gap: space.s, paddingBottom: 48 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: space.xl },
  statusBox: { borderWidth: 2, borderRadius: 10, padding: space.m, gap: 4 },
  statusLabel: { fontSize: font.l, fontWeight: "800" },
  todayRow: { flexDirection: "row", gap: space.l, alignItems: "center", marginTop: space.m },
  igBadge: { width: 96, height: 96, borderRadius: 12, alignItems: "center", justifyContent: "center" },
  igValue: { fontSize: 40, fontWeight: "900", color: "#111" },
  igCaption: { fontSize: font.s, fontWeight: "700", color: "#111" },
  h2: { fontSize: font.l, fontWeight: "800", color: colors.ink, marginTop: space.l },
  body: { fontSize: font.m, color: colors.ink, lineHeight: 22 },
  strong: { fontWeight: "800" },
  muted: { fontSize: font.m, color: colors.ink2 },
  note: { fontSize: font.s, color: colors.ink2 },
  speciesRow: { flexDirection: "row", flexWrap: "wrap", alignItems: "center", gap: space.s },
  speciesName: { width: 96, fontSize: font.m, color: colors.ink },
  track: { flex: 1, height: 12, backgroundColor: colors.surface, borderRadius: 6, overflow: "hidden" },
  fill: { height: "100%", backgroundColor: colors.accent },
  speciesValue: { width: 40, textAlign: "right", fontSize: font.m, color: colors.ink, fontVariant: ["tabular-nums"] },
  reason: { width: "100%", paddingLeft: 96 + space.s, fontSize: font.s, color: colors.ink2 },
});
