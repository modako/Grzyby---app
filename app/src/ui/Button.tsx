import { Pressable, StyleSheet, Text, ViewStyle } from "react-native";

import { colors, font, space, touch } from "./theme";

interface Props {
  label: string;
  onPress: () => void;
  kind?: "primary" | "secondary";
  style?: ViewStyle;
  accessibilityHint?: string;
}

export function Button({ label, onPress, kind = "primary", style, accessibilityHint }: Props) {
  const primary = kind === "primary";
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityHint={accessibilityHint}
      onPress={onPress}
      style={({ pressed }) => [
        styles.base,
        primary ? styles.primary : styles.secondary,
        pressed && { opacity: 0.75 },
        style,
      ]}
    >
      <Text style={[styles.label, { color: primary ? "#fff" : colors.ink }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    minHeight: touch,
    borderRadius: 10,
    paddingHorizontal: space.l,
    alignItems: "center",
    justifyContent: "center",
  },
  primary: { backgroundColor: colors.accent },
  secondary: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.line },
  label: { fontSize: font.m, fontWeight: "700" },
});
