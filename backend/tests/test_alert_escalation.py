"""
Alert escalation: a nurse assigned to a patient can flag an alert as
escalated (is_escalated + escalated_at), independent of its
acknowledged/resolved status. Only the assigned nurse can escalate -
same authorization boundary as acknowledge/resolve. Patients can never
escalate.

This phase does not add any new consumer of the escalated flag (no
admin capability change) - it is a visibility/priority signal only,
by design (see PROJECT_AUDIT.md).

Standalone script, no test framework required:

    app_env/Scripts/python.exe tests/test_alert_escalation.py   (Windows)
    app_env/bin/python tests/test_alert_escalation.py            (macOS/Linux)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models import Alert, PatientAssignment, User
from app.services.alert_service import escalate_alert_service


def make_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def seed(db, assign_nurse=True):
    patient = User(
        name="Test Patient",
        email="patient@test.local",
        password_hash="x",
        role="patient",
        is_active=True,
    )
    nurse = User(
        name="Test Nurse",
        email="nurse@test.local",
        password_hash="x",
        role="nurse",
        is_active=True,
        is_available=True,
    )
    other_nurse = User(
        name="Other Nurse",
        email="other-nurse@test.local",
        password_hash="x",
        role="nurse",
        is_active=True,
        is_available=True,
    )
    db.add_all([patient, nurse, other_nurse])
    db.commit()
    db.refresh(patient)
    db.refresh(nurse)
    db.refresh(other_nurse)

    if assign_nurse:
        db.add(PatientAssignment(patient_id=patient.id, nurse_id=nurse.id, is_active=True))

    alert = Alert(
        patient_id=patient.id,
        alert_type="spo2",
        severity="critical",
        message="Low oxygen saturation detected",
        status="active",
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    return patient, nurse, other_nurse, alert


def expect_403(fn, *args):
    try:
        fn(*args)
    except HTTPException as exc:
        assert exc.status_code == 403, f"expected 403, got {exc.status_code}"
        return
    raise AssertionError("expected HTTPException(403), but the call succeeded")


def test_patient_cannot_escalate_alert():
    db = make_session()
    patient, _nurse, _other, alert = seed(db)
    expect_403(escalate_alert_service, db, patient.id, "patient", alert.id)


def test_unassigned_nurse_cannot_escalate():
    db = make_session()
    _patient, _nurse, other_nurse, alert = seed(db)
    expect_403(escalate_alert_service, db, other_nurse.id, "nurse", alert.id)


def test_assigned_nurse_can_escalate():
    db = make_session()
    _patient, nurse, _other, alert = seed(db)

    result = escalate_alert_service(db, nurse.id, "nurse", alert.id)
    assert result["message"] == "Alert escalated successfully", result

    db.refresh(alert)
    assert alert.is_escalated is True, "is_escalated should be True after escalation"
    assert alert.escalated_at is not None, "escalated_at should be set after escalation"


def test_escalating_twice_is_idempotent():
    db = make_session()
    _patient, nurse, _other, alert = seed(db)

    escalate_alert_service(db, nurse.id, "nurse", alert.id)
    result = escalate_alert_service(db, nurse.id, "nurse", alert.id)
    assert result["message"] == "Alert already escalated", result


def test_escalation_is_independent_of_acknowledged_status():
    """Escalating does not change status - it's an orthogonal flag."""
    db = make_session()
    _patient, nurse, _other, alert = seed(db)

    escalate_alert_service(db, nurse.id, "nurse", alert.id)
    db.refresh(alert)
    assert alert.status == "active", "escalating must not change alert.status"


if __name__ == "__main__":
    tests = [
        test_patient_cannot_escalate_alert,
        test_unassigned_nurse_cannot_escalate,
        test_assigned_nurse_can_escalate,
        test_escalating_twice_is_idempotent,
        test_escalation_is_independent_of_acknowledged_status,
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
