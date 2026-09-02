from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.models import Vitals


DATA_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "RPM_combined_100_patients.csv"
)


def classify_weight_trend(change_per_day):
    """
    Classify direction of weight change.

    This is a trend indicator only.
    It is not a clinical alert.
    """

    if pd.isna(change_per_day):
        return "insufficient_data"

    if change_per_day > 0:
        return "increasing"

    if change_per_day < 0:
        return "decreasing"

    return "stable"


def build_nurse_friendly_reason(row):
    """
    Convert technical model features into a readable
    explanation for the nurse dashboard.

    This explains a statistical pattern only.
    It does not provide a diagnosis.
    """

    reason = row["AI_Primary_Reason"]
    value = row["AI_Primary_Reason_Value"]

    if pd.isna(value):
        return "Insufficient weight history"

    if reason == "Weight_Change_Per_Day_kg":
        if value > 0:
            return f"Rapid weight increase: +{value:.2f} kg/day"

        return f"Rapid weight decrease: {value:.2f} kg/day"

    if reason == "Deviation_From_Baseline_kg":
        if value > 0:
            return (
                f"Weight is {value:.2f} kg above "
                f"the patient's recent baseline"
            )

        return (
            f"Weight is {abs(value):.2f} kg below "
            f"the patient's recent baseline"
        )

    if reason == "Weight_Change_7d_kg":
        if value > 0:
            return f"7-day weight increase: +{value:.2f} kg"

        return f"7-day weight decrease: {value:.2f} kg"

    return "Unusual weight pattern detected"


def load_weight_data():
    """
    Load and prepare the CSV longitudinal patient weight dataset.
    """

    df = pd.read_csv(DATA_FILE)

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce",
    )

    df["Weight"] = pd.to_numeric(
        df["Weight"],
        errors="coerce",
    )

    df = df.dropna(
        subset=["Date", "Weight"]
    ).copy()

    df = df.sort_values(
        ["Subject", "Date"]
    ).reset_index(drop=True)

    df = df.rename(
        columns={
            "Weight": "Weight_kg"
        }
    )

    # ---------------------------------------------------------
    # Previous measurement
    # ---------------------------------------------------------
    df["Previous_Weight_kg"] = (
        df.groupby("Subject")["Weight_kg"]
        .shift(1)
    )

    df["Previous_Date"] = (
        df.groupby("Subject")["Date"]
        .shift(1)
    )

    # ---------------------------------------------------------
    # Weight change
    # ---------------------------------------------------------
    df["Weight_Change_kg"] = (
        df["Weight_kg"]
        - df["Previous_Weight_kg"]
    )

    df["Days_Since_Previous"] = (
        df["Date"]
        - df["Previous_Date"]
    ).dt.days

    safe_days = df["Days_Since_Previous"].mask(
        df["Days_Since_Previous"] == 0
    )

    df["Weight_Change_Per_Day_kg"] = (
        df["Weight_Change_kg"]
        / safe_days
    )

    df["Weight_Trend"] = (
        df["Weight_Change_Per_Day_kg"]
        .apply(classify_weight_trend)
    )

    # ---------------------------------------------------------
    # Personalized baseline
    # ---------------------------------------------------------
    df["Baseline_Weight_kg"] = (
        df.groupby("Subject")["Weight_kg"]
        .transform(
            lambda x: (
                x.shift(1)
                .rolling(
                    window=3,
                    min_periods=2,
                )
                .mean()
            )
        )
    )

    df["Deviation_From_Baseline_kg"] = (
        df["Weight_kg"]
        - df["Baseline_Weight_kg"]
    )

    # ---------------------------------------------------------
    # Patient-specific variability
    # ---------------------------------------------------------
    df["Baseline_Std_kg"] = (
        df.groupby("Subject")["Weight_kg"]
        .transform(
            lambda x: (
                x.shift(1)
                .rolling(
                    window=5,
                    min_periods=3,
                )
                .std()
            )
        )
    )

    safe_std = df["Baseline_Std_kg"].mask(
        df["Baseline_Std_kg"] == 0
    )

    df["Weight_Deviation_Score"] = (
        df["Deviation_From_Baseline_kg"]
        / safe_std
    )

    # ---------------------------------------------------------
    # 7-day weight change
    # ---------------------------------------------------------
    df["Weight_Change_7d_kg"] = float("nan")

    for subject, group in df.groupby("Subject"):
        group = group.sort_values("Date")

        for index, row in group.iterrows():
            current_date = row["Date"]
            current_weight = row["Weight_kg"]

            previous = group[
                (group["Date"] < current_date)
                & (
                    group["Date"]
                    >= current_date - pd.Timedelta(days=7)
                )
            ]

            if not previous.empty:
                oldest_weight = previous.iloc[0]["Weight_kg"]

                df.loc[
                    index,
                    "Weight_Change_7d_kg"
                ] = (
                    current_weight
                    - oldest_weight
                )

    return df


