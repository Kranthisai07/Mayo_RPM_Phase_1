import { View, Text, StyleSheet, FlatList } from "react-native";
import { useCallback, useEffect, useState } from "react";
import { useLocalSearchParams } from "expo-router";

import {
  getAssignedPatientDetail,
  getPatientWeightAIStatus,
} from "../../../src/features/nurse/nurseService";

import {
  acknowledgeAlert,
  resolveAlert,
  escalateAlert,
} from "../../../src/features/alerts/alertService";

import Card from "../../../src/components/card";
import PrimaryButton from "../../../src/components/PrimaryButton";
import StatusBadge from "../../../src/components/StatusBadge";
import { Colors } from "../../../src/constants/colors";
import { notify } from "../../../src/utils/alert";


export default function PatientDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();

  const [detail, setDetail] = useState<any>(null);
  const [weightAI, setWeightAI] = useState<any>(null);

  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      const patientId = Number(id);

      const [
        patientData,
        weightAIData,
      ] = await Promise.all([
        getAssignedPatientDetail(patientId),
        getPatientWeightAIStatus(patientId),
      ]);

      setDetail(patientData);
      setWeightAI(weightAIData);

    } catch (err) {
      console.log(
        "Patient detail load error",
        err
      );
    }
  }, [id]);


  useEffect(() => {
    load();
  }, [load]);


  const handleAlertAction = async (
    alertId: number,
    action: "acknowledge" | "resolve" | "escalate"
  ) => {
    setLoading(true);

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
      notify(
        "Action failed",
        err?.response?.data?.detail
          ?? "Please try again."
      );

    } finally {
      setLoading(false);
    }
  };


  if (!detail) {
    return (
      <View style={styles.flex}>
        <Text style={styles.empty}>
          Loading...
        </Text>
      </View>
    );
  }


  const aiAnalysis =
    weightAI?.ai_analysis ?? null;

  const latestWeight =
    weightAI?.latest_weight ?? null;

  const aiIsCurrent =
    weightAI?.ai_analysis_is_current
    ?? false;


  return (
    <FlatList
      style={styles.flex}

      contentContainerStyle={
        styles.container
      }

      data={
        detail.recent_vitals
      }

      keyExtractor={
        (item: any) =>
          `vital-${item.id}`
      }

      ListHeaderComponent={() => (
        <>

          {/* -------------------------------- */}
          {/* Patient information */}
          {/* -------------------------------- */}

          <Card>
            <Text style={styles.name}>
              {detail.patient.name}
            </Text>

            <Text style={styles.email}>
              {detail.patient.email}
            </Text>
          </Card>


          {/* -------------------------------- */}
          {/* Active alerts */}
          {/* -------------------------------- */}

          {detail.active_alerts.length > 0 && (
            <Card>

              <Text style={styles.sectionTitle}>
                Active Alerts
              </Text>

              {detail.active_alerts.map(
                (alert: any) => (

                  <View
                    key={alert.id}
                    style={styles.alertRow}
                  >

                    <View
                      style={
                        styles.alertBadges
                      }
                    >

                      <StatusBadge
                        label={
                          alert.severity
                        }

                        tone={
                          alert.severity
                            === "critical"
                            ? "danger"
                            : "warning"
                        }
                      />

                      {alert.is_escalated && (
                        <StatusBadge
                          label="Escalated"
                          tone="danger"
                        />
                      )}

                    </View>

                    <Text
                      style={
                        styles.alertMessage
                      }
                    >
                      {alert.message}
                    </Text>

                    <View
                      style={
                        styles.alertActions
                      }
                    >

                      <PrimaryButton
                        title="Received"

                        variant="secondary"

                        loading={loading}

                        onPress={() =>
                          handleAlertAction(
                            alert.id,
                            "acknowledge"
                          )
                        }

                        style={
                          styles.alertButton
                        }
                      />

                      {!alert.is_escalated && (
                        <PrimaryButton
                          title="Escalate"

                          variant="secondary"

                          loading={loading}

                          onPress={() =>
                            handleAlertAction(
                              alert.id,
                              "escalate"
                            )
                          }

                          style={
                            styles.alertButton
                          }
                        />
                      )}

                      <PrimaryButton
                        title="Resolve"

                        loading={loading}

                        onPress={() =>
                          handleAlertAction(
                            alert.id,
                            "resolve"
                          )
                        }

                        style={
                          styles.alertButton
                        }
                      />

                    </View>

                  </View>
                )
              )}

            </Card>
          )}


          {/* -------------------------------- */}
          {/* Weight AI monitoring */}
          {/* -------------------------------- */}

          {weightAI && (
            <Card>

              <View
                style={
                  styles.aiHeader
                }
              >

                <Text
                  style={
                    styles.sectionTitleNoMargin
                  }
                >
                  Weight AI Monitoring
                </Text>

                {aiAnalysis && (
                  <StatusBadge
                    label={
                      aiAnalysis.monitoring_status
                    }

                    tone={
                      aiAnalysis.monitoring_status
                        === "high"
                        ? "danger"
                        : aiAnalysis.monitoring_status
                          === "watch"
                          ? "warning"
                          : "success"
                    }
                  />
                )}

              </View>


              {/* Latest real DB weight */}

              {latestWeight && (
                <View
                  style={
                    styles.aiSection
                  }
                >

                  <Text
                    style={
                      styles.aiLabel
                    }
                  >
                    Latest Weight
                  </Text>

                  <Text
                    style={
                      styles.aiWeight
                    }
                  >
                    {
                      latestWeight.weight_kg
                    } kg
                  </Text>

                  <Text
                    style={
                      styles.aiDate
                    }
                  >
                    {new Date(
                      latestWeight.recorded_at
                    ).toLocaleString()}
                  </Text>

                </View>
              )}


              {/* AI result */}

              {aiAnalysis ? (
                <View>

                  {!aiIsCurrent && (
                    <View
                      style={
                        styles.aiNotice
                      }
                    >
                      <Text
                        style={
                          styles.aiNoticeText
                        }
                      >
                        AI analysis is based on
                        the most recent weight
                        with enough longitudinal
                        history.
                      </Text>
                    </View>
                  )}


                  <View
                    style={
                      styles.aiSection
                    }
                  >

                    <Text
                      style={
                        styles.aiLabel
                      }
                    >
                      AI Analysis
                    </Text>

                    <Text
                      style={
                        styles.aiReason
                      }
                    >
                      {
                        aiAnalysis.reason_text
                      }
                    </Text>

                    <Text
                      style={
                        styles.aiDate
                      }
                    >
                      Analyzed weight:{" "}
                      {
                        aiAnalysis.weight_kg
                      } kg
                    </Text>

                    <Text
                      style={
                        styles.aiDate
                      }
                    >
                      {new Date(
                        aiAnalysis.analysis_date
                      ).toLocaleDateString()}
                    </Text>

                  </View>


                  <View
                    style={
                      styles.aiMetrics
                    }
                  >

                    <View
                      style={
                        styles.aiMetric
                      }
                    >
                      <Text
                        style={
                          styles.aiMetricLabel
                        }
                      >
                        Baseline
                      </Text>

                      <Text
                        style={
                          styles.aiMetricValue
                        }
                      >
                        {
                          aiAnalysis
                            .baseline_weight_kg
                            ?.toFixed(1)
                        } kg
                      </Text>
                    </View>


                    <View
                      style={
                        styles.aiMetric
                      }
                    >
                      <Text
                        style={
                          styles.aiMetricLabel
                        }
                      >
                        Baseline Change
                      </Text>

                      <Text
                        style={
                          styles.aiMetricValue
                        }
                      >
                        {
                          aiAnalysis
                            .deviation_from_baseline_kg
                            ?.toFixed(1)
                        } kg
                      </Text>
                    </View>


                    <View
                      style={
                        styles.aiMetric
                      }
                    >
                      <Text
                        style={
                          styles.aiMetricLabel
                        }
                      >
                        7-Day Change
                      </Text>

                      <Text
                        style={
                          styles.aiMetricValue
                        }
                      >
                        {
                          aiAnalysis
                            .weight_change_7d_kg
                            ?.toFixed(1)
                        } kg
                      </Text>
                    </View>

                  </View>

                </View>

              ) : (

                <Text
                  style={
                    styles.aiUnavailable
                  }
                >
                  {
                    weightAI.message
                    ?? "Not enough weight history for AI analysis."
                  }
                </Text>

              )}

            </Card>
          )}


          {/* -------------------------------- */}
          {/* Vitals history */}
          {/* -------------------------------- */}

          <Text style={styles.sectionTitle}>
            Vitals History
          </Text>

        </>
      )}


      ListEmptyComponent={() => (
        <Text style={styles.empty}>
          No vitals recorded yet.
        </Text>
      )}


      renderItem={({ item }: any) => (

        <Card style={styles.vitalCard}>

          <View style={styles.vitalRow}>

            <Text style={styles.vitalValue}>
              {item.weight_value} kg
            </Text>

            <Text style={styles.vitalValue}>
              {item.spo2_value}% SpO₂
            </Text>

          </View>

          <Text style={styles.vitalDate}>
            {
              item.recorded_at
                ? new Date(
                    item.recorded_at
                  ).toLocaleString()
                : ""
            }
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

  name: {
    fontSize: 20,
    fontWeight: "700",
    color: Colors.text,
  },

  email: {
    fontSize: 14,
    color: Colors.muted,
  },

  sectionTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.text,
    marginBottom: 10,
  },

  sectionTitleNoMargin: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.text,
  },

  alertRow: {
    marginBottom: 14,
  },

  alertBadges: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 6,
  },

  alertMessage: {
    color: Colors.text,
    fontSize: 14,
    marginBottom: 10,
  },

  alertActions: {
    flexDirection: "row",
    gap: 10,
  },

  alertButton: {
    flex: 1,
  },

  aiHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 14,
  },

  aiSection: {
    marginBottom: 14,
  },

  aiLabel: {
    fontSize: 12,
    fontWeight: "600",
    color: Colors.muted,
    marginBottom: 4,
  },

  aiWeight: {
    fontSize: 24,
    fontWeight: "700",
    color: Colors.text,
  },

  aiDate: {
    fontSize: 12,
    color: Colors.muted,
    marginTop: 2,
  },

  aiReason: {
    fontSize: 15,
    fontWeight: "600",
    color: Colors.text,
    marginBottom: 4,
  },

  aiNotice: {
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
    marginBottom: 14,
  },

  aiNoticeText: {
    fontSize: 12,
    color: Colors.muted,
  },

  aiMetrics: {
    flexDirection: "row",
    gap: 10,
  },

  aiMetric: {
    flex: 1,
  },

  aiMetricLabel: {
    fontSize: 11,
    color: Colors.muted,
    marginBottom: 2,
  },

  aiMetricValue: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.text,
  },

  aiUnavailable: {
    fontSize: 13,
    color: Colors.muted,
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