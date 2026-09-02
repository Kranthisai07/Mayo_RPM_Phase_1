import { Tabs } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import LogoutButton from "../../src/components/LogoutButton";
import { Colors } from "../../src/constants/colors";

export default function PatientTabsLayout() {

  return (
    <Tabs
      screenOptions={{
        headerShown: true,
        headerRight: () => <LogoutButton />,
        tabBarActiveTintColor: Colors.primary,
      }}
    >

      <Tabs.Screen
        name="vitals"
        options={{
          title: "Log Vitals",
          tabBarLabel: "Vitals",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="pulse" color={color} size={size} />
          ),
        }}
      />

      <Tabs.Screen
        name="history"
        options={{
          title: "My History",
          tabBarLabel: "History",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="time" color={color} size={size} />
          ),
        }}
      />

    </Tabs>
  );
}
