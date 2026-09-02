import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from "react-native";
import { useState } from "react";
import { router } from "expo-router";
import { registerUser } from "../../src/auth/authService";
import InputField from "../../src/components/InputField";
import PrimaryButton from "../../src/components/PrimaryButton";
import Card from "../../src/components/card";
import { Colors } from "../../src/constants/colors";
import { notify } from "../../src/utils/alert";

export default function Register() {

  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {

    if (!name || !email || !password) {
      notify("Missing info", "Name, email, and password are required.");
      return;
    }

    setLoading(true);

    try {

      await registerUser(name, age ? parseInt(age, 10) : null, email, password);

      notify("Registration successful", "You can now log in.");

      router.replace("/(auth)/login");

    } catch (err: any) {

      notify(
        "Registration failed",
        err?.response?.data?.detail ?? "Please check your details and try again."
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

        <Text style={styles.title}>Create Account</Text>
        <Text style={styles.subtitle}>Register as a patient</Text>

        <Card>
          <InputField label="Name" value={name} onChangeText={setName} placeholder="Jane Doe" />

          <InputField
            label="Age"
            value={age}
            onChangeText={setAge}
            keyboardType="numeric"
            placeholder="Optional"
          />

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
            placeholder="At least 8 characters"
          />

          <PrimaryButton title="Register" onPress={handleRegister} loading={loading} />

          <View style={{ height: 12 }} />

          <PrimaryButton
            title="Back to login"
            variant="secondary"
            onPress={() => router.replace("/(auth)/login")}
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
