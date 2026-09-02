import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from "react-native";
import { useState } from "react";
import { router } from "expo-router";
import { loginUser } from "../../src/auth/authService";
import { getHomeRouteForRole } from "../../src/auth/roleRoutes";
import InputField from "../../src/components/InputField";
import PrimaryButton from "../../src/components/PrimaryButton";
import Card from "../../src/components/card";
import { Colors } from "../../src/constants/colors";
import { notify } from "../../src/utils/alert";

export default function Login() {

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {

    if (!email || !password) {
      notify("Missing info", "Enter both email and password.");
      return;
    }

    setLoading(true);

    try {

      const data = await loginUser(email, password);

      router.replace(getHomeRouteForRole(data.role) as any);

    } catch (err: any) {

      notify(
        "Login failed",
        err?.response?.data?.detail ?? "Check your email and password and try again."
      );

    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">

        <Text style={styles.title}>Remote Patient Monitoring</Text>
        <Text style={styles.subtitle}>Sign in to continue</Text>

        <Card>
          <InputField
            label="Email"
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
            placeholder="you@example.com"
          />

          <InputField
            label="Password"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            placeholder="••••••••"
          />

          <PrimaryButton title="Log In" onPress={handleLogin} loading={loading} />

          <View style={{ height: 12 }} />

          <PrimaryButton
            title="Create a patient account"
            variant="secondary"
            onPress={() => router.push("/(auth)/register")}
          />
        </Card>

      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({

  flex: {
    flex: 1,
    backgroundColor: Colors.background,
  },

  container: {
    flexGrow: 1,
    justifyContent: "center",
    padding: 25,
  },

  title: {
    fontSize: 28,
    fontWeight: "700",
    color: Colors.text,
    textAlign: "center",
    marginBottom: 4,
  },

  subtitle: {
    fontSize: 15,
    color: Colors.muted,
    textAlign: "center",
    marginBottom: 24,
  },

});
