import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Animated,
  Dimensions,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Colors } from "../constants/colors";

export type PatientOption = {
  id: number | string;
  name: string;
  email?: string;
};

type Props = {
  patients: PatientOption[];
  selectedPatient?: PatientOption | null;
  onSelect: (patient: PatientOption) => void;
  placeholder?: string;
  label?: string;
  loading?: boolean;
};

const isWeb = Platform.OS === "web";
const DEBOUNCE_MS = 200;
const ROW_HEIGHT = 64;
const SCREEN_HEIGHT = Dimensions.get("window").height;

// react-native's own Modal wraps content in a focus trap, which would steal
// focus away from the search TextInput (it deliberately stays outside the
// portaled results panel in the web autocomplete pattern below). Loading
// react-dom directly, only at runtime on web, avoids that side effect while
// still escaping the FlatList's stacking context via a real DOM portal.
// eslint-disable-next-line @typescript-eslint/no-require-imports
const createPortal: any = isWeb ? require("react-dom").createPortal : null;

function getInitials(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export default function PatientSearchDropdown({
  patients,
  selectedPatient = null,
  onSelect,
  placeholder = "Search patient by name or email...",
  label,
  loading = false,
}: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const [panelRect, setPanelRect] = useState<{ top: number; left: number; width: number } | null>(
    null
  );

  const wrapperRef = useRef<any>(null);
  const triggerBoxRef = useRef<any>(null);
  const inputRef = useRef<any>(null);
  const animatedValue = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query.trim().toLowerCase());
    }, DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [query]);

  const filtered = useMemo(() => {
    if (!debouncedQuery) return patients;
    return patients.filter((patient) => {
      const haystack = `${patient.name} ${patient.email ?? ""}`.toLowerCase();
      return haystack.includes(debouncedQuery);
    });
  }, [patients, debouncedQuery]);

  useEffect(() => {
    setActiveIndex(0);
  }, [debouncedQuery, open]);

  useEffect(() => {
    Animated.timing(animatedValue, {
      toValue: open ? 1 : 0,
      duration: 220,
      useNativeDriver: !isWeb,
    }).start();
  }, [open, animatedValue]);

  const closeDropdown = useCallback(() => {
    setOpen(false);
    setQuery("");
  }, []);

  // Measures the trigger box in viewport coordinates so the portaled panel
  // (rendered outside the FlatList's stacking context, see openDropdown) can
  // be anchored directly under it with position: "fixed".
  const measureTrigger = useCallback(() => {
    const node = triggerBoxRef.current;
    if (node && node.getBoundingClientRect) {
      const rect = node.getBoundingClientRect();
      setPanelRect({ top: rect.bottom + 8, left: rect.left, width: rect.width });
    }
  }, []);

  const openDropdown = useCallback(() => {
    setOpen(true);
    setQuery("");
    measureTrigger();
    requestAnimationFrame(() => inputRef.current?.focus?.());
  }, [measureTrigger]);

  const handleSelect = useCallback(
    (patient: PatientOption) => {
      onSelect(patient);
      closeDropdown();
    },
    [onSelect, closeDropdown]
  );

  // Keep the portaled panel aligned with the trigger if the window resizes
  // while it's open (e.g. rotating a tablet or resizing a browser window).
  useEffect(() => {
    if (!isWeb || !open) return;
    window.addEventListener("resize", measureTrigger);
    return () => window.removeEventListener("resize", measureTrigger);
  }, [open, measureTrigger]);

  // Arrow/Enter/Escape keyboard navigation for the web autocomplete.
  useEffect(() => {
    if (!isWeb || !open) return;
    const node = inputRef.current;
    if (!node || !node.addEventListener) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        setActiveIndex((i) => Math.min(i + 1, filtered.length - 1));
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        setActiveIndex((i) => Math.max(i - 1, 0));
      } else if (event.key === "Enter") {
        event.preventDefault();
        const patient = filtered[activeIndex];
        if (patient) handleSelect(patient);
      } else if (event.key === "Escape") {
        event.preventDefault();
        closeDropdown();
      }
    };
    node.addEventListener("keydown", handleKeyDown);
    return () => node.removeEventListener("keydown", handleKeyDown);
  }, [open, filtered, activeIndex, handleSelect, closeDropdown]);

  const renderSkeleton = () => (
    <View style={styles.listContent}>
      {[0, 1, 2, 3].map((i) => (
        <View key={`skeleton-${i}`} style={styles.skeletonRow}>
          <View style={styles.skeletonAvatar} />
          <View style={styles.skeletonLines}>
            <View style={styles.skeletonLineWide} />
            <View style={styles.skeletonLineNarrow} />
          </View>
        </View>
      ))}
    </View>
  );

  const renderEmpty = () => (
    <View style={styles.emptyState}>
      <Ionicons name="search-outline" size={22} color={Colors.muted} />
      <Text style={styles.emptyText}>No patients found</Text>
    </View>
  );

  const renderRow = useCallback(
    (patient: PatientOption, index: number) => {
      const isSelected = selectedPatient?.id === patient.id;
      const isActive = isWeb && index === activeIndex;
      return (
        <Pressable
          key={`patient-${patient.id}`}
          onPress={() => handleSelect(patient)}
          accessibilityRole="button"
          accessibilityLabel={`${patient.name}${patient.email ? `, ${patient.email}` : ""}`}
          accessibilityState={{ selected: isSelected }}
          style={({ pressed }) => [
            styles.row,
            isActive && styles.rowActive,
            isSelected && styles.rowSelected,
            pressed && styles.rowPressed,
          ]}
        >
          <View style={[styles.avatar, isSelected && styles.avatarSelected]}>
            <Text style={[styles.avatarText, isSelected && styles.avatarTextSelected]}>
              {getInitials(patient.name)}
            </Text>
          </View>
          <View style={styles.rowText}>
            <Text style={styles.rowName} numberOfLines={1} ellipsizeMode="tail">
              {patient.name}
            </Text>
            {patient.email ? (
              <Text style={styles.rowEmail} numberOfLines={1} ellipsizeMode="tail">
                {patient.email}
              </Text>
            ) : null}
          </View>
          {isSelected && (
            <Ionicons name="checkmark-circle" size={20} color={Colors.primary} />
          )}
        </Pressable>
      );
    },
    [activeIndex, handleSelect, selectedPatient]
  );

  const renderList = () => {
    if (loading) return renderSkeleton();
    if (filtered.length === 0) return renderEmpty();

    return (
      <ScrollView
        style={styles.list}
        contentContainerStyle={styles.listContent}
        keyboardShouldPersistTaps="handled"
        nestedScrollEnabled
      >
        {filtered.map((patient, index) => renderRow(patient, index))}
      </ScrollView>
    );
  };

  if (isWeb) {
    return (
      <View ref={wrapperRef} style={styles.webWrapper}>
        {label ? <Text style={styles.label}>{label}</Text> : null}
        <View
          ref={triggerBoxRef}
          style={[styles.inputWrapper, open && styles.inputWrapperFocused]}
        >
          <Ionicons name="search" size={18} color={Colors.muted} style={styles.searchIcon} />
          <TextInput
            ref={inputRef}
            value={open ? query : selectedPatient?.name ?? ""}
            onFocus={openDropdown}
            onChangeText={setQuery}
            placeholder={placeholder}
            placeholderTextColor={Colors.muted}
            style={styles.input}
            accessibilityLabel="Search patients by name or email"
          />
        </View>

        {/*
          Rendered through a raw react-dom portal to document.body instead of a
          plain position:"absolute" sibling. A FlatList's ListHeaderComponent
          creates its own stacking context, so no zIndex on an element inside it
          can ever paint above the FlatList's later row items — the panel needs
          to escape that tree entirely, anchored to the trigger's live viewport
          coordinates. (react-native's Modal would do the same escape, but its
          focus trap steals focus from the TextInput above, which stays outside
          the portal on purpose — see the createPortal note near the top.)
        */}
        {open &&
          panelRect &&
          createPortal(
            <>
              <Pressable style={styles.webModalBackdrop} onPress={closeDropdown} />
              <Animated.View
                style={[
                  styles.webPanel,
                  {
                    top: panelRect.top,
                    left: panelRect.left,
                    width: panelRect.width,
                    opacity: animatedValue,
                    transform: [
                      {
                        translateY: animatedValue.interpolate({
                          inputRange: [0, 1],
                          outputRange: [-6, 0],
                        }),
                      },
                    ],
                  },
                ]}
              >
                {renderList()}
              </Animated.View>
            </>,
            document.body
          )}
      </View>
    );
  }

  return (
    <View style={styles.wrapper}>
      {label ? <Text style={styles.label}>{label}</Text> : null}
      <Pressable
        onPress={openDropdown}
        style={styles.inputWrapper}
        accessibilityRole="button"
        accessibilityLabel={label ?? "Jump to patient"}
      >
        <Ionicons name="search" size={18} color={Colors.muted} style={styles.searchIcon} />
        <Text
          style={[styles.triggerText, !selectedPatient && styles.triggerPlaceholder]}
          numberOfLines={1}
          ellipsizeMode="tail"
        >
          {selectedPatient ? selectedPatient.name : placeholder}
        </Text>
        <Ionicons name="chevron-down" size={16} color={Colors.muted} />
      </Pressable>

      <Modal visible={open} transparent animationType="none" onRequestClose={closeDropdown}>
        <View style={styles.modalRoot}>
          <Pressable style={styles.backdrop} onPress={closeDropdown} />
          <KeyboardAvoidingView
            behavior={Platform.OS === "ios" ? "padding" : undefined}
            style={styles.sheetContainer}
            pointerEvents="box-none"
          >
            <Animated.View
              style={[
                styles.sheet,
                {
                  transform: [
                    {
                      translateY: animatedValue.interpolate({
                        inputRange: [0, 1],
                        outputRange: [SCREEN_HEIGHT, 0],
                      }),
                    },
                  ],
                },
              ]}
            >
              <View style={styles.sheetHandle} />
              <View style={styles.sheetSearchWrapper}>
                <Ionicons name="search" size={18} color={Colors.muted} style={styles.searchIcon} />
                <TextInput
                  ref={inputRef}
                  value={query}
                  onChangeText={setQuery}
                  placeholder={placeholder}
                  placeholderTextColor={Colors.muted}
                  style={styles.input}
                  autoFocus
                  returnKeyType="search"
                  accessibilityLabel="Search patients by name or email"
                />
                {query.length > 0 && (
                  <Pressable onPress={() => setQuery("")} hitSlop={8}>
                    <Ionicons name="close-circle" size={18} color={Colors.muted} />
                  </Pressable>
                )}
              </View>
              <View style={styles.sheetListWrapper}>{renderList()}</View>
            </Animated.View>
          </KeyboardAvoidingView>
        </View>
      </Modal>
    </View>
  );
}

