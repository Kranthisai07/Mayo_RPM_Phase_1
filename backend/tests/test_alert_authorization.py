"""
Safety-critical authorization test: a patient must never be able to
change the status of an alert (acknowledge/resolve), including their
own. Only a nurse assigned to that patient may do so.

Standalone script, no test framework or extra dependency required -
run directly with the backend's own interpreter:

    app_env/Scripts/python.exe tests/test_alert_authorization.py   (Windows)
    app_env/bin/python tests/test_alert_authorization.py            (macOS/Linux)

This is the first test in the repo. There is no pytest/test-runner
setup yet - that is a separate gap (see PROJECT_AUDIT.md), not fixed
by this script.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models import Alert, PatientAssignment, User
from app.services.alert_service import acknowledge_alert_service, resolve_alert_service


def make_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def seed(db):
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
    db.add_all([patient, nurse])
    db.commit()
    db.refresh(patient)
    db.refresh(nurse)

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

    return patient, nurse, alert


def expect_403(fn, *args):
    try:
        fn(*args)
    except HTTPException as exc:
        assert exc.status_code == 403, f"expected 403, got {exc.status_code}"
        return
    raise AssertionError("expected HTTPException(403), but the call succeeded")


def test_patient_cannot_acknowledge_own_alert():
    db = make_session()
    patient, _nurse, alert = seed(db)
    expect_403(acknowledge_alert_service, db, patient.id, "patient", alert.id)


def test_patient_cannot_resolve_own_alert():
    db = make_session()
    patient, _nurse, alert = seed(db)
    expect_403(resolve_alert_service, db, patient.id, "patient", alert.id)


def test_assigned_nurse_can_still_acknowledge():
    db = make_session()
    _patient, nurse, alert = seed(db)
    result = acknowledge_alert_service(db, nurse.id, "nurse", alert.id)
    assert result["message"] == "Alert acknowledged successfully", result


def test_assigned_nurse_can_still_resolve():
    db = make_session()
    _patient, nurse, alert = seed(db)
    result = resolve_alert_service(db, nurse.id, "nurse", alert.id)
    assert result["message"] == "Alert resolved successfully", result


if __name__ == "__main__":
    tests = [
        test_patient_cannot_acknowledge_own_alert,
        test_patient_cannot_resolve_own_alert,
        test_assigned_nurse_can_still_acknowledge,
        test_assigned_nurse_can_still_resolve,
    ]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL: {test.__name__}: {e}")

    if failures:
        print(f"\n{failures} of {len(tests)} tests failed")
        sys.exit(1)
    print(f"\nAll {len(tests)} tests passed")
