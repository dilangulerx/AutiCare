# 🧩 AutiCare — Autism Development Tracker

**A full-stack web application for tracking the daily behavioral development of children with Autism Spectrum Disorder (ASD).**

[https://vercel.com/dilangulerxs-projects/auti-care](https://vercel.com/dilangulerxs-projects/auti-care)

---

## 🌱 About the Project

AutiCare helps parents and caregivers of children with ASD to:

- **Record** daily behavioral metrics (eye contact, communication, aggression, sleep)
- **Visualize** weekly trends through summary cards and progress bars
- **Generate** AI-powered weekly development reports using GPT-4
- **Manage** medication, therapy, and activity reminders with email notifications
- **Track** multiple children under a single account

> ⚕️ AutiCare does not provide medical diagnoses. It is designed solely to help parents track their child's development and is intended as a supplementary tool alongside professional care.

---

## ✨ Features


| Feature                     | Description                                                  |
| --------------------------- | ------------------------------------------------------------ |
| 🔐 **Secure Auth**          | JWT-based login & registration with bcrypt password hashing  |
| 👶 **Multi-child Profiles** | Manage multiple children under one account                   |
| 📝 **Daily Log**            | Slider-based metric entry for 4 behavioral dimensions        |
| 🤖 **AI Weekly Reports**    | GPT-4 generated reports with insights & recommendations      |
| 🔔 **Smart Reminders**      | Medication, therapy & activity reminders with email delivery |
| ⚙️ **User Settings**        | Update name, email, phone, password + dark mode toggle       |
| 📊 **Overview Dashboard**   | Summary cards, trend averages, recent log & report preview   |


---

## 🛠 Tech Stack

### Backend

- **[FastAPI](https://fastapi.tiangolo.com/)** — Modern Python web framework with auto OpenAPI docs
- **[SQLAlchemy](https://www.sqlalchemy.org/)** — ORM for database interactions
- **[MySQL 8.0](https://www.mysql.com/)** — Relational database
- **[Python-Jose](https://github.com/mpdavis/python-jose)** — JWT token management
- **[bcrypt](https://github.com/pyca/bcrypt/)** — Password hashing
- **[OpenAI Python SDK](https://github.com/openai/openai-python)** — GPT-4 weekly report generation
- **[Resend](https://resend.com/)** — Transactional email delivery
- **[APScheduler](https://apscheduler.readthedocs.io/)** — Scheduled reminder jobs

### Frontend

- **[React 18](https://react.dev/)** + **[Vite](https://vitejs.dev/)** — Fast development environment
- **[TypeScript](https://www.typescriptlang.org/)** — Static type safety
- **[React Router DOM](https://reactrouter.com/)** — Client-side routing
- **[Axios](https://axios-http.com/)** — HTTP client with JWT interceptor
- **[Tailwind CSS v4](https://tailwindcss.com/)** — Utility-first styling

### Infrastructure

- **[Docker](https://www.docker.com/)** + **[Docker Compose](https://docs.docker.com/compose/)** — Containerized services

---

## 📁 Project Structure

```
autism-tracker/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── database.py             # DB connection & session
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── child.py
│   │   │   ├── daily_log.py
│   │   │   ├── weekly_report.py
│   │   │   └── reminder.py
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── routers/                # API route handlers
│   │   │   ├── auth.py
│   │   │   ├── children.py
│   │   │   ├── daily_logs.py
│   │   │   ├── weekly_reports.py
│   │   │   └── reminders.py
│   │   └── services/               # Business logic
│   │       ├── auth.py             # JWT + bcrypt
│   │       ├── ai_report.py        # OpenAI integration
│   │       ├── email.py            # Resend email service
│   │       └── scheduler.py        # APScheduler jobs
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/                    # Axios API clients
│   │   │   ├── client.ts           # Base Axios instance
│   │   │   ├── children.ts
│   │   │   ├── logs.ts
│   │   │   ├── reports.ts
│   │   │   └── reminders.ts
│   │   ├── components/
│   │   │   └── AutiCareLogo.tsx    # Logo component
│   │   ├── context/
│   │   │   └── AuthContext.tsx     # Global auth state
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   └── Dashboard.tsx       # Main app screen
│   │   ├── assets/
│   │   │   └── logo.png
│   │   └── App.tsx                 # Router + PrivateRoute
│   ├── index.css
│   ├── vite.config.ts
│   └── package.json
│ 
├── docker-compose.yml
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [Node.js 18+](https://nodejs.org/) (for frontend)
- Git

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/autism-tracker.git
cd autism-tracker
```

### 2. Create environment file

```bash
cp .env.example .env


### 3. Start backend & database

```bash
docker-compose up -d
```

This starts:

- `autism_backend` on **[http://localhost:8000](http://localhost:8000)**
- `autism_db` (MySQL) on **localhost:3307**

### 4. Install frontend dependencies & start

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on **[http://localhost:5173](http://localhost:5173)**

### 5. Verify everything is running

```bash
# Check backend
curl http://localhost:8000

# View API docs
open http://localhost:8000/docs
```

---

## 🔐 Environment Variables

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=mysql+pymysql://root:rootpassword@db:3306/autism_tracker

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production

# OpenAI (required for AI reports)
OPENAI_API_KEY=sk-...

# Resend (required for email reminders)
RESEND_API_KEY=re_...
```

---

## 📡 API Reference

Full interactive documentation available at **[http://localhost:8000/docs](http://localhost:8000/docs)** (Swagger UI).

### Authentication


| Method | Endpoint         | Description                         |
| ------ | ---------------- | ----------------------------------- |
| `POST` | `/auth/register` | Create new account                  |
| `POST` | `/auth/login`    | Login → returns JWT token           |
| `GET`  | `/auth/me`       | Get current user info               |
| `PUT`  | `/auth/me`       | Update name, email, phone, password |


### Children


| Method   | Endpoint         | Description                        |
| -------- | ---------------- | ---------------------------------- |
| `GET`    | `/children`      | List all children for current user |
| `POST`   | `/children`      | Create child profile               |
| `PUT`    | `/children/{id}` | Update child profile               |
| `DELETE` | `/children/{id}` | Delete child profile               |


### Daily Logs


| Method   | Endpoint           | Description              |
| -------- | ------------------ | ------------------------ |
| `GET`    | `/logs/child/{id}` | Get all logs for a child |
| `POST`   | `/logs`            | Create new daily log     |
| `PUT`    | `/logs/{id}`       | Update log               |
| `DELETE` | `/logs/{id}`       | Delete log               |


### Weekly Reports


| Method | Endpoint                 | Description                                         |
| ------ | ------------------------ | --------------------------------------------------- |
| `GET`  | `/reports/child/{id}`    | List reports for a child                            |
| `POST` | `/reports/generate/{id}` | Generate AI report (query: `week_start=YYYY-MM-DD`) |


### Reminders


| Method   | Endpoint                | Description                |
| -------- | ----------------------- | -------------------------- |
| `GET`    | `/reminders/child/{id}` | List reminders for a child |
| `POST`   | `/reminders`            | Create reminder            |
| `PUT`    | `/reminders/{id}`       | Update reminder            |
| `DELETE` | `/reminders/{id}`       | Delete reminder            |


---

## 🤖 AI Agent Planning

This project includes a planning document for the future integration of a **Conversational Advisor Agent** that will:

- Answer parent questions about their child's behavioral trends in real-time
- Detect anomalies when metrics deviate significantly from personal baseline
- Suggest daily activities based on recent behavioral patterns
- Generate structured therapy briefs for professional consultations

### Planned Architecture

```
Frontend Chat Panel
        │
        ▼
POST /agent/chat  (new FastAPI endpoint)
        │
        ├── Context Builder (fetches last 14 days of logs from DB)
        │
        ├── OpenAI GPT-4 (system prompt + conversation history)
        │
        └── Streaming response back to frontend
```

---

## 🗄️ Database Schema

```
users          → id, email, name, phone, hashed_password, role
children       → id, user_id*, name, birth_date, notes
daily_logs     → id, child_id*, date, eye_contact, communication_score,
                 aggression_level, sleep_hours, notes
weekly_reports → id, child_id*, week_start_date, report_text,
                 key_insights (JSON), recommendations (JSON)
reminders      → id, child_id*, title, reminder_type, remind_at,
                 recur_type, is_active
```

---

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Restart backend only
docker-compose restart backend

# Stop all services
docker-compose down

# Connect to database
docker exec -it autism_db mysql -u root -prootpassword autism_tracker
```

---

## ⚠️ Disclaimer

AutiCare is **not** a medical application. It does not provide clinical diagnoses or replace professional medical advice. All AI-generated reports are informational only and should be reviewed with a qualified healthcare provider.

---