def build_weight_ai_features():
    """
    Build the dataset used by the anomaly model.

    Source is retained for evaluation only.
    It is not used as an AI feature.
    """

    df = load_weight_data()

    feature_columns = [
        "Subject",
        "Age",
        "Gender",
        "Date",
        "Source",
        "Weight_kg",
        "Previous_Weight_kg",
        "Weight_Change_kg",
        "Days_Since_Previous",
        "Weight_Change_Per_Day_kg",
        "Weight_Trend",
        "Baseline_Weight_kg",
        "Deviation_From_Baseline_kg",
        "Baseline_Std_kg",
        "Weight_Deviation_Score",
        "Weight_Change_7d_kg",
    ]

    features = df[
        feature_columns
    ].copy()

    required_ai_features = [
        "Weight_Change_Per_Day_kg",
        "Deviation_From_Baseline_kg",
        "Weight_Change_7d_kg",
    ]

    features = (
        features
        .dropna(
            subset=required_ai_features
        )
        .reset_index(drop=True)
    )

    return features


def prepare_patient_db_weight_history(vitals):
    """
    Convert database Vitals records into one longitudinal
    weight observation per patient per calendar day.

    If multiple measurements exist on the same day,
    keep the latest submitted measurement.
    """

    records = []

    for vital in vitals:
        if vital.weight_value is None:
            continue

        records.append(
            {
                "Vital_ID": vital.id,
                "Subject": vital.patient_id,
                "DateTime": pd.to_datetime(
                    vital.recorded_at
                ),
                "Weight_kg": float(
                    vital.weight_value
                ),
            }
        )

    df = pd.DataFrame(records)

    if df.empty:
        return df

    df = df.sort_values(
        ["Subject", "DateTime"]
    )

    df["Date"] = (
        df["DateTime"]
        .dt.normalize()
    )

    df = (
        df.sort_values(
            [
                "Subject",
                "Date",
                "DateTime",
            ]
        )
        .groupby(
            [
                "Subject",
                "Date",
            ],
            as_index=False,
        )
        .tail(1)
        .reset_index(drop=True)
    )

    df = df.sort_values(
        [
            "Subject",
            "Date",
        ]
    ).reset_index(drop=True)

    return df


