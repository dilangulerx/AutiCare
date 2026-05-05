# AutiCare - Autism Development Tracker

AutiCare is a full-stack platform designed to track daily developmental signals of children with Autism Spectrum Disorder (ASD), support caregivers, and provide AI-assisted insights.

Live preview: [Vercel App](https://vercel.com/dilangulerxs-projects/auti-care)

---

## Project Overview

With AutiCare, parents and caregivers can:

- Record child-specific daily behavior logs (eye contact, communication, aggression, sleep)
- Track development trends over time
- Generate AI-powered weekly reports
- Detect potential anomalies
- Manage reminders
- Receive richer support through AI chat and expert-oriented agent workflows

> Note: This application does not provide medical diagnosis and does not replace clinical judgment.

---

## Features

### Core Application Features

- JWT-based authentication and authorization
- Multi-child profile management
- Create/update/delete daily behavior logs
- AI-generated weekly report generation
- Email-enabled reminders
- Dashboard summary cards and trend views

### Agentic AI Features (LangGraph + CrewAI)

- Dynamic routing (different execution paths based on task type)
- Search-enhanced knowledge collection step
- Human-in-the-Loop (HITL) review flow
- Checkpointing and workflow resume support
- Crew-based multi-agent task orchestration
- Monitoring and performance metrics (LangSmith-ready integration)

---

## Tech Stack

### Frontend

- React 18
- TypeScript
- Vite
- React Router DOM
- Axios
- Tailwind CSS

### Backend

- FastAPI
- SQLAlchemy
- MySQL
- APScheduler
- Python-Jose + bcrypt
- OpenAI SDK
- CrewAI
- LangGraph
- LangChain / LangChain OpenAI
- LangSmith

### DevOps & Infrastructure

- Docker + Docker Compose
- Cloud Build (`cloudbuild.yaml`)
- Google Cloud Run deployment flow

---

## Agent and Workflow Architecture

The AI layer uses a hybrid architecture:

1. **LangGraph** handles workflow orchestration and route decisions
2. **CrewAI** delegates specialized tasks to domain agents
3. **HITL** is used for critical outputs requiring human review
4. After approval/rejection, the workflow resumes from checkpoint

### LangGraph Flow (Summary)

`analyze_intent -> (search_information or prepare_crew_tasks) -> execute_crew_tasks -> process_analysis -> (human_review or generate_output) -> END`

Key capabilities:

- Task-driven dynamic routing (`report`, `chat`, `anomaly`, `analysis`, `deep_analysis`, `literature_review`, `parent_support`)
- `interrupt_before=["human_review"]` for critical output gating
- Checkpoint resume via workflow `thread_id`

### CrewAI Agents

- `BehavioralAnalystAgent`: behavior trend analysis
- `AnomalyDetectorAgent`: anomaly and deviation detection
- `TherapyAdvisorAgent`: therapy/activity recommendations
- `ReportGeneratorAgent`: weekly report synthesis
- `ConversationalAgent`: parent-facing Q&A support
- `LiteratureReviewAgent`: up-to-date academic evidence search
- `ParentSupportAgent`: empathetic parent guidance
- `DataAnalystAgent`: advanced correlation and deep data analysis

### Crew Types

- `analysis`
- `anomaly`
- `recommendations`
- `report`
- `chat`
- `deep_analysis`
- `literature_review`
- `parent_support`

---

## MCP + Streaming Chat Architecture (Implemented)

AutiCare now includes an MCP integration layer that can be used in two modes:

1. **HTTP bridge mode (inside FastAPI)** for app/frontend usage
2. **Native MCP stdio mode** for external MCP-capable agent runtimes

### What Was Added

- `backend/app/services/mcp_server.py`
  - `AutiCareMCPBridge` with ownership-safe tool methods
  - Optional FastMCP stdio server builder (`run_stdio_server`)
- `backend/app/routers/mcp.py`
  - `/mcp/tools`, `/mcp/call`, `/mcp/advisor`, `/mcp/advisor/stream`
- `backend/run_mcp_server.py`
  - Launches native MCP stdio server
- `frontend/src/api/ai.ts`
  - `streamAdvisorMessage(...)` SSE client helper
- `frontend/src/pages/Dashboard.tsx`
  - AI chat now consumes streaming advisor endpoint with fallback to legacy endpoint

### End-to-End Chat Flow (Current)

1. Parent sends message from Dashboard chat panel
2. Frontend opens SSE connection to `/mcp/advisor/stream`
3. Backend uses MCP bridge tools (`query_child_metrics`, `generate_therapy_brief`, etc.)
4. Response is streamed in chunks (`start` -> `chunk` -> `done`)
5. UI appends chunks live
6. If SSE fails, frontend falls back to `POST /ai/chat/{child_id}`

### Security Model

- Tool calls are never direct DB access from the LLM side.
- Every MCP tool call enforces ownership check (`parent_id`, `child_id`).
- Unauthorized access returns `403`.
- Invalid tool inputs return `400`.

---

## API Endpoints (Quick Guide)

Swagger docs: `http://localhost:8000/docs`

### Auth

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `PUT /auth/me`

### Child & Log Management

- `GET/POST/PUT/DELETE /children`
- `GET/POST/PUT/DELETE /logs`
- `GET/POST /reports`
- `GET/POST/PUT/DELETE /reminders`

### AI & Workflow

- `POST /ai/chat/{child_id}` (legacy compatibility endpoint)
- `GET /ai/anomaly/{child_id}` (legacy compatibility endpoint)
- `POST /ai/v2/workflow/{child_id}` (LangGraph hybrid workflow)
- `GET /ai/v2/workflow/info`
- `GET /ai/v2/monitoring/stats`
- `POST /ai/v2/crew/{crew_type}/{child_id}`

### MCP Integration (New)

- `GET /mcp/tools` (list available MCP tools for authenticated user)
- `POST /mcp/call` (invoke a tool safely with ownership checks)
- `POST /mcp/advisor` (conversational advisor endpoint using MCP tools)
- `GET /mcp/advisor/stream` (SSE-based streaming advisor response for chat UI)

`/mcp/call` example body:

```json
{
  "tool_name": "query_child_metrics",
  "arguments": {
    "child_id": 1,
    "metric": "sleep_hours",
    "days": 30
  }
}
```

`/mcp/advisor/stream` example request:

```text
GET /mcp/advisor/stream?token=<JWT>&child_id=1&message=Bu%20hafta%20uyku%20duzeni%20nasil
```

SSE event shape:

```json
{ "type": "start" }
{ "type": "chunk", "text": "..." }
{ "type": "done", "tool_result": { "...": "..." } }
```

### Human-in-the-Loop (Admin)

- `GET /ai/v2/reviews/{child_id}`
- `GET /ai/v2/reviews/all/{child_id}`
- `PUT /ai/v2/reviews/{review_id}`
- `POST /ai/v2/reviews/create`

---

## Project Structure

```text
autism-tracker/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── workflow.py
│   │   ├── crew_manager.py
│   │   ├── workflow_nodes.py
│   │   ├── tools.py
│   │   ├── routers/
│   │   │   └── mcp.py
│   │   ├── models/
│   │   └── services/
│   │       └── mcp_server.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run_mcp_server.py
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── ai.ts
│   │   └── pages/
│   │       └── Dashboard.tsx
│   └── package.json
├── docker-compose.yml
├── cloudbuild.yaml
└── README.md
```

---

## Setup (Local Development)

### Requirements

- Docker Desktop
- Node.js 18+
- Python 3.11+

### 1) Clone the repository

```bash
git clone https://github.com/dilangulerx/AutiCare.git
cd autism-tracker
```

### 2) Prepare backend environment variables

Create your `backend/.env` file according to your local setup.

Example:

```env
DATABASE_URL=mysql+pymysql://root:rootpassword@db:3306/autism_tracker
SECRET_KEY=change-me-in-production
OPENAI_API_KEY=your_openai_key
RESEND_API_KEY=your_resend_key
```

### 3) Start backend + database

```bash
docker-compose up -d
```

Backend: `http://localhost:8000`  
Docs: `http://localhost:8000/docs`  
MySQL: `localhost:3307`

### 4) Start frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

### 5) (Optional) Run native MCP stdio server

If you want to connect an external MCP-capable agent runtime directly:

```bash
cd backend
pip install -r requirements.txt
python run_mcp_server.py
```

This starts an MCP stdio server that exposes:

- `get_child_logs`
- `query_child_metrics`
- `get_weekly_summary`
- `add_reminder`
- `generate_therapy_brief`

### 6) Validate streaming chat integration

After backend + frontend are running:

1. Login from UI
2. Open Dashboard -> `AI Asistan`
3. Send a question like: `Bu hafta uyku duzeni nasil?`
4. You should see answer text streamed progressively
5. If stream is unavailable, the app automatically uses legacy chat endpoint

---

## Google Cloud Deployment Notes

This repository includes Cloud Build configuration: `cloudbuild.yaml`

Recommended simple production flow:

1. Work from the `deploy/prod` branch
2. In Cloud Run, choose "Continuously deploy from repository"
3. Select branch `deploy/prod`
4. Set Dockerfile path to `backend/Dockerfile`
5. Manage secrets with Secret Manager

---

## Docker Commands

```bash
docker-compose up -d
docker-compose logs -f
docker-compose restart backend
docker-compose down
docker exec -it autism_db mysql -u root -prootpassword autism_tracker
```

---

## Database Summary

- `users`
- `children`
- `daily_logs`
- `weekly_reports`
- `reminders`
- `human_reviews` (HITL review records)

---

## Screenshots


```md
## Screenshots

### Login Page
![Login](./docs/screenshots/login.png)

### Dashboard
![Dashboard](./docs/screenshots/dashboard.png)

### Child Profile
![Child Profile](./docs/screenshots/child-profile.png)

### AI Workflow / Report
![AI Workflow](./docs/screenshots/ai-workflow.png)
```

---

## License

This project was created for educational and product development purposes.

---

## Disclaimer

AutiCare is not a medical device and does not provide clinical diagnosis or treatment. AI outputs are informational and should be reviewed with qualified professionals.

