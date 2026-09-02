# Mayo RPM Phase 1

Remote Patient Monitoring (RPM) system with:

- FastAPI backend for auth, patient/nurse/admin workflows, vitals, alerts, and assignments
- Expo React Native frontend (web/mobile dev flow) for role-based dashboards

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

## Backend

- Python 3.11+
- PostgreSQL running locally (or provide a custom `DATABASE_URL`)

## Frontend

- Node.js 20.19.4+ (Node 22 works)
- npm 10+

If Node is too old, Expo/Metro may fail with:
`TypeError: _os.default.availableParallelism is not a function`

## Start The Backend

From repository root:

```bash
cd backend
source app_env/bin/activate
export ADMIN_EMAIL="admin@example.com"
export ADMIN_PASSWORD="AdminPass123!"
export ADMIN_NAME="System Admin"
uvicorn app.main:app --reload --port 8001
```

Default API URLs:

- Health/root: http://127.0.0.1:8001/
- Swagger: http://127.0.0.1:8001/docs

Note:

- Port `8000` may already be in use on your machine. Use `--port 8001` (or another free port).

### Optional Backend Environment Variables

- `DATABASE_URL`
- `SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`

If `DATABASE_URL` is not set, backend defaults to:

`postgresql+psycopg2://postgres:mayo_project%40123@localhost:5432/mayo_app`

## Start The Frontend

From repository root:

```bash
cd frontend/patient-app
npm install
npm run web
```

Frontend dev server URL (web):

- http://localhost:8081

### Important API Base URL Note

Frontend currently points to a hardcoded host:

- `frontend/patient-app/src/api/apiClient.js`
- `frontend/patient-app/services/api.js`

Both are set to `http://192.168.1.23:8000`.

If backend runs on `http://127.0.0.1:8001`, update those base URLs accordingly, for example:

- `http://127.0.0.1:8001`

## Typical End-To-End Flow

1. Start PostgreSQL
2. Start backend
3. Open backend docs and verify endpoints
4. Start frontend
5. Register/log in users (admin/nurse/patient)
6. Submit vitals
7. Verify generated alerts and assignment workflows

## Common Commands

```bash
# backend
cd backend
source app_env/bin/activate
uvicorn app.main:app --reload --port 8001

# frontend
cd frontend/patient-app
npm run web
```

## Troubleshooting

- Backend port conflict:
  - `lsof -nP -iTCP:8000 -sTCP:LISTEN`
  - Run backend on another port (for example `8001`).

- Frontend cannot call backend:
  - Ensure backend host/port matches frontend base URL files.

- Node version warnings/errors with Expo:
  - Confirm `node -v` is at least `20.19.4`.

- CORS issues:
  - Backend CORS in `backend/app/main.py` already allows localhost and `:8081` origins.

## Next Improvements (Recommended)

- Move frontend API host into env-based config instead of hardcoding IPs
- Add Docker Compose for one-command startup
- Add seed/demo scripts for test users and vitals
