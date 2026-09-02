import { Pressable, Text, StyleSheet } from "react-native";
import { router } from "expo-router";
import { logoutUser } from "../auth/authService";
import { Colors } from "../constants/colors";
import { confirmAsync } from "../utils/alert";

export default function LogoutButton() {
  const handleLogout = async () => {
    const confirmed = await confirmAsync(
      "Log out",
      "Are you sure you want to log out?",
      "Log out"
    );

    if (!confirmed) return;

    await logoutUser();
    router.replace("/(auth)/login");
  };

  return (
    <Pressable onPress={handleLogout} style={styles.button} hitSlop={10}>
      <Text style={styles.text}>Log out</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    marginRight: 16,
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  text: {
    color: Colors.primary,
    fontWeight: "600",
    fontSize: 15,
  },
});
