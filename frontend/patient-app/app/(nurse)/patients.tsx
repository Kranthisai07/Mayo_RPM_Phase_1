import { View, Text, StyleSheet, FlatList, RefreshControl, Pressable, Switch } from "react-native";
import { useCallback, useEffect, useState } from "react";
import { router } from "expo-router";
import {
  getAssignedPatients,
  getAssignedPatientDetail,
  getNurseDashboard,
  updateNurseStatus,
} from "../../src/features/nurse/nurseService";
import Card from "../../src/components/card";
import PatientSearchDropdown from "../../src/components/PatientSearchDropdown";
import StatusBadge from "../../src/components/StatusBadge";
import { Colors } from "../../src/constants/colors";
import { notify } from "../../src/utils/alert";

type PatientRow = {
  id: number;
  name: string;
  email: string;
  weight: number | null;
  spo2: number | null;
  hasAlert: boolean;
  hasData: boolean;
};

export default function NursePatients() {

  const [patients, setPatients] = useState<PatientRow[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [isAvailable, setIsAvailable] = useState(false);
  const [statusLoading, setStatusLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      const dashboard = await getNurseDashboard();
      setIsAvailable(dashboard.is_available);

      const list = await getAssignedPatients();

      const details = await Promise.all(
        list.map((patient: any) =>
          getAssignedPatientDetail(patient.id).catch(() => null)
        )
      );

      const rows: PatientRow[] = list.map((patient: any, index: number) => {
        const detail = details[index];
        const latestVital = detail?.recent_vitals?.[0] ?? null;

        return {
          id: patient.id,
          name: patient.name,
          email: patient.email,
          weight: latestVital?.weight_value ?? null,
          spo2: latestVital?.spo2_value ?? null,
          hasAlert: (detail?.active_alerts?.length ?? 0) > 0,
          hasData: !!latestVital,
        };
      });

      setPatients(rows);

    } catch (err) {
      console.log("Nurse patients load error", err);
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

  const toggleAvailability = async (value: boolean) => {
    setStatusLoading(true);
    try {
      await updateNurseStatus(value);
      setIsAvailable(value);
    } catch (err: any) {
      notify("Update failed", err?.response?.data?.detail ?? "Please try again.");
    } finally {
      setStatusLoading(false);
    }
  };

  const handlePatientSelect = (patient: { id: number | string }) => {
    router.push(`/(nurse)/patient/${patient.id}` as any);
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
          <Card style={styles.availabilityCard}>
            <View style={styles.availabilityRow}>
              <Text style={styles.availabilityLabel}>Available for new patients</Text>
              <Switch
                value={isAvailable}
                onValueChange={toggleAvailability}
                disabled={statusLoading}
                trackColor={{ true: Colors.primary }}
              />
            </View>
          </Card>

          {patients.length > 0 && (
            <Card style={styles.jumpCard}>
              <PatientSearchDropdown
                patients={patients}
                selectedPatient={null}
                onSelect={handlePatientSelect}
                label="Jump to patient"
              />
            </Card>
          )}
        </>
      )}
      ListEmptyComponent={() => (
        <Text style={styles.empty}>No patients assigned yet.</Text>
      )}
      renderItem={({ item }) => (
        <Pressable onPress={() => router.push(`/(nurse)/patient/${item.id}` as any)}>
          <Card>
            <View style={styles.rowTop}>
              <Text style={styles.name}>{item.name}</Text>
              {item.hasData ? (
                <StatusBadge
                  label={item.hasAlert ? "Abnormal" : "Normal"}
                  tone={item.hasAlert ? "danger" : "success"}
                />
              ) : (
                <StatusBadge label="No data" tone="muted" />
              )}
            </View>
            <Text style={styles.email}>{item.email}</Text>
            {item.hasData && (
              <View style={styles.vitalsRow}>
                <Text style={styles.vitalText}>Weight: {item.weight} kg</Text>
                <Text style={styles.vitalText}>SpO₂: {item.spo2}%</Text>
              </View>
            )}
          </Card>
        </Pressable>
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

  availabilityCard: {
    backgroundColor: Colors.card,
  },

  jumpCard: {
    backgroundColor: Colors.card,
    width: "100%",
    maxWidth: "100%",
  },

  availabilityRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },

  availabilityLabel: {
    fontSize: 15,
    fontWeight: "600",
    color: Colors.text,
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

  vitalsRow: {
    flexDirection: "row",
    gap: 16,
  },

  vitalText: {
    fontSize: 14,
    color: Colors.text,
  },

  empty: {
    textAlign: "center",
    color: Colors.muted,
    marginTop: 40,
  },

});
