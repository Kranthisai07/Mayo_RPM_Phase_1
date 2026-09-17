# Project Audit — Mayo RPM Phase 1

**Date:** 2026-09-01
**Scope:** Phase 0 (repository audit) + Phase 0.5 (reviewer-gap cross-check) per master prompt. No code was changed to produce this document.

> **Note on Phase 0.5 inputs:** `/docs/reference/rpm_paper_draft.docx` and `/docs/reference/reviewer_comments.docx` are not present anywhere in the repo or in `d:\RPM`, and no reviewer text was pasted into the prompt despite the reference to it. The gap checklist below was assessed against the **eight specific questions the master prompt itself listed**, using repo evidence — not against the original reviews or draft, which I have not seen. Upload the two files and I'll re-run this section against the actual reviewer language.

---

## 1. Tech Stack Summary

| Layer | Technology | Notes |
|---|---|---|
| Backend | FastAPI 0.135.1 (`backend/app`) | Python 3.13 in practice (3.11+ required) |
| ORM / DB | SQLAlchemy 2.0 + PostgreSQL (`psycopg2-binary`) | Default DB URL has a hardcoded password fallback (see §6) |
| Auth | Custom JWT (`python-jose`) + `passlib`/`bcrypt`, `HTTPBearer` | SHA-256 pre-hash before bcrypt (defensible, not a defect) |
| AI/ML | **scikit-learn `IsolationForest`** (`backend/app/services/weight_analysis_service.py`) | Trains on a static CSV, not declared in `requirements.txt` (see §5, §6) |
| Frontend | Expo / React Native (`frontend/patient-app`), Expo Router, TypeScript for screens, JS for services | Expo SDK 54, React 19, RN 0.81.5 |
| HTTP client | Axios (`src/api/apiClient.js`) | One competing legacy `fetch`-based client is dead code (see §5) |
| Local state | AsyncStorage (session/token only) | React Context (`authContext.js`) exists but is **never mounted** — dead code |
| Tests | **None** | No test files anywhere in `backend/` or `frontend/` (only vendored tests inside installed packages) |
| CI/CD | **None** | No `.github/workflows`, no other CI config |
| Data | `backend/data/RPM_combined_100_patients.csv` — 1,420 rows, columns `Subject, Age, Gender, Date, Weight, Source`; 335 rows `Source=Real`, 1,085 `Source=Synthetic` | Identical to the CSV sitting at the `d:\RPM` root |

Three roles exist end-to-end: **patient**, **nurse**, **admin** — auth, routing, and DB all agree on exactly these three (no `physician` role anywhere in code).

---

## 2. Current State by Feature Area

### Auth
**Working.** Register (patient-only, public), login, JWT issue/verify, `require_role()` dependency, per-request active-user check. Public `/auth/register` cannot mint nurse/admin accounts — nurses/admins are created only by an existing admin or the startup-seeded default admin. Frontend login/register screens are complete and wired correctly.

### Patient logging
**Working.** `POST /vitals/` records weight + SpO2, runs rule-based alerting inline, returns the record. Frontend `Vitals` and `History` screens are built, validated client-side (weight 0–1000 kg, SpO2 70–100%) and server-side (Pydantic `Field` constraints match).

### Nurse dashboard
**Working, more complete than expected.** Dashboard (assigned-patient count, active-alert count), assigned-patient list, per-patient detail (vitals history + active alerts + **AI weight-monitoring display**), acknowledge/resolve actions, availability toggle. This directly answers the rejected paper's "no frontend" criticism — a working nurse UI exists now.

### Admin panel
**Mostly working, one real gap.** Dashboard counts, nurse CRUD (create/deactivate), patient CRUD, manual reassignment. **Admin cannot view or act on individual alerts anywhere in the UI**, and the backend explicitly blocks admin from acknowledging/resolving alerts (`alert_service.py::_get_manageable_alert` raises 403 for any role other than `patient`/`nurse`). Admin's only alert visibility is the aggregate count on the dashboard.

