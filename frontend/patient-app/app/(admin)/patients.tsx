import { View, Text, StyleSheet, FlatList, RefreshControl, Pressable } from "react-native";
import { useCallback, useEffect, useState } from "react";
import {
  listPatients,
  createPatient,
  deactivatePatient,
  listNurses,
  listAssignments,
  assignPatientToNurse,
} from "../../src/features/admin/adminService";
import Card from "../../src/components/card";
import InputField from "../../src/components/InputField";
import PrimaryButton from "../../src/components/PrimaryButton";
import StatusBadge from "../../src/components/StatusBadge";
import { Colors } from "../../src/constants/colors";
import { notify, confirmAsync } from "../../src/utils/alert";

export default function AdminPatients() {

  const [patients, setPatients] = useState<any[]>([]);
  const [nurses, setNurses] = useState<any[]>([]);
  const [assignedNurseByPatient, setAssignedNurseByPatient] = useState<Record<number, string>>({});
  const [refreshing, setRefreshing] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [saving, setSaving] = useState(false);
  const [reassigningId, setReassigningId] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      const [patientsData, nursesData, assignmentsData] = await Promise.all([
        listPatients(),
        listNurses(),
        listAssignments(),
      ]);
      setPatients(patientsData);
      setNurses(nursesData);

      const map: Record<number, string> = {};
      assignmentsData.forEach((assignment: any) => {
        if (assignment.is_active) {
          map[assignment.patient_id] = assignment.nurse_name ?? `Nurse #${assignment.nurse_id}`;
        }
      });
      setAssignedNurseByPatient(map);
    } catch (err) {
      console.log("List patients error", err);
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
      await createPatient(name, age, email, password);
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

  const handleDeactivate = async (patientId: number, patientName: string) => {
    const confirmed = await confirmAsync(
      "Deactivate patient",
      `Deactivate ${patientName}?`,
      "Deactivate"
    );

    if (!confirmed) return;

    try {
      await deactivatePatient(patientId);
      await load();
    } catch (err: any) {
      notify("Failed", err?.response?.data?.detail ?? "Please try again.");
    }
  };

  const handleAssign = async (patientId: number, nurseId: number) => {
    setReassigningId(patientId);
    try {
      await assignPatientToNurse(patientId, nurseId);
      await load();
    } catch (err: any) {
      notify("Assignment failed", err?.response?.data?.detail ?? "Please try again.");
    } finally {
      setReassigningId(null);
    }
  };

  return (
    <FlatList
      style={styles.flex}
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      data={patients}
      keyExtractor={(item) => `patient-${item.id}`}
      ListHeaderComponent={() => (
        <>
          <PrimaryButton
            title={showForm ? "Cancel" : "+ Add Patient"}
            variant="secondary"
            onPress={() => setShowForm(!showForm)}
            style={styles.toggleButton}
          />

          {showForm && (
            <Card>
              <InputField label="Name" value={name} onChangeText={setName} placeholder="John Patient" />
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
                placeholder="patient@example.com"
              />
              <InputField
                label="Password"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
                placeholder="At least 8 characters"
              />
              <PrimaryButton title="Create Patient" onPress={handleCreate} loading={saving} />
            </Card>
          )}
        </>
      )}
      ListEmptyComponent={() => <Text style={styles.empty}>No patients yet.</Text>}
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

          <Text style={styles.assignedLabel}>
            Assigned to: {assignedNurseByPatient[item.id] ?? "Unassigned"}
          </Text>

          {item.is_active && nurses.length > 0 && (
            <>
              <Text style={styles.reassignLabel}>Reassign:</Text>
              <View style={styles.nurseChips}>
                {nurses
                  .filter((nurse) => nurse.is_active)
                  .map((nurse) => (
                    <Pressable
                      key={nurse.id}
                      disabled={reassigningId === item.id}
                      onPress={() => handleAssign(item.id, nurse.id)}
                      style={styles.chip}
                    >
                      <Text style={styles.chipText}>{nurse.name}</Text>
                    </Pressable>
                  ))}
              </View>
            </>
          )}

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

  assignedLabel: {
    fontSize: 13,
    color: Colors.text,
    marginBottom: 8,
  },

  reassignLabel: {
    fontSize: 12,
    color: Colors.muted,
    marginBottom: 6,
  },

  nurseChips: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginBottom: 12,
  },

  chip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: Colors.primary,
  },

  chipText: {
    color: Colors.primary,
    fontSize: 12,
    fontWeight: "600",
  },

  deactivateButton: {
    marginTop: 4,
  },

  empty: {
    textAlign: "center",
    color: Colors.muted,
    marginTop: 40,
  },

});
