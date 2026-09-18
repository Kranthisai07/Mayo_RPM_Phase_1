import { View, Text, StyleSheet, FlatList, RefreshControl, Platform } from "react-native";
import { Picker } from "@react-native-picker/picker";
import { useCallback, useEffect, useMemo, useState } from "react";
import { getNurseAlerts, acknowledgeAlert, resolveAlert, escalateAlert } from "../../src/features/alerts/alertService";
import { getAssignedPatients } from "../../src/features/nurse/nurseService";
import Card from "../../src/components/card";
import PrimaryButton from "../../src/components/PrimaryButton";
import StatusBadge from "../../src/components/StatusBadge";
import { Colors } from "../../src/constants/colors";
import { notify } from "../../src/utils/alert";

const severityTone = (severity: string) => (severity === "critical" ? "danger" : "warning");
const statusTone = (status: string) =>
  status === "active" ? "danger" : status === "acknowledged" ? "info" : "success";
const statusLabel = (status: string) =>
  status === "active" ? "Pending" : status === "acknowledged" ? "Received - To be reviewed" : status;

export default function NurseAlerts() {

  const [alerts, setAlerts] = useState<any[]>([]);
  const [patients, setPatients] = useState<{ id: number; name: string }[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [actingId, setActingId] = useState<number | null>(null);
  const [filterPatientId, setFilterPatientId] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      const [data, patientList] = await Promise.all([getNurseAlerts(), getAssignedPatients()]);
      setAlerts(data);
      setPatients(patientList);
    } catch (err) {
      console.log("Nurse alerts load error", err);
    }
  }, []);

  const patientNameById = useMemo(() => {
    const map = new Map<number, string>();
    patients.forEach((patient) => map.set(patient.id, patient.name));
    return map;
  }, [patients]);

  const visibleAlerts = useMemo(() => {
    if (filterPatientId == null) return alerts;
    return alerts.filter((alert) => alert.patient_id === filterPatientId);
  }, [alerts, filterPatientId]);

  useEffect(() => {
    load();
  }, [load]);

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  const handleAction = async (alertId: number, action: "acknowledge" | "resolve" | "escalate") => {
    setActingId(alertId);
    try {
      if (action === "acknowledge") {
        await acknowledgeAlert(alertId);
      } else if (action === "resolve") {
        await resolveAlert(alertId);
      } else {
        await escalateAlert(alertId);
      }
      await load();
    } catch (err: any) {
      notify("Action failed", err?.response?.data?.detail ?? "Please try again.");
    } finally {
      setActingId(null);
    }
  };

  return (
    <FlatList
      style={styles.flex}
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      data={visibleAlerts}
      keyExtractor={(item) => `alert-${item.id}`}
      ListHeaderComponent={() => (
        <Card style={styles.filterCard}>
          <Text style={styles.filterLabel}>Filter by patient</Text>
          <View style={styles.pickerWrapper}>
            <Picker
              selectedValue={filterPatientId}
              onValueChange={(value) => setFilterPatientId(value)}
              style={styles.picker}
            >
              <Picker.Item label="All patients" value={null} />
              {patients.map((patient) => (
                <Picker.Item key={`filter-${patient.id}`} label={patient.name} value={patient.id} />
              ))}
            </Picker>
          </View>
        </Card>
      )}
      ListEmptyComponent={() => (
        <Text style={styles.empty}>No alerts for your patients.</Text>
      )}
      renderItem={({ item }) => (
        <Card>
          <View style={styles.badges}>
            <StatusBadge label={item.severity} tone={severityTone(item.severity)} />
            <StatusBadge label={statusLabel(item.status)} tone={statusTone(item.status)} />
            {item.is_escalated && <StatusBadge label="Escalated" tone="danger" />}
            {item.alert_type === "ai_weight_anomaly" && <StatusBadge label="AI" tone="info" />}
          </View>
          <Text style={styles.patientName}>
            {patientNameById.get(item.patient_id) ?? `Patient #${item.patient_id}`}
          </Text>
          <Text style={styles.message}>{item.message}</Text>
          {item.status !== "resolved" && (
            <View style={styles.actions}>
              {item.status === "active" && (
                <PrimaryButton
                  title="Received"
                  variant="secondary"
                  loading={actingId === item.id}
                  onPress={() => handleAction(item.id, "acknowledge")}
                  style={styles.actionButton}
                />
              )}
              {!item.is_escalated && (
                <PrimaryButton
                  title="Escalate"
                  variant="secondary"
                  loading={actingId === item.id}
                  onPress={() => handleAction(item.id, "escalate")}
                  style={styles.actionButton}
                />
              )}
              <PrimaryButton
                title="Resolve"
                loading={actingId === item.id}
                onPress={() => handleAction(item.id, "resolve")}
                style={styles.actionButton}
              />
            </View>
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

  filterCard: {
    backgroundColor: Colors.card,
    marginBottom: 12,
  },

  filterLabel: {
    fontSize: 15,
    fontWeight: "600",
    color: Colors.text,
  },

  pickerWrapper: {
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 10,
    marginTop: 8,
    overflow: "hidden",
    ...Platform.select({
      android: { justifyContent: "center" },
    }),
  },

  picker: {
    color: Colors.text,
  },

  badges: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 8,
  },

  patientName: {
    fontSize: 14,
    fontWeight: "700",
    color: Colors.text,
    marginBottom: 4,
  },

  message: {
    fontSize: 14,
    color: Colors.text,
    marginBottom: 12,
  },

  actions: {
    flexDirection: "row",
    gap: 10,
  },

  actionButton: {
    flex: 1,
  },

  empty: {
    textAlign: "center",
    color: Colors.muted,
    marginTop: 40,
  },

});
