/** Main screen: forest cells coloured by IG, day slider, species filter, legend, my location. */
import {
  Camera,
  CameraRef,
  GeoJSONSource,
  Layer,
  Map,
  NativeUserLocation,
} from "@maplibre/maplibre-react-native";
import Slider from "@react-native-community/slider";
import * as Location from "expo-location";
import { router } from "expo-router";
import { useMemo, useRef, useState } from "react";
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { BASEMAP_STYLE_URL, REGION_BOUNDS } from "../config";
import { useData } from "../data/DataProvider";
import { igArray } from "../model/forecast";
import { IG_PARAMS, SPECIES, SPECIES_LABEL, Species } from "../model/params";
import { Button } from "../ui/Button";
import { dateTime, dayLabel } from "../ui/format";
import { Legend } from "../ui/Legend";
import { colors, font, space, touch } from "../ui/theme";

const DAYS = 15;

/**
 * Map data: one polygon per cell with the rounded IG for every day as d0..d14, so moving the
 * day slider only changes the style expression (no new GeoJSON, no re-tiling on the device).
 */
function useCellsGeoJSON(): GeoJSON.FeatureCollection | null {
  const { cells, daily, species } = useData();
  return useMemo(() => {
    if (!daily || !cells.length) return null;
    return {
      type: "FeatureCollection",
      features: cells.map((c) => {
        const igs = igArray(c, daily, species);
        const props: Record<string, number | string> = { id: c.id, b: c.banned ? 1 : 0, p: c.private_maybe ? 1 : 0 };
        igs.forEach((v, d) => (props[`d${d}`] = v));
        return {
          type: "Feature",
          id: c.id,
          geometry: { type: "Polygon", coordinates: [c.ring] },
          properties: props,
        } as GeoJSON.Feature;
      }),
    };
  }, [cells, daily, species]);
}

function fillColor(day: number): any {
  const key = `d${day}`;
  return [
    "case",
    ["==", ["get", "b"], 1], colors.grey, // banned: always grey (CLAUDE.md safety rule)
    ["<", ["get", key], 0], colors.noData,
    ["step", ["get", key], colors.red, IG_PARAMS.yellowMin, colors.yellow, IG_PARAMS.greenMin, colors.green],
  ];
}

