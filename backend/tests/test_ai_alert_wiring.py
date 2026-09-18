"""
End-to-end: a genuinely anomalous weight reading, submitted through the
real add_vitals_service() path, must produce a real Alert row (not just
a UI-rendered score) - visible to the assigned nurse, carrying the raw
ai_score, and not duplicated on a second anomalous submission.

Uses a small synthetic training CSV (real IsolationForest, not mocked)
and an in-memory SQLite DB (real models/queries, not mocked). Monkeypatches
weight_analysis_service.DATA_FILE/CACHE_FILE so this never touches the
real dataset or the real model cache.

Standalone script, no test framework required:

    app_env/Scripts/python.exe tests/test_ai_alert_wiring.py   (Windows)
    app_env/bin/python tests/test_ai_alert_wiring.py            (macOS/Linux)
"""

import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models import Alert, PatientAssignment, User, Vitals
from app.services import weight_analysis_service as wa
from app.services.vitals_service import add_vitals_service


CSV_HEADER = "Subject,Age,Gender,Date,Weight,Source\n"


def make_training_csv(path: Path):
    """Eight training subjects with very tight, near-identical
    day-to-day fluctuations. IsolationForest's decision_function
    saturates for far-out points (a +10kg jump and a +30kg jump score
    almost identically - the point gets isolated within the first
    couple of splits either way), so a genuinely anomalous test point's
    score only clears the "high" threshold when the training
    distribution itself is tight enough to push that threshold close
    to zero. Calibrated empirically against this exact test's fixture -
    see the "high"/"watch" thresholds this produces if you change it."""
    lines = [CSV_HEADER]
    base_weights = [
        70.0, 70.05, 69.98, 70.02, 70.0,
        69.97, 70.03, 70.0, 69.99, 70.01, 70.02, 69.98,
    ]
    for subject in range(1, 9):
        for i, w in enumerate(base_weights):
            lines.append(f"{subject},50,F,2026-01-{i + 1:02d},{w:.2f},Real\n")
    path.write_text("".join(lines))


def make_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def seed_patient_and_nurse(db):
    patient = User(
        name="AI Test Patient", email="ai-test@test.local",
        password_hash="x", role="patient", is_active=True,
    )
    nurse = User(
        name="AI Test Nurse", email="ai-nurse@test.local",
        password_hash="x", role="nurse", is_active=True, is_available=True,
    )
    db.add_all([patient, nurse])
    db.commit()
    db.refresh(patient)
    db.refresh(nurse)
    db.add(PatientAssignment(patient_id=patient.id, nurse_id=nurse.id, is_active=True))
    db.commit()
    return patient, nurse


def backdate_stable_history(db, patient_id):
    """Insert five stable historical readings directly, spread across
    real past days (not "just now" in rapid succession - the model's
    rolling-window features need genuine day-over-day spacing to have
    enough history at all, matching how real patients submit one
    reading per day rather than several in the same minute)."""
    today = datetime.now(timezone.utc)
    for days_ago, w in zip([6, 5, 4, 3, 2], [70.0, 70.02, 69.99, 70.01, 70.0]):
        db.add(Vitals(
            patient_id=patient_id,
            weight_value=w,
            spo2_value=97,
            recorded_at=today - timedelta(days=days_ago),
        ))
    db.commit()


def with_isolated_ai(fn):
    original_data_file = wa.DATA_FILE
    original_cache_file = wa.CACHE_FILE
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        wa.DATA_FILE = tmp_path / "data.csv"
        wa.CACHE_FILE = tmp_path / ".weight_model_cache.joblib"
        wa._cached_weight_model.cache_clear()
        make_training_csv(wa.DATA_FILE)
        try:
            fn()
        finally:
            wa.DATA_FILE = original_data_file
            wa.CACHE_FILE = original_cache_file
            wa._cached_weight_model.cache_clear()


def test_anomalous_reading_creates_visible_ai_alert():
    def body():
        db = make_session()
        patient, nurse = seed_patient_and_nurse(db)
        backdate_stable_history(db, patient.id)

        # Wildly anomalous jump relative to the tight training distribution.
        add_vitals_service(db, patient.id, 100.0, 97)

        ai_alerts = (
            db.query(Alert)
            .filter(Alert.patient_id == patient.id, Alert.alert_type == "ai_weight_anomaly")
            .all()
        )
        assert len(ai_alerts) == 1, f"expected exactly 1 AI alert, got {len(ai_alerts)}"
        alert = ai_alerts[0]
        assert alert.severity == "high", alert.severity
        assert alert.status == "active", alert.status
        assert alert.ai_score is not None, "ai_score must be populated"
        assert isinstance(alert.message, str) and len(alert.message) > 0

        # Visible to the assigned nurse via the real nurse-facing query.
        from app.services.alert_service import get_alerts_for_nurse
        nurse_alerts = get_alerts_for_nurse(db, nurse.id)
        assert any(a.id == alert.id for a in nurse_alerts), (
            "AI alert must be visible in the nurse's alert queue"
        )

    with_isolated_ai(body)


def test_stable_reading_does_not_create_ai_alert():
    def body():
        db = make_session()
        patient, _nurse = seed_patient_and_nurse(db)
        backdate_stable_history(db, patient.id)

        ai_alerts = (
            db.query(Alert)
            .filter(Alert.alert_type == "ai_weight_anomaly")
            .all()
        )
        assert len(ai_alerts) == 0, f"expected 0 AI alerts from stable readings, got {len(ai_alerts)}"

    with_isolated_ai(body)


def test_second_anomalous_reading_does_not_duplicate_active_ai_alert():
    def body():
        db = make_session()
        patient, _nurse = seed_patient_and_nurse(db)
        backdate_stable_history(db, patient.id)

        add_vitals_service(db, patient.id, 100.0, 97)
        add_vitals_service(db, patient.id, 101.0, 97)

        ai_alerts = (
            db.query(Alert)
            .filter(Alert.patient_id == patient.id, Alert.alert_type == "ai_weight_anomaly")
            .all()
        )
        assert len(ai_alerts) == 1, (
            f"expected the second anomalous submission to skip creating a "
            f"duplicate while one is still active, got {len(ai_alerts)}"
        )

    with_isolated_ai(body)


if __name__ == "__main__":
    tests = [
        test_anomalous_reading_creates_visible_ai_alert,
        test_stable_reading_does_not_create_ai_alert,
        test_second_anomalous_reading_does_not_duplicate_active_ai_alert,
    ]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL: {test.__name__}: {e}")
        except Exception as e:
            failures += 1
            print(f"ERROR: {test.__name__}: {type(e).__name__}: {e}")

    if failures:
        print(f"\n{failures} of {len(tests)} tests failed")
        sys.exit(1)
    print(f"\nAll {len(tests)} tests passed")
