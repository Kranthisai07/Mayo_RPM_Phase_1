import { View, Text, StyleSheet } from "react-native";
import { Colors } from "../constants/colors";

type Tone = "success" | "danger" | "warning" | "info" | "muted";

type Props = {
  label: string;
  tone?: Tone;
};

const TONES: Record<Tone, { bg: string; fg: string }> = {
  success: { bg: Colors.successBg, fg: Colors.success },
  danger: { bg: Colors.dangerBg, fg: Colors.danger },
  warning: { bg: Colors.warningBg, fg: Colors.warning },
  info: { bg: Colors.infoBg, fg: Colors.info },
  muted: { bg: Colors.border, fg: Colors.muted },
};

export default function StatusBadge({ label, tone = "muted" }: Props) {
  const colors = TONES[tone];

  return (
    <View style={[styles.badge, { backgroundColor: colors.bg }]}>
      <Text style={[styles.text, { color: colors.fg }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
    alignSelf: "flex-start",
  },
  text: {
    fontSize: 12,
    fontWeight: "700",
  },
});
