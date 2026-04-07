import { View, Text, TextInput, Button, Alert, StyleSheet } from "react-native";
import { useState } from "react";
import API from "../../src/api/apiClient";

export default function Vitals() {

  const [weight, setWeight] = useState("");
  const [spo2, setSpo2] = useState("");

  const submitVitals = async () => {

    try {

      await API.post("/vitals/", {
        weight_value: parseFloat(weight),
        spo2_value: parseFloat(spo2),
      });

      Alert.alert("Vitals submitted");

      setWeight("");
      setSpo2("");

    } catch {

      Alert.alert("Submission failed");

    }
  };

  return (
    <View style={styles.container}>

      <Text style={styles.label}>Weight (kg)</Text>

      <TextInput
        style={styles.input}
        value={weight}
        onChangeText={setWeight}
        keyboardType="numeric"
      />

      <Text style={styles.label}>SpO₂ (%)</Text>

      <TextInput
        style={styles.input}
        value={spo2}
        onChangeText={setSpo2}
        keyboardType="numeric"
      />

      <Button title="Submit Vitals" onPress={submitVitals} />

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