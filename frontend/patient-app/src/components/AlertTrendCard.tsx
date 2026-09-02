import { StyleProp, StyleSheet, Text, View, ViewStyle } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import Card from "./card";
import StatusBadge from "./StatusBadge";
import { Colors } from "../constants/colors";

export type MetricType = "weight" | "spo2";

export type TrendAlert = {
  id: number | string;
  alert_type: string;
  severity: string;
  message: string;
  status: string;
  created_at?: string | null;
};

type Props = {
  alert: TrendAlert;
  currentValue?: number | null;
  previousValue?: number | null;
  metricType: MetricType;
  style?: StyleProp<ViewStyle>;
};

type MetricConfig = {
  label: string;
  accessibleLabel: string;
  formatValue: (value: number) => string;
  formatAmount: (value: number) => string;
  accessibleAmount: (value: number) => string;
};

const METRIC_CONFIG: Record<MetricType, MetricConfig> = {
  weight: {
    label: "Weight",
    accessibleLabel: "Weight",
    formatValue: (value) => `${value.toFixed(1)} kg`,
    formatAmount: (value) => `${value.toFixed(1)} kg`,
    accessibleAmount: (value) => `${value.toFixed(1)} kilograms`,
  },
  spo2: {
    label: "SpO₂",
    accessibleLabel: "Oxygen saturation",
    formatValue: (value) => `${Math.round(value)}%`,
    formatAmount: (value) => `${Math.round(value)}%`,
    accessibleAmount: (value) => `${Math.round(value)} percent`,
  },
};

type Direction = "increase" | "decrease" | "stable";

const DIRECTION_CONFIG: Record<
  Direction,
  { icon: keyof typeof Ionicons.glyphMap; word: string; color: string; softColor: string }
> = {
  increase: { icon: "arrow-up", word: "increased", color: Colors.success, softColor: Colors.successBg },
  decrease: { icon: "arrow-down", word: "decreased", color: Colors.danger, softColor: Colors.dangerBg },
  stable: { icon: "arrow-forward", word: "unchanged", color: Colors.muted, softColor: Colors.border },
};

const severityTone = (severity: string) =>
  severity === "critical" ? "danger" : severity === "high" ? "warning" : "muted";

const statusTone = (status: string) =>
  status === "active" ? "danger" : status === "acknowledged" ? "warning" : "success";

const formatDateTime = (value?: string | null) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString();
};

export default function AlertTrendCard({
  alert,
  currentValue = null,
  previousValue = null,
  metricType,
  style,
}: Props) {
  const metricConfig = METRIC_CONFIG[metricType];
  const hasData =
    !!metricConfig && currentValue != null && previousValue != null;

  const difference = hasData ? currentValue! - previousValue! : 0;
  const direction: Direction = difference > 0 ? "increase" : difference < 0 ? "decrease" : "stable";
  const dirConfig = DIRECTION_CONFIG[direction];

  const amount = Math.abs(difference);

  const title = hasData
    ? `${metricConfig.label} ${dirConfig.word} by ${metricConfig.formatAmount(amount)}`
    : alert.message;

  const accessibilityLabel = hasData
    ? `${metricConfig.accessibleLabel} ${dirConfig.word} by ${metricConfig.accessibleAmount(amount)}`
    : alert.message;

  return (
    <Card style={[styles.card, style]}>
      <View style={styles.topRow}>
        <View style={styles.badges}>
          <StatusBadge label={alert.severity} tone={severityTone(alert.severity)} />
          <StatusBadge label={alert.status} tone={statusTone(alert.status)} />
        </View>
        {alert.created_at ? (
          <Text style={styles.date} numberOfLines={1}>
            {formatDateTime(alert.created_at)}
          </Text>
        ) : null}
      </View>

      <View style={styles.mainRow}>
        <View
          style={[
            styles.iconWrap,
            { backgroundColor: hasData ? dirConfig.softColor : Colors.border },
          ]}
        >
          <Ionicons
            name={hasData ? dirConfig.icon : "help-outline"}
            size={16}
            color={hasData ? dirConfig.color : Colors.muted}
          />
        </View>
        <Text style={styles.title} accessibilityLabel={accessibilityLabel}>
          {title}
        </Text>
      </View>

      {hasData ? (
        <View style={styles.detailsRow}>
          <Text style={styles.detailText}>
            Previous: {metricConfig.formatValue(previousValue!)}
          </Text>
          <Text style={styles.detailText}>
            Current: {metricConfig.formatValue(currentValue!)}
          </Text>
        </View>
      ) : (
        <Text style={styles.unavailableText}>Change details unavailable</Text>
      )}
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.card,
  },

  topRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 10,
    gap: 8,
  },

  badges: {
    flexDirection: "row",
    gap: 8,
    flexShrink: 1,
  },

  date: {
    fontSize: 12,
    color: Colors.muted,
    flexShrink: 0,
  },

  mainRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginBottom: 8,
  },

  iconWrap: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
  },

  title: {
    flex: 1,
    fontSize: 15,
    fontWeight: "600",
    color: Colors.text,
    flexWrap: "wrap",
  },

  detailsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 16,
    paddingLeft: 38,
  },

  detailText: {
    fontSize: 13,
    color: Colors.muted,
  },

  unavailableText: {
    fontSize: 13,
    color: Colors.muted,
    fontStyle: "italic",
    paddingLeft: 38,
  },
});
