import { Pressable, Text, StyleSheet, ActivityIndicator, StyleProp, ViewStyle } from "react-native";
import { Colors } from "../constants/colors";

type Variant = "primary" | "danger" | "secondary";

type Props = {
  title: string;
  onPress: () => void;
  variant?: Variant;
  loading?: boolean;
  disabled?: boolean;
  style?: StyleProp<ViewStyle>;
};

const VARIANT_BG: Record<Variant, string> = {
  primary: Colors.primary,
  danger: Colors.danger,
  secondary: Colors.card,
};

const VARIANT_TEXT: Record<Variant, string> = {
  primary: "#ffffff",
  danger: "#ffffff",
  secondary: Colors.primary,
};

export default function PrimaryButton({
  title,
  onPress,
  variant = "primary",
  loading = false,
  disabled = false,
  style,
}: Props) {
  const isDisabled = disabled || loading;

  return (
    <Pressable
      onPress={onPress}
      disabled={isDisabled}
      style={({ pressed }) => [
        styles.button,
        { backgroundColor: VARIANT_BG[variant] },
        variant === "secondary" && styles.secondaryBorder,
        isDisabled && styles.disabled,
        pressed && !isDisabled && styles.pressed,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={VARIANT_TEXT[variant]} />
      ) : (
        <Text style={[styles.text, { color: VARIANT_TEXT[variant] }]}>
          {title}
        </Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  secondaryBorder: {
    borderWidth: 1,
    borderColor: Colors.primary,
  },
  disabled: {
    opacity: 0.5,
  },
  pressed: {
    opacity: 0.8,
  },
  text: {
    fontSize: 16,
    fontWeight: "600",
  },
});
