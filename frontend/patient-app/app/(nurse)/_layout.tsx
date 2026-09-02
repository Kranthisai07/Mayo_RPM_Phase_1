import { Tabs } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import LogoutButton from "../../src/components/LogoutButton";
import { Colors } from "../../src/constants/colors";

export default function NurseTabsLayout() {

  return (
    <Tabs
      screenOptions={{
        headerShown: true,
        headerRight: () => <LogoutButton />,
        tabBarActiveTintColor: Colors.primary,
      }}
    >

      <Tabs.Screen
        name="patients"
        options={{
          title: "My Patients",
          tabBarLabel: "Patients",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="people" color={color} size={size} />
          ),
        }}
      />

      <Tabs.Screen
        name="alerts"
        options={{
          title: "Alerts",
          tabBarLabel: "Alerts",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="warning" color={color} size={size} />
          ),
        }}
      />

      <Tabs.Screen
        name="patient/[id]"
        options={{
          href: null,
          headerShown: true,
          title: "Patient Detail",
        }}
      />

    </Tabs>
  );
}