def add_weight_features_to_history(df):
    """
    Add longitudinal weight features to prepared
    database weight history.
    """

    if df.empty:
        return df

    df = df.copy()

    df = df.sort_values(
        [
            "Subject",
            "Date",
        ]
    ).reset_index(drop=True)

    # ---------------------------------------------------------
    # Previous measurement
    # ---------------------------------------------------------
    df["Previous_Weight_kg"] = (
        df.groupby("Subject")["Weight_kg"]
        .shift(1)
    )

    df["Previous_Date"] = (
        df.groupby("Subject")["Date"]
        .shift(1)
    )

    # ---------------------------------------------------------
    # Weight change
    # ---------------------------------------------------------
    df["Weight_Change_kg"] = (
        df["Weight_kg"]
        - df["Previous_Weight_kg"]
    )

    df["Days_Since_Previous"] = (
        df["Date"]
        - df["Previous_Date"]
    ).dt.days

    safe_days = df["Days_Since_Previous"].mask(
        df["Days_Since_Previous"] == 0
    )

    df["Weight_Change_Per_Day_kg"] = (
        df["Weight_Change_kg"]
        / safe_days
    )

    df["Weight_Trend"] = (
        df["Weight_Change_Per_Day_kg"]
        .apply(classify_weight_trend)
    )

    # ---------------------------------------------------------
    # Personalized baseline
    # ---------------------------------------------------------
    df["Baseline_Weight_kg"] = (
        df.groupby("Subject")["Weight_kg"]
        .transform(
            lambda x: (
                x.shift(1)
                .rolling(
                    window=3,
                    min_periods=2,
                )
                .mean()
            )
        )
    )

    df["Deviation_From_Baseline_kg"] = (
        df["Weight_kg"]
        - df["Baseline_Weight_kg"]
    )

    # ---------------------------------------------------------
    # Variability
    # ---------------------------------------------------------
    df["Baseline_Std_kg"] = (
        df.groupby("Subject")["Weight_kg"]
        .transform(
            lambda x: (
                x.shift(1)
                .rolling(
                    window=5,
                    min_periods=3,
                )
                .std()
            )
        )
    )

    safe_std = df["Baseline_Std_kg"].mask(
        df["Baseline_Std_kg"] == 0
    )

    df["Weight_Deviation_Score"] = (
        df["Deviation_From_Baseline_kg"]
        / safe_std
    )

    # ---------------------------------------------------------
    # 7-day weight change
    # ---------------------------------------------------------
    df["Weight_Change_7d_kg"] = float("nan")

    for subject, group in df.groupby("Subject"):
        group = group.sort_values("Date")

        for index, row in group.iterrows():
            current_date = row["Date"]
            current_weight = row["Weight_kg"]

            previous = group[
                (group["Date"] < current_date)
                & (
                    group["Date"]
                    >= current_date - pd.Timedelta(days=7)
                )
            ]

            if not previous.empty:
                oldest_weight = previous.iloc[0]["Weight_kg"]

                df.loc[
                    index,
                    "Weight_Change_7d_kg"
                ] = (
                    current_weight
                    - oldest_weight
                )

    return df


def create_weight_model():
    """
    Train the Isolation Forest model from real-patient
    observations and return the reusable model components.
    """

    training_df = build_weight_ai_features()

    model_features = [
        "Weight_Change_Per_Day_kg",
        "Deviation_From_Baseline_kg",
        "Weight_Change_7d_kg",
    ]

    real_training = training_df[
        training_df["Source"] == "Real"
    ].copy()

    if real_training.empty:
        raise ValueError(
            "No real patient observations are available "
            "for model training."
        )

    X_train = real_training[
        model_features
    ]

    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(
        X_train
    )

    model = IsolationForest(
        n_estimators=200,
        contamination="auto",
        random_state=42,
    )

    model.fit(
        X_train_scaled
    )

    real_training_scores = (
        model.decision_function(
            X_train_scaled
        )
    )

    high_threshold = pd.Series(
        real_training_scores
    ).quantile(0.05)

    watch_threshold = pd.Series(
        real_training_scores
    ).quantile(0.10)

    return {
        "model": model,
        "scaler": scaler,
        "model_features": model_features,
        "real_training": real_training,
        "high_threshold": high_threshold,
        "watch_threshold": watch_threshold,
    }


def assign_ai_monitoring_status(
    score,
    high_threshold,
    watch_threshold,
):
    """
    Convert anomaly score into a statistical
    monitoring category.
    """

    if pd.isna(score):
        return "insufficient_data"

    if score <= high_threshold:
        return "high"

    if score <= watch_threshold:
        return "watch"

    return "normal"


