import { StyleSheet, Text, View } from "react-native";

import { colors, font, space } from "./theme";

const ITEMS = [
  { color: colors.green, label: "≥ 60 jedź" },
  { color: colors.yellow, label: "35–59 warto, jeśli blisko" },
  { color: colors.red, label: "< 35 nie warto" },
  { color: colors.grey, label: "zakaz wstępu lub zbioru" },
];

export function Legend() {
  return (
    <View style={styles.row} accessibilityLabel="Legenda kolorów">
      {ITEMS.map((i) => (
        <View key={i.label} style={styles.item}>
          <View style={[styles.swatch, { backgroundColor: i.color }]} />
          <Text style={styles.text}>{i.label}</Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", flexWrap: "wrap", gap: space.s },
  item: { flexDirection: "row", alignItems: "center", gap: 6 },
  swatch: { width: 18, height: 14, borderRadius: 3, borderWidth: 1, borderColor: "rgba(0,0,0,0.25)" },
  text: { fontSize: font.s, color: colors.ink },
});
