"""
The weight-anomaly IsolationForest must train once per distinct CSV
state, not on every call. Verifies:
  1. Repeated calls within a process reuse the in-memory cache (no
     retrain).
  2. Clearing the in-memory cache but leaving the CSV untouched loads
     from the on-disk cache instead of retraining.
  3. Changing the CSV's content invalidates both caches and forces a
     real retrain.

Uses a small synthetic CSV fixture (real code path, not a mock) and
monkeypatches the module's DATA_FILE/CACHE_FILE constants so this
doesn't touch the real dataset or the real cache file.

Standalone script, no test framework required:

    app_env/Scripts/python.exe tests/test_weight_model_caching.py   (Windows)
    app_env/bin/python tests/test_weight_model_caching.py            (macOS/Linux)
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import weight_analysis_service as wa


CSV_HEADER = "Subject,Age,Gender,Date,Weight,Source\n"


def make_csv(path: Path, weights):
    lines = [CSV_HEADER]
    for i, w in enumerate(weights):
        lines.append(f"1,60,F,2026-01-{i + 1:02d},{w},Real\n")
    path.write_text("".join(lines))


def with_isolated_files(fn):
    """Run fn with DATA_FILE/CACHE_FILE pointed at a temp dir, then restore."""
    original_data_file = wa.DATA_FILE
    original_cache_file = wa.CACHE_FILE
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        wa.DATA_FILE = tmp_path / "data.csv"
        wa.CACHE_FILE = tmp_path / ".weight_model_cache.joblib"
        wa._cached_weight_model.cache_clear()
        try:
            fn(tmp_path)
        finally:
            wa.DATA_FILE = original_data_file
            wa.CACHE_FILE = original_cache_file
            wa._cached_weight_model.cache_clear()
    return


def count_real_trainings(fn):
    """Wrap _train_weight_model with a call counter, run fn, return the count."""
    original = wa._train_weight_model
    calls = {"count": 0}

    def counting_wrapper():
        calls["count"] += 1
        return original()

    wa._train_weight_model = counting_wrapper
    try:
        fn()
    finally:
        wa._train_weight_model = original
    return calls["count"]


def test_repeated_calls_train_once():
    def body(tmp_path):
        make_csv(wa.DATA_FILE, [60, 60.5, 61, 61.5, 62, 62.5, 63])

        def do_three_calls():
            wa.create_weight_model()
            wa.create_weight_model()
            wa.create_weight_model()

        trainings = count_real_trainings(do_three_calls)
        assert trainings == 1, f"expected 1 training across 3 calls, got {trainings}"

    with_isolated_files(body)


def test_disk_cache_survives_memory_cache_clear():
    def body(tmp_path):
        make_csv(wa.DATA_FILE, [60, 60.5, 61, 61.5, 62, 62.5, 63])

        wa.create_weight_model()
        assert wa.CACHE_FILE.exists(), "expected a disk cache file to be written"

        # Simulate a fresh process: clear the in-memory cache, CSV unchanged.
        wa._cached_weight_model.cache_clear()

        trainings = count_real_trainings(wa.create_weight_model)
        assert trainings == 0, (
            f"expected 0 retrains after a memory-cache clear with an "
            f"unchanged CSV (should load from disk), got {trainings}"
        )

    with_isolated_files(body)


def test_changed_csv_forces_retrain():
    def body(tmp_path):
        make_csv(wa.DATA_FILE, [60, 60.5, 61, 61.5, 62, 62.5, 63])
        wa.create_weight_model()

        # Change the CSV content (and therefore its fingerprint).
        make_csv(wa.DATA_FILE, [70, 70.5, 71, 71.5, 72, 72.5, 73])

        trainings = count_real_trainings(wa.create_weight_model)
        assert trainings == 1, (
            f"expected exactly 1 retrain after the CSV changed, got {trainings}"
        )

    with_isolated_files(body)


if __name__ == "__main__":
    tests = [
        test_repeated_calls_train_once,
        test_disk_cache_survives_memory_cache_clear,
        test_changed_csv_forces_retrain,
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
