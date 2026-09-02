import { View, Text, StyleSheet, FlatList, RefreshControl, Platform, useWindowDimensions } from "react-native";
import { useCallback, useEffect, useMemo, useState } from "react";
import { getMyHistory } from "../../src/features/vitals/vitalsService";
import { getMyAlerts } from "../../src/features/alerts/alertService";
import Card from "../../src/components/card";
import AlertTrendCard, { MetricType } from "../../src/components/AlertTrendCard";
import { Colors } from "../../src/constants/colors";

type VitalEntry = {
  id: number;
  weight_value: number;
  spo2_value: number;
  recorded_at: string | null;
};

type AlertEntry = {
  id: number;
  vital_id: number | null;
  alert_type: string;
  severity: string;
  message: string;
  status: string;
  created_at: string | null;
};

const WIDE_LAYOUT_BREAKPOINT = 720;

function getTrendValues(alert: AlertEntry, vitals: VitalEntry[]) {
  if (alert.vital_id == null) {
    return { currentValue: null, previousValue: null };
  }

  const currentIndex = vitals.findIndex((vital) => vital.id === alert.vital_id);

  if (currentIndex === -1) {
    return { currentValue: null, previousValue: null };
  }

  // `vitals` is ordered newest first, so the previous reading sits at the next index.
  const currentVital = vitals[currentIndex];
  const previousVital = vitals[currentIndex + 1] ?? null;
  const field = alert.alert_type === "weight" ? "weight_value" : "spo2_value";

  return {
    currentValue: currentVital[field] ?? null,
    previousValue: previousVital ? previousVital[field] ?? null : null,
  };
}

export default function History() {

  const [vitals, setVitals] = useState<VitalEntry[]>([]);
  const [alerts, setAlerts] = useState<AlertEntry[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const { width } = useWindowDimensions();
  const isWideLayout = Platform.OS === "web" && width >= WIDE_LAYOUT_BREAKPOINT;

  const load = useCallback(async () => {
    try {
      const [vitalsData, alertsData] = await Promise.all([getMyHistory(), getMyAlerts()]);
      setVitals(vitalsData);
      setAlerts(alertsData);
    } catch (err) {
      console.log("History load error", err);
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

  const alertTrends = useMemo(
    () =>
      alerts.map((alert) => ({
        alert,
        metricType: alert.alert_type as MetricType,
        ...getTrendValues(alert, vitals),
      })),
    [alerts, vitals]
  );

  return (
    <FlatList
      style={styles.flex}
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      data={vitals}
      keyExtractor={(item) => `vital-${item.id}`}
      ListHeaderComponent={() => (
        <>
          {alertTrends.length > 0 && (
            <View style={styles.alertsSection}>
              <Text style={styles.sectionTitle}>Alerts</Text>
              <View style={[styles.alertsGrid, isWideLayout && styles.alertsGridWide]}>
                {alertTrends.map(({ alert, metricType, currentValue, previousValue }) => (
                  <AlertTrendCard
                    key={alert.id}
                    alert={alert}
                    metricType={metricType}
                    currentValue={currentValue}
                    previousValue={previousValue}
                    style={isWideLayout ? styles.alertCardWide : styles.alertCardFull}
                  />
                ))}
              </View>
            </View>
          )}
          <Text style={styles.sectionTitle}>Past Readings</Text>
        </>
      )}
      ListEmptyComponent={() => (
        <Text style={styles.empty}>No vitals recorded yet.</Text>
      )}
      renderItem={({ item }) => (
        <Card style={styles.vitalCard}>
          <View style={styles.vitalRow}>
            <Text style={styles.vitalValue}>{item.weight_value} kg</Text>
            <Text style={styles.vitalValue}>{item.spo2_value}% SpO₂</Text>
          </View>
          <Text style={styles.vitalDate}>
            {item.recorded_at ? new Date(item.recorded_at).toLocaleString() : ""}
          </Text>
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

  sectionTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.text,
    marginBottom: 10,
  },

  alertsSection: {
    marginBottom: 20,
  },

  alertsGrid: {
    gap: 12,
  },

  alertsGridWide: {
    flexDirection: "row",
    flexWrap: "wrap",
  },

  alertCardFull: {
    marginBottom: 0,
    width: "100%",
  },

  alertCardWide: {
    marginBottom: 0,
    width: "48%",
  },

  vitalCard: {
    marginBottom: 10,
  },

  vitalRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 4,
  },

  vitalValue: {
    fontSize: 16,
    fontWeight: "600",
    color: Colors.text,
  },

  vitalDate: {
    fontSize: 12,
    color: Colors.muted,
  },

  empty: {
    textAlign: "center",
    color: Colors.muted,
    marginTop: 40,
  },

});
