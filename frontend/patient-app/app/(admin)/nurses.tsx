import { View, Text, StyleSheet, FlatList, RefreshControl } from "react-native";
import { useCallback, useEffect, useState } from "react";
import { listNurses, createNurse, deactivateNurse } from "../../src/features/admin/adminService";
import Card from "../../src/components/card";
import InputField from "../../src/components/InputField";
import PrimaryButton from "../../src/components/PrimaryButton";
import StatusBadge from "../../src/components/StatusBadge";
import { Colors } from "../../src/constants/colors";
import { notify, confirmAsync } from "../../src/utils/alert";

export default function AdminNurses() {

  const [nurses, setNurses] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await listNurses();
      setNurses(data);
    } catch (err) {
      console.log("List nurses error", err);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  const handleCreate = async () => {
    if (!name || !email || !password) {
      notify("Missing info", "Name, email, and password are required.");
      return;
    }

    setSaving(true);
    try {
      await createNurse(name, age, email, password);
      setName("");
      setAge("");
      setEmail("");
      setPassword("");
      setShowForm(false);
      await load();
    } catch (err: any) {
      notify("Create failed", err?.response?.data?.detail ?? "Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async (nurseId: number, nurseName: string) => {
    const confirmed = await confirmAsync(
      "Deactivate nurse",
      `Deactivate ${nurseName}?`,
      "Deactivate"
    );

    if (!confirmed) return;

    try {
      await deactivateNurse(nurseId);
      await load();
    } catch (err: any) {
      notify("Failed", err?.response?.data?.detail ?? "Please try again.");
    }
  };

  return (
    <FlatList
      style={styles.flex}
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      data={nurses}
      keyExtractor={(item) => `nurse-${item.id}`}
      ListHeaderComponent={() => (
        <>
          <PrimaryButton
            title={showForm ? "Cancel" : "+ Add Nurse"}
            variant="secondary"
            onPress={() => setShowForm(!showForm)}
            style={styles.toggleButton}
          />

          {showForm && (
            <Card>
              <InputField label="Name" value={name} onChangeText={setName} placeholder="Jane Nurse" />
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
                placeholder="nurse@example.com"
              />
              <InputField
                label="Password"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
                placeholder="At least 8 characters"
              />
              <PrimaryButton title="Create Nurse" onPress={handleCreate} loading={saving} />
            </Card>
          )}
        </>
      )}
      ListEmptyComponent={() => <Text style={styles.empty}>No nurses yet.</Text>}
      renderItem={({ item }) => (
        <Card>
          <View style={styles.rowTop}>
            <Text style={styles.name}>{item.name}</Text>
            <StatusBadge
              label={item.is_active ? "Active" : "Inactive"}
              tone={item.is_active ? "success" : "muted"}
            />
          </View>
          <Text style={styles.email}>{item.email}</Text>
          <StatusBadge
            label={item.is_available ? "Available" : "Unavailable"}
            tone={item.is_available ? "success" : "warning"}
          />
          {item.is_active && (
            <PrimaryButton
              title="Deactivate"
              variant="danger"
              onPress={() => handleDeactivate(item.id, item.name)}
              style={styles.deactivateButton}
            />
          )}
        </Card>
      )}
    />
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

  toggleButton: {
    marginBottom: 14,
  },

  rowTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 4,
  },

  name: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.text,
  },

  email: {
    fontSize: 13,
    color: Colors.muted,
    marginBottom: 8,
  },

  deactivateButton: {
    marginTop: 12,
  },

  empty: {
    textAlign: "center",
    color: Colors.muted,
    marginTop: 40,
  },

});
