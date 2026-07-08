# 🔬 Data Pipeline Failure Debugger

A production-ready **agentic AI system** that automatically diagnoses, classifies, and generates fixes for ETL/ELT pipeline failures using Google Gemini.

## Architecture

```
Frontend (React + Vite + Tailwind)
    ↓  POST /debug-failure
FastAPI Backend
    ↓
Orchestrator (async, parallel agents)
    ├── Log Fetch Agent   → Airflow API / S3 / Inline
    ├── Metadata Agent    → Run history, config synthesis
    ├── Classifier Agent  → Error type, severity, confidence
    ├── Dependency Agent  → Blast radius, upstream/downstream
    └── Fix Agent         → Steps, validation, rollback plan
         ↓
    Gemini 2.5 Flash (JSON-enforced output)
         ↓
    Redis (LLM response cache) + Postgres (result history)
```

## Quick Start

### Option 1: Docker Compose (recommended)

```bash
git clone <repo>
cd pipeline-debugger

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env: set GEMINI_API_KEY

docker-compose up --build
```

Open: http://localhost (frontend) | http://localhost:8000/docs (API)

### Option 2: Manual Setup

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Set GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key | ✅ Yes |
| `REDIS_URL` | Redis connection string | No (caching disabled) |
| `DATABASE_URL` | Postgres async URL | No (history disabled) |
| `AIRFLOW_BASE_URL` | Airflow REST API base | Only for Airflow source |
| `AIRFLOW_USERNAME` | Airflow credentials | Only for Airflow source |
| `AIRFLOW_PASSWORD` | Airflow credentials | Only for Airflow source |
| `AWS_ACCESS_KEY_ID` | AWS credentials | Only for S3 source |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials | Only for S3 source |
| `S3_LOG_BUCKET` | Bucket containing pipeline logs | Only for S3 source |

## API Reference

### `POST /debug-failure`
Run the full 4-agent debug pipeline.

```json
{
  "pipeline_id": "etl_sales_daily_v2",
  "error_logs": "AnalysisException: Cannot resolve column 'user_id'...",
  "pipeline_config": "Upstream: crm_sync | Downstream: finance_mart",
  "log_source": "inline"
}
```

Response includes results from all 5 agents with timing.

### `GET /pipeline-status?pipeline_id=<id>`
Fetch debug history for a pipeline from Postgres.

### `GET /health`
Health check endpoint.

## Project Structure

```
pipeline-debugger/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, routes, middleware
│   │   ├── orchestrator.py      # Agent coordination + async flow
│   │   ├── core/config.py       # Settings (pydantic-settings)
│   │   ├── agents/
│   │   │   ├── log_fetch_agent.py
│   │   │   ├── metadata_agent.py
│   │   │   ├── classifier_agent.py
│   │   │   ├── dependency_agent.py
│   │   │   └── fix_agent.py
│   │   ├── services/
│   │   │   ├── llm_service.py   # Gemini wrapper + retry
│   │   │   ├── airflow_service.py
│   │   │   ├── s3_service.py
│   │   │   ├── cache.py         # Redis
│   │   │   └── db.py            # Postgres + SQLAlchemy
│   │   ├── schemas/models.py    # Pydantic models
│   │   └── utils/
│   │       ├── parser.py
│   │       └── validators.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── Procfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── Sidebar.jsx
│   │   │   ├── Topbar.jsx
│   │   │   ├── InputPanel.jsx
│   │   │   ├── AgentPipeline.jsx
│   │   │   ├── ResultCard.jsx
│   │   │   ├── MetadataPanel.jsx
│   │   │   ├── ClassificationPanel.jsx
│   │   │   ├── DependencyPanel.jsx
│   │   │   └── FixPanel.jsx
│   │   └── services/
│   │       ├── api.js
│   │       └── presets.js
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── Dockerfile
└── docker-compose.yml
```

## Deploy to Render

1. Create a **Web Service** for the backend:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Add environment variables in Render dashboard

2. Create a **Static Site** for the frontend:
   - Build: `npm install && npm run build`
   - Publish: `dist`
   - Set `VITE_API_URL` to your backend Render URL

3. Add **Redis** and **Postgres** from Render's database add-ons.

## Features

- ✅ 4-agent agentic pipeline (Log Fetch → Metadata → Classify → Dependencies → Fix)
- ✅ Parallel agent execution (metadata + classification run concurrently)
- ✅ Gemini 1.5 Flash with enforced JSON output (`response_mime_type`)
- ✅ Retry logic with exponential backoff (tenacity)
- ✅ Redis LLM response caching (5-min TTL)
- ✅ Postgres result persistence
- ✅ Airflow REST API integration
- ✅ AWS S3 log fetching (boto3)
- ✅ Rate limiting (10 req/min)
- ✅ Structured logging (structlog)
- ✅ Prometheus metrics endpoint
- ✅ CORS, health check, Pydantic validation
- ✅ Dark-themed React UI with real-time agent state visualization
- ✅ 4 built-in pipeline failure presets
- ✅ Docker + docker-compose + Render-ready Procfile
