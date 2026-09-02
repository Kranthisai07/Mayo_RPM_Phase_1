RPM Backend README

This project is a FastAPI backend for a Remote Patient Monitoring (RPM) system focused on CHF monitoring workflows.

What This Backend Does

Registers and authenticates admin, nurse, and patient users
Stores patient vitals such as weight and SpO2
Generates alerts for clinically significant weight change and low SpO2
Supports nurse-patient assignment
Allows nurses and patients to view alerts
Allows assigned nurses or patients to acknowledge and resolve alerts
Records audit activity for key actions

Project Structure

app/main.py: FastAPI app entry point
app/config.py: environment-based configuration
app/database/database.py: SQLAlchemy engine and session setup
app/auth/: authentication and authorization logic
app/models/: database models
app/routers/: API endpoints
app/services/: backend business logic
requirements.txt: Python dependencies

Requirements

Python 3.11+ recommended
PostgreSQL running locally if using the default database configuration

Installation

1. Create a virtual environment:

python -m venv app_env

2. Activate it:

.\app_env\Scripts\Activate.ps1

3. Install dependencies:

pip install -r requirements.txt

Environment Variables

Set these before starting the app.

Required for admin login

- ADMIN_EMAIL
- ADMIN_PASSWORD

Optional

- ADMIN_NAME
- DATABASE_URL
- SECRET_KEY
- JWT_ALGORITHM
- ACCESS_TOKEN_EXPIRE_MINUTES

Default database

If DATABASE_URL is not set, the backend uses:

postgresql+psycopg2://postgres:mayo_project%40123@localhost:5432/mayo_app

Example PowerShell Setup

$env:ADMIN_EMAIL="admin@example.com"
$env:ADMIN_PASSWORD="AdminPass123!"
$env:ADMIN_NAME="System Admin"
$env:SECRET_KEY="change-this-secret-key"

If you want to use a different database:

$env:DATABASE_URL="postgresql+psycopg2://username:password@localhost:5432/db_name"

How To Run

Start the API from the project root:

uvicorn app.main:app --reload

The backend will be available at:

- http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs

First Startup Behavior

On startup, the backend:

1. Creates database tables if they do not exist
2. Creates the default admin user if ADMIN_EMAIL and ADMIN_PASSWORD are set

Basic Workflow To Make It Work

1) Start PostgreSQL
2) Set the required environment variables
3) Run the FastAPI server
4) Open Swagger docs at http://127.0.0.1:8000/docs
5) Log in as the admin user using /auth/login
6) Create nurse accounts using /admin/nurses
7) Log in as a nurse and set nurse availability using /nurse/status
8) Register or create patient accounts
9) Submit vitals through /vitals/
10) Review alerts through patient, nurse, or admin endpoints

Main API Groups

Authentication

- POST /auth/register
- POST /auth/login

Patient

- GET /patient/me
- GET /patient/history
- GET /patient/alerts

Nurse

- GET /nurse/dashboard
- PATCH /nurse/status
- GET /nurse/patients
- GET /nurse/patients/{patient_id}
- GET /nurse/alerts

Admin

- GET /admin/dashboard
- POST /admin/nurses
- GET /admin/nurses
- POST /admin/patients
- GET /admin/patients
- GET /admin/assignments
- GET /admin/alerts
- PATCH /admin/patients/{patient_id}/assign-nurse
- DELETE /admin/nurses/{nurse_id}
- DELETE /admin/patients/{patient_id}

Alerts

- GET /alerts/me
- GET /alerts/me/active
- GET /alerts/user/{user_id}
- PUT /alerts/{alert_id}/acknowledge
- PUT /alerts/{alert_id}/resolve

Vitals

- POST /vitals/

Current Alert Rules

- Weight alert: triggered when weight change from the previous reading is greater than 2
- SpO2 alert: triggered when spo2_value < 92

Assignment Behavior

- New patients are assigned to an available nurse if one exists
- If a nurse becomes available later, waiting unassigned patients are auto-assigned
- Admins can manually reassign patients
- If a nurse is deactivated, active patients are reassigned to another available nurse if possible

