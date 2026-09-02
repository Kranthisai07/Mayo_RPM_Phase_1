import { View, Text, StyleSheet, ScrollView, RefreshControl } from "react-native";
import { useCallback, useEffect, useState } from "react";
import { getAdminDashboard } from "../../src/features/admin/adminService";
import Card from "../../src/components/card";
import { Colors } from "../../src/constants/colors";

const STAT_LABELS: Record<string, string> = {
  total_patients: "Total Patients",
  active_patients: "Active Patients",
  total_nurses: "Total Nurses",
  active_nurses: "Active Nurses",
  available_nurses: "Available Nurses",
  active_alerts: "Active Alerts",
};

export default function AdminDashboard() {

  const [stats, setStats] = useState<Record<string, number> | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await getAdminDashboard();
      setStats(data);
    } catch (err) {
      console.log("Admin dashboard load error", err);
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

  return (
    <ScrollView
      style={styles.flex}
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.grid}>
        {stats &&
          Object.entries(stats).map(([key, value]) => (
            <Card key={key} style={styles.statCard}>
              <Text style={styles.statValue}>{value}</Text>
              <Text style={styles.statLabel}>{STAT_LABELS[key] ?? key}</Text>
            </Card>
          ))}
      </View>
    </ScrollView>
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

  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
  },

  statCard: {
    width: "47%",
    alignItems: "center",
    paddingVertical: 22,
  },

  statValue: {
    fontSize: 28,
    fontWeight: "700",
    color: Colors.primary,
    marginBottom: 4,
  },

  statLabel: {
    fontSize: 13,
    color: Colors.muted,
    textAlign: "center",
  },

});
