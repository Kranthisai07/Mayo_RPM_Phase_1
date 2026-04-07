import { View, Text, TextInput, Button, Alert, StyleSheet } from "react-native";
import { useState } from "react";
import { router } from "expo-router";
import { loginUser } from "../../src/auth/authService";

export default function Login() {

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async () => {

    try {

      await loginUser(email, password);

      router.replace("/(tabs)/vitals");

    } catch {

      Alert.alert("Login failed");

    }
  };

  return (
    <View style={styles.container}>

      <Text style={styles.label}>Email</Text>

      <TextInput
        style={styles.input}
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
      />

      <Text style={styles.label}>Password</Text>

      <TextInput
        style={styles.input}
        secureTextEntry
        value={password}
        onChangeText={setPassword}
      />

      <Button title="Login" onPress={handleLogin} />

      <View style={{ height: 20 }} />

      <Button
        title="Register"
        onPress={() => router.push("/(auth)/register")}
      />

    </View>
  );
}

const styles = StyleSheet.create({

  container: {
    flex: 1,
    justifyContent: "center",
    padding: 25
  },

  label: {
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 5
  },

  input: {
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 6,
    padding: 10,
    marginBottom: 15
  }

});