### Alerting
**Rule-based only, and this is the central finding of the whole audit — see §3.**

---

## 3. The AI Question — What Actually Exists Today

The master prompt's Phase 0.5 item #8 assumes the system is "rule-based only (no AI yet)." **That's not quite right.** There is a real, working AI component already in the repo:

- `backend/app/services/weight_analysis_service.py` (~600 lines): builds a longitudinal weight-feature pipeline (day-over-day change, rolling personal baseline, 7-day change, deviation z-score) and fits a scikit-learn `IsolationForest` anomaly detector on the **335 `Source=Real` rows** of the CSV dataset (correctly excludes synthetic rows from training — good practice worth keeping for the paper).
- Exposed via `GET /vitals/weight-ai/{patient_id}` (nurse/admin only), and **fully rendered in the nurse's patient-detail screen** — monitoring status badge (normal/watch/high), plain-language reason text, baseline/deviation/7-day metrics.

So the honest framing for the paper is not "we added AI where there was none" — it's:

> **A weight-anomaly detection model exists and is displayed to nurses, but it is disconnected from the alert/escalation pipeline, is SpO2-blind, and has architectural problems that block reliable use.** The paper's genuine contribution is closing that loop.

Specifically, this AI component does **not**:
- Generate `Alert` rows, so it never appears in alert counts, nurse "active alerts," or the escalation flow described below — it is a manual "check this dashboard" signal, not a push alert.
- Cover SpO2 at all (only weight).
- Get evaluated against ground truth in any documented way (no held-out set, no precision/recall reported anywhere in the repo).

And it has two concrete engineering defects:
1. ~~**Retrains from scratch on every single API call.**~~ — **Fixed (2026-09-17).** `create_weight_model()` now checks an in-memory cache, then a disk cache (`backend/data/.weight_model_cache.joblib`, gitignored), keyed to a fingerprint of `RPM_combined_100_patients.csv`'s mtime+size. Only retrains if that fingerprint changes. Verified live against the real dataset: cold train ~1.8s, cached in-process ~0.06s, cached-on-disk-after-restart ~0.2s. Tested in `backend/tests/test_weight_model_caching.py` (synthetic CSV fixture, RED/GREEN, 3 tests: repeat-calls-train-once, disk-cache-survives-memory-clear, changed-CSV-forces-retrain). Deliberately did not add a scheduled/admin-triggered retrain mechanism — the model only ever trains against this static file, which doesn't change while the server runs, so there's nothing for a scheduled job to react to yet. That becomes relevant only if the training source moves to the live `Vitals` table, which is a separate, larger decision not yet made.
2. **Its dependencies are not installed in the documented environment.** See §6 — this route currently throws `ModuleNotFoundError` if you follow the backend README exactly.

> **Scope decision (2026-09-15): weight-only, by choice, not by omission.** Confirmed SpO2 cannot be added to this model with the data currently available: `backend/data/RPM_combined_100_patients.csv` — the actual training source — has no SpO2 column at all (`Subject,Age,Gender,Date,Weight,Source`), and while the live `Vitals` table does capture `spo2_value` on every real submission, it doesn't yet hold enough longitudinal history to train against. The current anomaly-detection model operates on weight data only; SpO2 integration is identified as future work pending accumulation of sufficient longitudinal SpO2 data through clinical use. State this explicitly in the paper as a scoped limitation, not an oversight.

---

## 4. Reviewer Gap Status (Phase 0.5 checklist)