def run_weight_anomaly_model():
    """
    Run the model across the CSV dataset.

    Statistical anomaly detection only.
    Not a clinical diagnosis or severity score.
    """

    df = build_weight_ai_features()

    model_bundle = create_weight_model()

    model = model_bundle["model"]
    scaler = model_bundle["scaler"]
    model_features = model_bundle["model_features"]

    high_threshold = model_bundle[
        "high_threshold"
    ]

    watch_threshold = model_bundle[
        "watch_threshold"
    ]

    X_all_scaled = scaler.transform(
        df[model_features]
    )

    scaled_df = pd.DataFrame(
        X_all_scaled,
        columns=model_features,
        index=df.index,
    )

    df["AI_Primary_Reason"] = (
        scaled_df
        .abs()
        .idxmax(axis=1)
    )

    df["AI_Primary_Reason_Value"] = [
        df.loc[index, feature]
        for index, feature
        in df["AI_Primary_Reason"].items()
    ]

    df["AI_Anomaly_Prediction"] = (
        model.predict(
            X_all_scaled
        )
    )

    df["AI_Anomaly_Score"] = (
        model.decision_function(
            X_all_scaled
        )
    )

    df["AI_Is_Anomaly"] = (
        df["AI_Anomaly_Prediction"]
        == -1
    )

    df["AI_Monitoring_Status"] = (
        df["AI_Anomaly_Score"]
        .apply(
            lambda score: assign_ai_monitoring_status(
                score,
                high_threshold,
                watch_threshold,
            )
        )
    )

    df["AI_Reason_Text"] = (
        df.apply(
            build_nurse_friendly_reason,
            axis=1,
        )
    )

    df["AI_High_Threshold"] = (
        high_threshold
    )

    df["AI_Watch_Threshold"] = (
        watch_threshold
    )

    return df


def score_patient_db_weight_history(vitals):
    """
    Score a patient's PostgreSQL weight history.

    Returns only observations with enough history
    for AI scoring.
    """

    patient_df = (
        prepare_patient_db_weight_history(
            vitals
        )
    )

    patient_df = (
        add_weight_features_to_history(
            patient_df
        )
    )

    model_bundle = create_weight_model()

    model = model_bundle["model"]
    scaler = model_bundle["scaler"]
    model_features = model_bundle[
        "model_features"
    ]

    high_threshold = model_bundle[
        "high_threshold"
    ]

    watch_threshold = model_bundle[
        "watch_threshold"
    ]

    patient_ready = (
        patient_df
        .dropna(
            subset=model_features
        )
        .copy()
    )

    if patient_ready.empty:
        return patient_ready

    X_patient_scaled = scaler.transform(
        patient_ready[
            model_features
        ]
    )

    patient_ready[
        "AI_Anomaly_Prediction"
    ] = model.predict(
        X_patient_scaled
    )

    patient_ready[
        "AI_Anomaly_Score"
    ] = model.decision_function(
        X_patient_scaled
    )

    patient_ready[
        "AI_Is_Anomaly"
    ] = (
        patient_ready[
            "AI_Anomaly_Prediction"
        ] == -1
    )

    scaled_patient_df = pd.DataFrame(
        X_patient_scaled,
        columns=model_features,
        index=patient_ready.index,
    )

    patient_ready[
        "AI_Primary_Reason"
    ] = (
        scaled_patient_df
        .abs()
        .idxmax(axis=1)
    )

    patient_ready[
        "AI_Primary_Reason_Value"
    ] = [
        patient_ready.loc[
            index,
            feature,
        ]
        for index, feature
        in patient_ready[
            "AI_Primary_Reason"
        ].items()
    ]

    patient_ready[
        "AI_Reason_Text"
    ] = patient_ready.apply(
        build_nurse_friendly_reason,
        axis=1,
    )

    patient_ready[
        "AI_Monitoring_Status"
    ] = (
        patient_ready[
            "AI_Anomaly_Score"
        ]
        .apply(
            lambda score: assign_ai_monitoring_status(
                score,
                high_threshold,
                watch_threshold,
            )
        )
    )

    patient_ready[
        "AI_High_Threshold"
    ] = high_threshold

    patient_ready[
        "AI_Watch_Threshold"
    ] = watch_threshold

    return patient_ready

