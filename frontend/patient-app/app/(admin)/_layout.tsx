import { Tabs } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import LogoutButton from "../../src/components/LogoutButton";
import { Colors } from "../../src/constants/colors";

export default function AdminTabsLayout() {

  return (
    <Tabs
      screenOptions={{
        headerShown: true,
        headerRight: () => <LogoutButton />,
        tabBarActiveTintColor: Colors.primary,
      }}
    >

      <Tabs.Screen
        name="dashboard"
        options={{
          title: "Dashboard",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="stats-chart" color={color} size={size} />
          ),
        }}
      />

      <Tabs.Screen
        name="nurses"
        options={{
          title: "Nurses",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="medkit" color={color} size={size} />
          ),
        }}
      />

      <Tabs.Screen
        name="patients"
        options={{
          title: "Patients",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="people" color={color} size={size} />
          ),
        }}
      />

    </Tabs>
  );
}