export default function MapScreen() {
  const data = useData();
  const { status, daily, day, setDay, species, setSpecies, offline, refreshing } = data;
  const geojson = useCellsGeoJSON();
  const camera = useRef<CameraRef>(null);
  const [locating, setLocating] = useState(false);
  const [showUser, setShowUser] = useState(false);

  async function goToMyLocation() {
    setLocating(true);
    try {
      const perm = await Location.requestForegroundPermissionsAsync();
      if (perm.status !== "granted") {
        Alert.alert("Brak zgody na lokalizację", "Bez zgody nie pokażę Twojego położenia. Możesz ją włączyć w ustawieniach telefonu.");
        return;
      }
      setShowUser(true);
      const pos =
        (await Location.getLastKnownPositionAsync()) ??
        (await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced }));
      camera.current?.flyTo({ center: [pos.coords.longitude, pos.coords.latitude], zoom: 11, duration: 1200 });
    } catch {
      Alert.alert("Nie udało się ustalić lokalizacji", "Sprawdź, czy lokalizacja jest włączona w telefonie.");
    } finally {
      setLocating(false);
    }
  }

  if (status !== "ready" || !daily || !geojson) {
    return (
      <SafeAreaView style={styles.center}>
        {status === "error" ? (
          <>
            <Text style={styles.title}>Nie udało się pobrać danych</Text>
            <Text style={styles.muted}>Sprawdź internet. Przy pierwszym uruchomieniu aplikacja musi pobrać mapę lasów (ok. 9 MB).</Text>
            <Button label="Spróbuj ponownie" onPress={() => data.refresh(true)} />
          </>
        ) : (
          <>
            <ActivityIndicator size="large" color={colors.accent} />
            <Text style={styles.muted}>Pobieram mapę lasów i prognozę…</Text>
          </>
        )}
      </SafeAreaView>
    );
  }

  const uncertain = day >= IG_PARAMS.uncertainFromDay;
  const generated = dateTime(daily.generated_at);

  return (
    <SafeAreaView style={styles.root} edges={["top", "bottom"]}>
      <View style={styles.topBar}>
        <View style={{ flex: 1 }}>
          <Text style={styles.dataDate} accessibilityRole="text">
            Dane z dnia {generated}
            {offline ? " · bez internetu" : refreshing ? " · odświeżam…" : ""}
          </Text>
        </View>
        <Pressable accessibilityRole="button" accessibilityLabel="Informacje" onPress={() => router.push("/info")}
          style={styles.iconButton}>
          <Text style={styles.iconText}>i</Text>
        </Pressable>
      </View>

      <View style={styles.mapWrap}>
        <Map style={StyleSheet.absoluteFill} mapStyle={BASEMAP_STYLE_URL} compass={false} attributionPosition={{ bottom: 8, left: 8 }}>
          <Camera ref={camera} initialViewState={{ bounds: REGION_BOUNDS, padding: { top: 20, bottom: 20, left: 20, right: 20 } }} />
          <GeoJSONSource
            id="cells"
            data={geojson}
            onPress={(e) => {
              const id = e.nativeEvent.features?.[0]?.properties?.id;
              if (id) router.push(`/cell/${id}`);
            }}
          >
            <Layer id="cells-fill" type="fill"
              paint={{ "fill-color": fillColor(day), "fill-opacity": uncertain ? 0.5 : 0.75 }} />
            <Layer id="cells-line" type="line" minzoom={10}
              paint={{ "line-color": "rgba(0,0,0,0.25)", "line-width": 0.6 }} />
            <Layer id="cells-private" type="line" minzoom={10} filter={["==", ["get", "p"], 1]}
              paint={{ "line-color": colors.private, "line-width": 1.5, "line-dasharray": [2, 1.5] }} />
          </GeoJSONSource>
          {showUser ? <NativeUserLocation /> : null}
        </Map>
        <Pressable accessibilityRole="button" accessibilityLabel="Moja lokalizacja" onPress={goToMyLocation}
          style={[styles.fab, locating && { opacity: 0.6 }]}>
          <Text style={styles.fabText}>{locating ? "…" : "◎"}</Text>
          <Text style={styles.fabLabel}>Ja</Text>
        </Pressable>
        <View style={styles.sourcesTag} pointerEvents="none">
          <Text style={styles.sourcesText}>BDL LP · GDOŚ · Open-Meteo</Text>
        </View>
      </View>

      <View style={styles.panel}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
          {([null, ...SPECIES] as (Species | null)[]).map((sp) => {
            const active = sp === species;
            return (
              <Pressable key={sp ?? "all"} accessibilityRole="button" accessibilityState={{ selected: active }}
                onPress={() => setSpecies(sp)} style={[styles.chip, active && styles.chipActive]}>
                <Text style={[styles.chipText, active && styles.chipTextActive]}>
                  {sp ? SPECIES_LABEL[sp] : "Wszystkie"}
                </Text>
              </Pressable>
            );
          })}
        </ScrollView>

        <View style={styles.dayRow}>
          <Text style={styles.dayLabel}>{dayLabel(daily.dates[day], day)}</Text>
          <Text style={[styles.dayNote, uncertain && styles.uncertain]}>
            {uncertain ? "prognoza niepewna (dni +8…+14)" : day === 0 ? "" : `za ${day} dni`}
          </Text>
        </View>
        <Slider
          accessibilityLabel="Dzień prognozy"
          minimumValue={0}
          maximumValue={DAYS - 1}
          step={1}
          value={day}
          onValueChange={(v) => setDay(Math.round(v))}
          minimumTrackTintColor={colors.accent}
          maximumTrackTintColor={colors.line}
          thumbTintColor={colors.accent}
          style={{ height: 44 }}
        />
        <Legend />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  center: { flex: 1, alignItems: "center", justifyContent: "center", gap: space.l, padding: space.xl, backgroundColor: colors.bg },
  title: { fontSize: font.l, fontWeight: "700", color: colors.ink, textAlign: "center" },
  muted: { fontSize: font.m, color: colors.ink2, textAlign: "center" },
  topBar: { flexDirection: "row", alignItems: "center", paddingHorizontal: space.l, paddingVertical: space.s, gap: space.m },
  dataDate: { fontSize: font.s, color: colors.ink2 },
  iconButton: { width: touch, height: touch, borderRadius: touch / 2, borderWidth: 1, borderColor: colors.line,
    alignItems: "center", justifyContent: "center" },
  iconText: { fontSize: font.l, fontWeight: "800", color: colors.ink },
  mapWrap: { flex: 1 },
  fab: { position: "absolute", right: space.l, bottom: space.xl, width: 64, height: 64, borderRadius: 32,
    backgroundColor: colors.bg, alignItems: "center", justifyContent: "center", elevation: 4,
    shadowColor: "#000", shadowOpacity: 0.25, shadowRadius: 4, shadowOffset: { width: 0, height: 2 } },
  fabText: { fontSize: 26, color: colors.accent, lineHeight: 28 },
  fabLabel: { fontSize: 12, fontWeight: "700", color: colors.ink },
  sourcesTag: { position: "absolute", left: 8, top: 8, backgroundColor: "rgba(255,255,255,0.85)", borderRadius: 4,
    paddingHorizontal: 6, paddingVertical: 2 },
  sourcesText: { fontSize: 11, color: colors.ink2 },
  panel: { paddingHorizontal: space.l, paddingTop: space.s, paddingBottom: space.m, gap: space.s,
    borderTopWidth: 1, borderColor: colors.line, backgroundColor: colors.bg },
  chips: { gap: space.s, paddingVertical: 2 },
  chip: { minHeight: 44, paddingHorizontal: space.l, borderRadius: 22, borderWidth: 1, borderColor: colors.line,
    justifyContent: "center", backgroundColor: colors.surface },
  chipActive: { backgroundColor: colors.accent, borderColor: colors.accent },
  chipText: { fontSize: font.m, color: colors.ink, fontWeight: "600" },
  chipTextActive: { color: "#fff" },
  dayRow: { flexDirection: "row", alignItems: "baseline", justifyContent: "space-between" },
  dayLabel: { fontSize: font.xl, fontWeight: "800", color: colors.ink },
  dayNote: { fontSize: font.s, color: colors.ink2 },
  uncertain: { color: colors.private, fontWeight: "700" },
});
