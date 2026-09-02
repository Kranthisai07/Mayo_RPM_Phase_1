import { View, Text, StyleSheet, ScrollView, KeyboardAvoidingView, Platform } from "react-native";
import { useState } from "react";
import { submitVitals } from "../../src/features/vitals/vitalsService";
import InputField from "../../src/components/InputField";
import PrimaryButton from "../../src/components/PrimaryButton";
import Card from "../../src/components/card";
import { Colors } from "../../src/constants/colors";
import { notify } from "../../src/utils/alert";

export default function Vitals() {

  const [weight, setWeight] = useState("");
  const [spo2, setSpo2] = useState("");
  const [loading, setLoading] = useState(false);

  const validate = () => {
    const weightNum = parseFloat(weight);
    const spo2Num = parseFloat(spo2);

    if (!weight || isNaN(weightNum) || weightNum <= 0 || weightNum >= 1000) {
      notify("Invalid weight", "Enter a weight between 0 and 1000 kg.");
      return false;
    }

    if (!spo2 || isNaN(spo2Num) || spo2Num < 70 || spo2Num > 100) {
      notify("Invalid SpO₂", "Enter an SpO₂ between 70 and 100%.");
      return false;
    }

    return true;
  };

  const handleSubmit = async () => {

    if (!validate()) return;

    setLoading(true);

    try {

      await submitVitals(weight, spo2);

      notify("Submitted", "Your vitals have been recorded.");

      setWeight("");
      setSpo2("");

    } catch (err: any) {

      notify(
        "Submission failed",
        err?.response?.data?.detail ?? "Please try again."
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

        <Card>
          <Text style={styles.cardTitle}>Today's Reading</Text>

          <InputField
            label="Weight (kg)"
            value={weight}
            onChangeText={setWeight}
            keyboardType="decimal-pad"
            placeholder="e.g. 72.5"
          />

          <InputField
            label="SpO₂ (%)"
            value={spo2}
            onChangeText={setSpo2}
            keyboardType="decimal-pad"
            placeholder="e.g. 97"
          />

          <PrimaryButton title="Submit Vitals" onPress={handleSubmit} loading={loading} />
        </Card>

        <View style={styles.note}>
          <Text style={styles.noteText}>
            Your care team is notified automatically if your weight changes by more than 2 kg
            since your last reading, or your SpO₂ drops below 92%.
          </Text>
        </View>

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
    padding: 20,
  },

  cardTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: Colors.text,
    marginBottom: 16,
  },

  note: {
    paddingHorizontal: 4,
  },

  noteText: {
    color: Colors.muted,
    fontSize: 13,
    lineHeight: 19,
  },

});