const softShadow = Platform.select({
  web: { boxShadow: "0px 2px 8px rgba(0,0,0,0.06)" },
  default: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
});

const panelShadow = Platform.select({
  web: { boxShadow: "0px 8px 20px rgba(0,0,0,0.14)" },
  default: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.14,
    shadowRadius: 20,
    elevation: 10,
  },
});

const sheetShadow = Platform.select({
  web: { boxShadow: "0px -4px 16px rgba(0,0,0,0.1)" },
  default: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.1,
    shadowRadius: 16,
    elevation: 12,
  },
});

const styles = StyleSheet.create({
  wrapper: {
    width: "100%",
  },

  webWrapper: {
    width: "100%",
    maxWidth: "100%",
    position: "relative",
    zIndex: 20,
  },

  label: {
    fontSize: 15,
    fontWeight: "600",
    color: Colors.text,
    marginBottom: 8,
  },

  inputWrapper: {
    flexDirection: "row",
    alignItems: "center",
    width: "100%",
    maxWidth: "100%",
    overflow: "hidden",
    backgroundColor: Colors.card,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: Platform.OS === "ios" ? 14 : 12,
    gap: 10,
    ...softShadow,
  },

  inputWrapperFocused: {
    borderColor: Colors.primary,
  },

  searchIcon: {
    marginRight: 2,
  },

  input: {
    flex: 1,
    fontSize: 16,
    color: Colors.text,
    paddingVertical: 0,
    ...Platform.select({ web: { outlineStyle: "none" } }),
  },

  triggerText: {
    flex: 1,
    fontSize: 16,
    color: Colors.text,
  },

  triggerPlaceholder: {
    color: Colors.muted,
  },

  webModalBackdrop: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 9998,
  },

  webPanel: {
    position: "absolute",
    maxWidth: "100%",
    backgroundColor: Colors.card,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: Colors.border,
    maxHeight: 320,
    overflow: "hidden",
    zIndex: 9999,
    ...panelShadow,
  },

  list: {
    maxHeight: 320,
    ...Platform.select({ web: { overflowY: "auto", overflowX: "hidden" } }),
  },

  listContent: {
    paddingVertical: 6,
  },

  row: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginHorizontal: 6,
    borderRadius: 12,
    gap: 12,
    height: ROW_HEIGHT,
    maxWidth: "100%",
    overflow: "hidden",
  },

  rowActive: {
    backgroundColor: Colors.background,
  },

  rowSelected: {
    backgroundColor: Colors.primarySoft,
  },

  rowPressed: {
    opacity: 0.7,
  },

  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.border,
    alignItems: "center",
    justifyContent: "center",
  },

  avatarSelected: {
    backgroundColor: Colors.primary,
  },

  avatarText: {
    fontSize: 14,
    fontWeight: "700",
    color: Colors.text,
  },

  avatarTextSelected: {
    color: "#ffffff",
  },

  rowText: {
    flex: 1,
    minWidth: 0,
    overflow: "hidden",
  },

  rowName: {
    fontSize: 15,
    fontWeight: "600",
    color: Colors.text,
  },

  rowEmail: {
    fontSize: 12,
    color: Colors.muted,
    marginTop: 2,
  },

  emptyState: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 32,
    gap: 8,
  },

  emptyText: {
    fontSize: 14,
    color: Colors.muted,
  },

  skeletonRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 18,
    paddingVertical: 10,
    gap: 12,
    height: ROW_HEIGHT,
  },

  skeletonAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.border,
  },

  skeletonLines: {
    flex: 1,
    gap: 8,
  },

  skeletonLineWide: {
    height: 12,
    borderRadius: 6,
    backgroundColor: Colors.border,
    width: "60%",
  },

  skeletonLineNarrow: {
    height: 10,
    borderRadius: 5,
    backgroundColor: Colors.border,
    width: "40%",
  },

  modalRoot: {
    flex: 1,
    justifyContent: "flex-end",
  },

  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: Colors.overlay,
  },

  sheetContainer: {
    justifyContent: "flex-end",
  },

  sheet: {
    backgroundColor: Colors.card,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingTop: 10,
    paddingBottom: 24,
    maxHeight: "85%",
    ...sheetShadow,
  },

  sheetHandle: {
    width: 36,
    height: 4,
    borderRadius: 2,
    backgroundColor: Colors.border,
    alignSelf: "center",
    marginBottom: 14,
  },

  sheetSearchWrapper: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.background,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 12,
    marginHorizontal: 16,
    marginBottom: 10,
    gap: 10,
  },

  sheetListWrapper: {
    flexShrink: 1,
  },
});
