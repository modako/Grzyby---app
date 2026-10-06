import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";

import { DataProvider } from "../data/DataProvider";
import { colors } from "../ui/theme";

export default function RootLayout() {
  return (
    <DataProvider>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colors.bg },
          headerTintColor: colors.ink,
          headerTitleStyle: { fontWeight: "700" },
          contentStyle: { backgroundColor: colors.bg },
        }}
      >
        <Stack.Screen name="index" options={{ headerShown: false }} />
        <Stack.Screen name="cell/[id]" options={{ title: "Karta lasu" }} />
        <Stack.Screen name="info" options={{ title: "Informacje" }} />
      </Stack>
    </DataProvider>
  );
}