| # | Reviewer concern | Status | Evidence |
|---|---|---|---|
| 1 | Escalation pathway after nurse acknowledges | **Partially addressed** | The assigned nurse can now flag an alert as escalated (`is_escalated`/`escalated_at` on `Alert`, `PUT /alerts/{id}/escalate`, verified at the API layer — 403 for anyone but the assigned nurse; tested in `backend/tests/test_alert_escalation.py`, live-verified end-to-end 2026-09-17). Reviewed and confirmed working in the nurse UI (alerts list + patient-detail screen). Still open: nothing *consumes* the flag yet — no admin capability change, no timeout/re-notify logic, no physician role (none exists in this codebase). Deciding who acts on an escalated alert is a deliberately separate decision, not yet made. |
| 2 | Nurse availability edge case (stale/unexpected unavailability) | **Not addressed** | `User.is_available` is a bare boolean with no timestamp — no way to detect a nurse who went unavailable without updating status (app crash, phone died). Unassigned patients (no nurse ever available) generate alerts that are invisible to *every* nurse (`get_alerts_for_nurse` joins on `PatientAssignment`) and admin cannot act on alerts either (see #3 above) — so an alert can exist with literally no one able to act on it. |
| 3 | Clinical admin vs IT admin separation | **Not addressed** | Single `role="admin"` string; one admin scope sees and can do everything (user management, all patient data, dashboard). No sub-role or scoped permission model. |
| 4 | PII/PHI access control + logging | **Partially addressed** | `AuditLog` exists and is written on most sensitive actions (nurse-views-patient, alert ack/resolve, admin CRUD, vitals submission). Per-nurse access is correctly scoped to assigned patients (`is_patient_assigned_to_nurse` check, 403 otherwise). Gap: **a patient can acknowledge and resolve their own alerts**, including a `critical` SpO2 alert (`_get_manageable_alert` allows `actor_role == "patient"` when `alert.patient_id == actor_user_id`), which lets a patient silently clear a safety signal out of the nurse's active-alert view with no second check. This is worth flagging to the clinic explicitly — it reads as unintentional rather than a deliberate design choice. |
| 5 | Device integration (hospital vs. patient's own phone) | **Not addressed** | No device model, no device metadata on `Vitals`, no distinction anywhere in the data model. |
| 6 | Alert scope beyond weight + SpO2 | **Not addressed** | `Vitals` model has exactly two fields: `weight_value`, `spo2_value`. Still weight + SpO2 only, same as the rejected draft. |
| 7 | Code documentation for a new contributor | **Partially addressed** | Root `README.md` and `backend/README.txt` are both good and mostly accurate, but have drifted from the actual code (see §6) and there's real dead code left in the tree with no explanation (`backend/app/routers/roles/`, `services/api.js`, `authContext.js`) that would confuse a new contributor. No docstrings/comments in most backend service files except `weight_analysis_service.py`, which is well-commented. |
| 8 | AI/ML component — rule-based only? | **Partially true, correct as clarified in §3** | Rule-based alert generation is real and is what drives the actual alert pipeline today. A separate, working but disconnected AI anomaly-detection component also already exists for weight. |

---

## 5. Code Quality / Cleanup Findings

- **Dead code, safe to delete:**
  - `backend/app/routers/roles/` — an earlier draft of patient/nurse/admin routers, not imported by `main.py`, fully superseded by `backend/app/routers/{patient,nurse,admin}.py`.
  - `backend/seed_demo_users.pyes` — near-duplicate of `seed_demo_users.py` (1-line diff).
  - `frontend/patient-app/services/api.js` — legacy fetch-based client. Calls `/patient/register`, a route that **does not exist** in the backend (real route is `/auth/register`), and never attaches the auth Bearer token, so its `submitVitals` call would 401 against the real API. Not imported by any current screen.
  - `frontend/patient-app/src/auth/authContext.js` — defines `AuthProvider`/`AuthContext`, never mounted anywhere in the component tree (`app/_layout.tsx` is a bare `<Stack>`). Session state actually flows through direct `AsyncStorage` reads in `app/index.tsx` and each screen.
  - `frontend/patient-app/src/features/vitals/vitalsHooks.js` and `src/features/chat/chatService.js` — empty stub files. Chat between nurse/patient appears to have been planned and abandoned/not started.
  - Five stray empty files at `backend/--access-log`, `--host`, `--log-level`, `--port`, `--reload` — artifacts of a `uvicorn` command whose flags got parsed as filenames. Harmless, untracked, but should be deleted before committing anything from that directory.
- **Two virtual environments, neither fully matches the README:** `backend/app_env` (the one the README documents) is a real, populated Python 3.13 venv but is missing pandas/scikit-learn/numpy. A second venv at the repo root, `mayo_rpm_phase1/.venv`, was created by `uv` on **macOS** (`pyvenv.cfg` points at `/Library/Frameworks/Python.framework/...`) and has pandas/numpy/scikit-learn installed — it's not usable on this Windows machine as-is, and isn't referenced by either README.
- **Two READMEs disagree with each other and with the code:** root `README.md` says `source app_env/bin/activate` (Unix); `backend/README.txt` says `.\app_env\Scripts\Activate.ps1` (Windows) — the actual venv has a Unix `bin/` layout, so the Windows instructions in `backend/README.txt` would fail as written. Root README also references a stale hardcoded LAN IP (`192.168.1.23:8000`) in `apiClient.js`/`services/api.js` that no longer matches the current file contents (`127.0.0.1:8000`).

---

## 6. Risk Flags

**Security / data handling:**
- `config.py` default `DATABASE_URL` embeds a plaintext password (`mayo_project%40123`) as a fallback, and `JWT_SECRET_KEY` defaults to the literal string `"change-this-secret-key"`. Neither is a problem if env vars are always set in real deployments, but both are landmines if anyone runs this without setting them — worth a startup check that refuses to boot with the JWT default in a non-debug mode.
- ~~**Patient can acknowledge/resolve their own critical alerts**~~ — **Fixed.** `_get_manageable_alert()` no longer has a patient branch; patients now get 403 on both endpoints regardless of ownership, same as admin. Covered by `backend/tests/test_alert_authorization.py` (RED/GREEN, first test in the repo).
- No rate limiting on `/auth/login` — brute-force is unmitigated, minor but worth a line in the paper's limitations if you discuss security posture.
- No `.env` files are committed (good), but there's also no `.env.example`, so a new contributor has to reverse-engineer required variables from two READMEs.

**Deployment blockers:**
- ~~`backend/requirements.txt` and `requirements-mac.txt` are both **UTF-16 encoded**~~ — **Fixed.** Re-saved as UTF-8, `requirements-mac.txt` removed (it was a byte-identical duplicate, not actually macOS-specific). Verified against PyPI that every pinned package, including the AI dependencies below, publishes wheels for Windows, Intel macOS, and Apple Silicon macOS.
- ~~`requirements.txt` does not list `pandas`, `numpy`, or `scikit-learn`~~ — **Fixed.** All three (plus `scipy`) are now pinned in `requirements.txt`.
- No CI, no tests of any kind. For a CCWC Work-in-Progress paper this is acceptable to disclose as a limitation, but any "evaluation" claim in the paper needs to rest on something more than "it ran during development."
- Nothing in the repo addresses app-store requirements (privacy policy hooks, permission manifests, data-handling disclosures) — expected, since mobile packaging is explicitly Phase 2 in your own roadmap, not blocking the paper.

---

## 7. Gap List — What's Needed for "AI-Driven Alerts + Good UI"

Ranked by what actually changes the paper's story, not by difficulty:

1. **Wire the existing AI signal into the alert pipeline.** Today it's a read-only nurse-dashboard widget; it needs to produce `Alert` rows (or a new `ai_flag` alongside rule-based alerts) so "AI-driven alerts" is literally true, not just "AI-informed dashboard."
2. ~~**Fix the retrain-per-request architecture**~~ — **Fixed.** In-memory + disk-persisted cache, invalidated only when the source CSV actually changes. See §3.
3. ~~**Add SpO2 to the AI scope**~~ — **Decided (2026-09-15): weight-only, Option A.** Confirmed not viable to extend right now: the training CSV has no SpO2 column, and the live `Vitals` table doesn't yet hold enough longitudinal SpO2 history. Documented as a stated limitation, future work pending clinical-use data accumulation — see §3.
4. **Close the escalation gap** (reviewer item #1) — **Partially done.** Manual nurse-triggered escalation flag shipped and reviewed working (see §4, item 1). Still open, and higher-leverage than the flag itself: nothing consumes `is_escalated` yet (no admin capability, no timeout-based auto-escalation) — that's the part that actually addresses reviewer item #2 (nurse-unavailable edge case) too, and needs its own explicit design decision before implementing.
5. ~~**Decide the patient-self-resolve question explicitly**~~ — **Fixed.** Server-side restriction, not just a design note. See §6.
6. **Fix the environment/requirements issues in §6** before doing any live demo for the paper. **Fixed** — see §6.
7. Everything else in §5 is cleanup, not scope — worth doing but shouldn't consume roadmap time before the above.

---

## 8. CCWC 2027 Fit Assessment

**Realistic for a 6-page Short/WIP paper by Nov 6:**
- Items 1–4 above (AI-driven alert generation, fixed architecture, explicit scope statement, basic escalation) are scoped correctly for "interim/preliminary results" — this is exactly what the Work-in-Progress category exists for, and matches your stated reasoning for choosing it.
- A working three-role demo (already mostly true today) directly answers the "no frontend, no deployment" rejection reason.
- A small, honestly-reported evaluation on the 335 real longitudinal weight observations (not claiming clinical validation, just anomaly-detection behavior on retrospective data) is a legitimate WIP-paper contribution.
- The novelty argument becomes concrete and specific: role-based RPM system + anomaly-detection-driven (not just threshold-driven) alerting + working escalation state machine, evaluated end-to-end on synthetic + limited real data — that's a defensible "vs. existing RPM systems" story the original draft apparently lacked.

**Out of scope for Nov 6, and should be stated as such in the paper's limitations rather than attempted:**
- Any claim of clinical validation or outcome improvement — you have no patient-outcome data and no IRB-scale evaluation.
- Full device-integration story (reviewer item #5) — document as future work.
- Admin role separation (reviewer item #3) — a real gap but low-risk to defer; note as future work rather than building it under deadline pressure.
- Mobile store packaging — already correctly sequenced as Phase 2 after the paper in your own plan.

**Self-plagiarism risk:** I have not seen the original draft (see note at top), so I can't yet diff language. Once you upload `rpm_paper_draft.docx`, flag it back to me and I'll do a section-by-section comparison before any paper drafting starts, per your standing instruction.

---

## Summary Table

| Area | State |
|---|---|
| Auth | ✅ Working |
| Patient logging + UI | ✅ Working |
| Nurse dashboard + UI | ✅ Working (more complete than the rejection implies) |
| Admin panel + UI | ⚠️ Working except alert visibility/action |
| Rule-based alerts | ✅ Working |
| AI weight anomaly detection | ⚠️ Exists, works, deps fixed, caching fixed — still disconnected from the alert pipeline |
| AI scope (SpO2) | ✅ Decided — weight-only, documented as a stated limitation |
| Patient self-resolve authorization | ✅ Fixed |
| Escalation pathway | ⚠️ Nurse can flag as escalated (reviewed, working) — no consumer yet |
| Nurse-unavailable edge case | ❌ Missing |
| Admin role separation | ❌ Missing |
| Device integration | ❌ Missing |
| Alert scope beyond weight/SpO2 | ❌ Missing |
| Tests / CI | ⚠️ One test exists (alert authorization); no runner/CI setup yet |
| Deployment readiness | ✅ requirements.txt + AI deps fixed; CORS wildcard+credentials still open |