def get_latest_patient_weight_ai_status(
    db: Session,
    patient_id: int,
):
    """
    Return both:

    1. The patient's latest actual weight measurement.
    2. The latest weight measurement that had enough
       longitudinal history for AI analysis.

    This prevents an older AI result from being presented
    as though it belongs to the newest weight measurement.
    """

    vitals = (
        db.query(Vitals)
        .filter(
            Vitals.patient_id == patient_id
        )
        .order_by(
            Vitals.recorded_at.asc()
        )
        .all()
    )

    if not vitals:
        return {
            "patient_id": patient_id,
            "status": "no_data",
            "message": "No vitals found for this patient",
        }

    # ---------------------------------------------------------
    # Latest ACTUAL database weight
    # ---------------------------------------------------------
    weight_vitals = [
        vital
        for vital in vitals
        if vital.weight_value is not None
    ]

    if not weight_vitals:
        return {
            "patient_id": patient_id,
            "status": "no_weight_data",
            "message": "No weight measurements found",
        }

    latest_actual = weight_vitals[-1]

    latest_actual_weight = float(
        latest_actual.weight_value
    )

    latest_actual_datetime = pd.to_datetime(
        latest_actual.recorded_at
    )

    # ---------------------------------------------------------
    # AI scoring
    # ---------------------------------------------------------
    scored = score_patient_db_weight_history(
        vitals
    )

    # ---------------------------------------------------------
    # Not enough history for AI
    # ---------------------------------------------------------
    if scored.empty:
        return {
            "patient_id": int(patient_id),
            "status": "insufficient_data",

            "latest_weight": {
                "weight_kg": latest_actual_weight,
                "recorded_at": (
                    latest_actual_datetime.isoformat()
                ),
            },

            "ai_analysis": None,

            "message": (
                "Latest weight is available, but there is "
                "not enough longitudinal history for "
                "AI analysis."
            ),
        }

    # ---------------------------------------------------------
    # Latest AI-analyzable reading
    # ---------------------------------------------------------
    latest_ai = (
        scored
        .sort_values("Date")
        .iloc[-1]
    )

    latest_ai_date = pd.to_datetime(
        latest_ai["Date"]
    )

    # Compare calendar dates because AI history
    # is reduced to one measurement per day.
    actual_calendar_date = (
        latest_actual_datetime.date()
    )

    ai_calendar_date = (
        latest_ai_date.date()
    )

    ai_is_current = (
        actual_calendar_date
        == ai_calendar_date
    )

    # ---------------------------------------------------------
    # Response
    # ---------------------------------------------------------
    return {
        "patient_id": int(patient_id),
        "status": "ok",

        # Latest real measurement from PostgreSQL
        "latest_weight": {
            "weight_kg": latest_actual_weight,
            "recorded_at": (
                latest_actual_datetime.isoformat()
            ),
        },

        # Latest measurement for which AI had
        # enough history to calculate all features
        "ai_analysis": {
            "analysis_date": (
                latest_ai_date.isoformat()
            ),

            "weight_kg": float(
                latest_ai["Weight_kg"]
            ),

            "monitoring_status": (
                latest_ai[
                    "AI_Monitoring_Status"
                ]
            ),

            "reason_text": (
                latest_ai[
                    "AI_Reason_Text"
                ]
            ),

            "anomaly_score": float(
                latest_ai[
                    "AI_Anomaly_Score"
                ]
            ),

            "is_anomaly": bool(
                latest_ai[
                    "AI_Is_Anomaly"
                ]
            ),

            "weight_change_per_day_kg": float(
                latest_ai[
                    "Weight_Change_Per_Day_kg"
                ]
            ),

            "deviation_from_baseline_kg": float(
                latest_ai[
                    "Deviation_From_Baseline_kg"
                ]
            ),

            "weight_change_7d_kg": float(
                latest_ai[
                    "Weight_Change_7d_kg"
                ]
            ),

            "baseline_weight_kg": float(
                latest_ai[
                    "Baseline_Weight_kg"
                ]
            ),
        },

        # Important field for frontend
        "ai_analysis_is_current": ai_is_current,

        "message": (
            "AI analysis reflects the latest weight."
            if ai_is_current
            else
            "Latest weight does not yet have enough "
            "longitudinal history for complete AI analysis. "
            "AI result shown is from the most recent "
            "analyzable weight."
        ),
    }