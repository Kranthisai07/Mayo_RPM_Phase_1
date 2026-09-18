# AI Weight-Anomaly Alert — Descriptive Summary

**Date:** 2026-09-18
**Scope:** Descriptive statistics only. This is not a validated evaluation — see Limitations.

## Dataset and Method

The dataset (`backend/data/RPM_combined_100_patients.csv`) has 335 rows tagged `Source=Real`. Of those, **269 rows across 23 distinct subjects** have enough longitudinal history for the model's rolling-window features (day-over-day change, personal baseline deviation, 7-day change) to be computable — the other 66 are each subject's first one or two readings, which the pipeline already excludes rather than scoring with incomplete features. All numbers below are over those 269 evaluable rows.

Scores were produced by running the existing, unmodified `run_weight_anomaly_model()` (the same function wired into the live alert pipeline in commit `7d2d5b9`) against the real data — nothing was changed to produce this summary.

For the rule-based comparison, this CSV has **no SpO2 column at all**, so only the weight rule could be replicated (the SpO2 rule has no data here to test against). The weight rule reproduces `add_vitals_service()`'s exact live thresholds — flagged if the change from the immediately preceding reading is `> +1.5 kg` or `< -2 kg` — applied to the same day-over-day `Weight_Change_kg` field the live app would see.

## Alert Volume

| AI tier | Count | % of evaluable rows |
|---|---|---|
| `high` (the only tier that fires a live Alert) | 14 | 5.2% |
| `watch` (dashboard-only, does not fire an Alert) | 13 | 4.8% |
| `normal` | 242 | 90.0% |

| Rule-based (weight only) | Count | % of evaluable rows |
|---|---|---|
| Flagged | 34 | 12.6% |
| Not flagged | 235 | 87.4% |

## `ai_score` Distribution

Raw `IsolationForest` decision-function value — more negative means more anomalous.

| Group | n | min | median | mean | max |
|---|---|---|---|---|---|
| AI `high` | 14 | -0.2644 | -0.1540 | -0.1635 | -0.1066 |
| AI not-`high` (`watch` + `normal`) | 255 | -0.1029 | 0.1350 | 0.1170 | 0.1705 |

The two groups don't overlap in this sample — every `high`-tier score falls below every non-`high` score. That's a property of the quantile-based tier cutoff by construction (the `high` threshold is set from this same data's own 5th-percentile score), not independent evidence of separability — see Limitations.

## AI vs. Rule-Based: Overlap

|  | Rule-based: not flagged | Rule-based: flagged |
|---|---|---|
| **AI `high`: no** | 233 | 22 |
| **AI `high`: yes** | 2 | 12 |

- **12 rows** were flagged by both.
- **22 rows** were flagged by the rule but not by AI `high` — of these, 8 fell in the AI `watch` tier (a softer signal, visible on the dashboard but not alert-worthy today) and 14 scored fully `normal` by AI. These are single-day swings that cross the fixed day-over-day threshold but aren't unusual relative to that specific patient's own historical variability.
- **2 rows** were flagged by AI `high` but not by the rule. Both are multi-day trends, not single-day swings — one is a 7-day decline of -6.17 kg with only a +0.91 kg change on the day itself; the other is -4.69 kg below the patient's personal baseline with a -1.55 kg same-day change (short of the rule's -2 kg cutoff). The day-over-day rule structurally cannot see either pattern, since it only ever compares two consecutive readings.

## Limitations — read before using this in the paper

- **No ground-truth deterioration labels exist in this dataset.** These numbers describe how often the model flags and how its flags relate to the existing rule, not whether either is *correct*. Do not describe this as precision, recall, sensitivity, or accuracy anywhere in the paper — none of those are computable here.
- **This is in-sample, not held-out.** The model was trained on these same 269 rows and then scored on them. The `high`/`watch` thresholds are the 5th/10th percentile of this exact score distribution, so by construction close to 5%/10% of the data will fall in those tiers regardless of whether the underlying patterns are clinically meaningful. This summary describes the model's behavior on its own training data, not generalization to new patients.
- **Small sample.** 23 subjects, 269 evaluable readings. Individual subjects contribute unequal numbers of rows; the summary above is not adjusted for that.
- **The 2 "AI-only" catches are illustrative, not proof of superior detection** — two data points is not evidence of a general capability, just a concrete example of the kind of case a trend-aware feature set can see that a single-day-delta rule cannot.
