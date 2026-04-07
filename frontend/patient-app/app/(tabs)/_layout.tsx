import { Tabs } from "expo-router";

export default function TabsLayout() {

  return (
    <Tabs>

      <Tabs.Screen
        name="vitals"
        options={{ title: "Vitals" }}
      />

      <Tabs.Screen
        name="history"
        options={{ title: "History" }}
      />

    </Tabs>
  );
}