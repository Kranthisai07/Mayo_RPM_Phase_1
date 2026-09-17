# Mayo RPM Phase 1

Remote Patient Monitoring (RPM) system with:

- FastAPI backend for auth, patient/nurse/admin workflows, vitals, alerts, and assignments
- Expo React Native frontend (web/mobile dev flow) for role-based dashboards

## Getting Started (new collaborator)

These steps assume a fresh clone on macOS — the same steps work on Windows using the PowerShell commands noted in each section below.

```bash
git clone git@github.com:Kranthisai07/Mayo_RPM_Phase_1.git
cd Mayo_RPM_Phase_1
```

1. **Read [`PROJECT_AUDIT.md`](PROJECT_AUDIT.md) first** — it's the current, accurate picture of what's implemented, what's broken, and what's still missing. Saves re-discovering things that are already known issues.
2. **Backend**: follow [Start The Backend](#start-the-backend) below — SQLite by default, no database server to install.
3. **Frontend**: follow [Start The Frontend](#start-the-frontend) below, and set your own `EXPO_PUBLIC_API_URL` (see that section) before testing on a phone.
4. Demo login credentials, once you've run `python seed_demo_users.py` against your own local database: `admin@example.com` / `AdminPass123`, `nurse@example.com` / `Nurse123`, `patient@example.com` / `Patient123`.
5. Work on a feature branch, open a PR against `main` — don't push directly to `main`.

`ROADMAP.md` and `CLAUDE.md` are referenced in `PROJECT_AUDIT.md`'s plan but haven't been written yet — check with Kranthi before assuming project conventions not documented here.

## Project Structure

- `backend/`: FastAPI app, SQLAlchemy models, routers, services
- `frontend/patient-app/`: Expo app with route groups (`(auth)`, `(admin)`, `(nurse)`, `(patient)`)
- `supplementary_materials/`: reference copy of backend artifacts and docs

## Architecture At A Glance

### Backend (`backend/app/`)

- `main.py`: App bootstrap, CORS config, router registration, startup hooks
- `config.py`: Environment configuration (DB URL, JWT, admin seed credentials)
- `database/database.py`: SQLAlchemy engine/session setup
- `models/`: Database entities (`user`, `vitals`, `alert`, `assignment`, `audit_log`)
- `auth/`: Login/register, token handling, auth dependencies
- `routers/`: API endpoints grouped by domain (`admin`, `nurse`, `patient`, `alerts`, `vitals`)
- `services/`: Business logic (alert generation, assignment, admin seed, audit)

### Frontend (`frontend/patient-app/`)

- `app/`: Expo Router pages and route groups
- `src/api/apiClient.js`: Axios client and auth token injection
- `services/api.js`: Basic fetch helpers for registration/vitals
- `src/features/`: Feature-level service/hooks modules by domain
- `src/auth/`: Auth context/service/token storage and role route mapping

## Prerequisites

- **Python 3.11+** (backend)
- **Node.js 20.19.4+** (Node 22 works), **npm 10+** (frontend). If Node is too old, Expo/Metro may fail with `TypeError: _os.default.availableParallelism is not a function`.
- **No database server required for local dev.** The backend defaults to a local SQLite file (`backend/mayo_app.db`, gitignored). PostgreSQL is only needed if you explicitly set `DATABASE_URL` to a Postgres connection string — see below.
- The AI weight-anomaly service needs `pandas`, `numpy`, and `scikit-learn` (declared in `backend/requirements.txt`). All three ship prebuilt wheels for Windows, Intel macOS, and Apple Silicon macOS — a plain `pip install -r requirements.txt` installs them with no compiler needed on either platform.

## Start The Backend

From `backend/`, create and activate a virtual environment, then install dependencies. Activation differs by platform — everything else is identical:

**Windows (PowerShell):**
```powershell
cd backend
python -m venv app_env
.\app_env\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
cd backend
python3 -m venv app_env
source app_env/bin/activate
pip install -r requirements.txt
```

Then, on either platform:

```bash
export ADMIN_EMAIL="admin@example.com"      # $env:ADMIN_EMAIL="admin@example.com" on PowerShell
export ADMIN_PASSWORD="AdminPass123!"
export ADMIN_NAME="System Admin"
uvicorn app.main:app --reload --port 8000
```

Default API URLs:

- Health/root: http://127.0.0.1:8000/
- Swagger: http://127.0.0.1:8000/docs

On first startup, the backend creates all tables (SQLite file or Postgres, whichever `DATABASE_URL` points at) and seeds the default admin from `ADMIN_EMAIL`/`ADMIN_PASSWORD` if they're set. Run `python seed_demo_users.py` afterward to also create demo nurse/patient accounts (`nurse@example.com` / `Nurse123`, `patient@example.com` / `Patient123`).

### Optional Backend Environment Variables

- `DATABASE_URL` — defaults to `sqlite:///./mayo_app.db`. Set this to a Postgres URL (e.g. `postgresql+psycopg2://user:pass@localhost:5432/mayo_app`) to use Postgres instead; nothing else needs to change.
- `SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`

## Start The Frontend

From repository root:

```bash
cd frontend/patient-app
npm install
npm run web      # or: npx expo start   (for Expo Go / device testing)
```

Frontend dev server URL (web): http://localhost:8081

### API Base URL — one thing every collaborator needs to set individually

`frontend/patient-app/src/api/apiClient.js` reads `process.env.EXPO_PUBLIC_API_URL`, falling back to a hardcoded LAN IP that's specific to whoever last edited that file — **it will not point at your machine.** Before running the app against a real device (Expo Go) or a different machine's backend, set your own:

```bash
# macOS/Linux
export EXPO_PUBLIC_API_URL="http://<your-LAN-IP>:8000"

# Windows PowerShell
$env:EXPO_PUBLIC_API_URL="http://<your-LAN-IP>:8000"
```

Find your LAN IP with `ipconfig` (Windows) or `ifconfig`/`ipconfig getifaddr en0` (macOS). This only matters for testing on a physical device over Wi-Fi — `npm run web` on the same machine as the backend works fine without it (`127.0.0.1` case isn't currently the fallback, so set the env var for web too if you hit connection errors).

`frontend/patient-app/services/api.js` is legacy/unused code (calls a route that no longer exists, `/patient/register`) — safe to ignore or remove, not part of the active app.

## Typical End-To-End Flow

1. Start backend (SQLite, no external DB setup needed)
2. Open backend docs and verify endpoints
3. Start frontend
4. Register/log in users (admin/nurse/patient)
5. Submit vitals
6. Verify generated alerts and assignment workflows

## Troubleshooting

- **Backend port conflict:** find what's using it (`netstat -ano | findstr :8000` on Windows, `lsof -nP -iTCP:8000 -sTCP:LISTEN` on macOS) and either stop it or run uvicorn with a different `--port`. If you change the port, update `EXPO_PUBLIC_API_URL` to match.
- **Frontend cannot call backend / request hangs forever:** almost always the API base URL — see the section above. A silent hang (not an error) with no request ever reaching the backend log is also consistent with a firewall blocking inbound connections to the specific Python executable in `app_env` on a Windows machine set to a "Public" network profile — check Windows Defender Firewall's inbound rules for `app_env\Scripts\python.exe` specifically if this happens.
- **Node version warnings/errors with Expo:** confirm `node -v` is at least `20.19.4`.
- **CORS:** `backend/app/main.py` currently allows all origins (`allow_origins=["*"]`). Combined with `allow_credentials=True` this is invalid per the CORS spec for browser-based requests (`npm run web`) — browsers will reject it. Works fine for the native Expo Go app, which doesn't enforce CORS. Not yet fixed; noted in `PROJECT_AUDIT.md`.
- **`bcrypt`/`passlib` errors:** if you see an error mentioning `bcrypt.__about__`, you have an old `bcrypt` package installed alongside `passlib` — this project already works around it by calling `bcrypt` directly (see `backend/app/auth/utils.py`), so a fresh `pip install -r requirements.txt` should not hit this.

## Project Docs

- [`PROJECT_AUDIT.md`](PROJECT_AUDIT.md) — full repo audit: what's implemented, what's missing, known bugs, security notes. Start here for context on the current state of the app.
- `ROADMAP.md` and `CLAUDE.md` — planned but not yet written.

## Next Improvements (Recommended)

- Add Docker Compose for one-command startup
- Fix the CORS wildcard + credentials combination noted above
- Remove or fix `frontend/patient-app/services/api.js` (dead code, references a nonexistent route)
