# GARUDA Resume Intelligence Platform

GARUDA is a multi-agent resume intelligence system built for hackathon-grade speed without giving up production-style architecture. It ingests resumes in PDF, DOCX, and TXT formats, extracts structured candidate data with OpenAI structured outputs, normalizes raw skills against a seeded taxonomy, and performs semantic candidate-to-job matching with a weighted multi-agent pipeline.

The platform is split into a FastAPI backend and a React frontend. LangGraph orchestrates parsing, normalization, embedding, and matching as explicit graph nodes; PostgreSQL stores durable records; Redis powers caching and batch queues; and ChromaDB backs embedding-based skill normalization and taxonomy search.

## Architecture Overview

```text
Resume Upload / Job Description
        |
        v
 React Frontend  --->  FastAPI API Layer
                          |  |  |
                          |  |  +--> Auth + Rate Limit
                          |  +-----> Redis Queue / Cache
                          +-------> LangGraph Orchestrator
                                       |-> Parsing Agent
                                       |-> Normalization Agent
                                       |-> Embed Node
                                       |-> Matching Agent
                          |
                          +--> PostgreSQL (candidates, jobs, matches, traces, keys, webhooks)
                          +--> ChromaDB (skill embeddings)
                          +--> Webhook Dispatcher
```

## Quick Start

```bash
git clone https://github.com/KHUSHPATEL143/Talentra.git
cd Talentra
cp .env.example .env
# Fill in OPENAI_API_KEY and optionally DEFAULT_API_KEY
docker compose up --build
# API: http://localhost:8000/docs
# Frontend: http://localhost:3000
```

If `DEFAULT_API_KEY` is left blank, the backend seeds a UUID development key at first startup and prints it to the backend logs as `DEV API KEY: ...`.

## API Endpoints

### 1. `POST /api/v1/parse`

```bash
curl -X POST "http://localhost:8000/api/v1/parse" \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "file=@sample_resume.pdf"
```

### 2. `POST /api/v1/parse/batch`

```bash
curl -X POST "http://localhost:8000/api/v1/parse/batch" \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "files=@resume_1.pdf" \
  -F "files=@resume_2.docx"
```

### 3. `GET /api/v1/jobs/{job_id}/status`

```bash
curl "http://localhost:8000/api/v1/jobs/YOUR_JOB_ID/status" \
  -H "X-API-Key: YOUR_API_KEY"
```

### 4. `GET /api/v1/candidates/{candidate_id}`

```bash
curl "http://localhost:8000/api/v1/candidates/YOUR_CANDIDATE_ID" \
  -H "X-API-Key: YOUR_API_KEY"
```

### 5. `GET /api/v1/candidates/{candidate_id}/skills`

```bash
curl "http://localhost:8000/api/v1/candidates/YOUR_CANDIDATE_ID/skills" \
  -H "X-API-Key: YOUR_API_KEY"
```

### 6. `POST /api/v1/match`

```bash
curl -X POST "http://localhost:8000/api/v1/match" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "candidate_id": "YOUR_CANDIDATE_ID",
    "job_description": "We need a backend engineer with Python, FastAPI, Docker, and PostgreSQL experience.",
    "weights": {"required": 0.7, "preferred": 0.3},
    "mode": "precision"
  }'
```

### 7. `GET /api/v1/skills/taxonomy`

```bash
curl "http://localhost:8000/api/v1/skills/taxonomy?page=1&page_size=50" \
  -H "X-API-Key: YOUR_API_KEY"
```

### 8. `GET /api/v1/skills/taxonomy/search`

```bash
curl "http://localhost:8000/api/v1/skills/taxonomy/search?q=machine%20learning&limit=10" \
  -H "X-API-Key: YOUR_API_KEY"
```

### 9. `POST /api/v1/webhooks`

```bash
curl -X POST "http://localhost:8000/api/v1/webhooks" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "url": "https://example.com/webhooks/garuda",
    "events": ["parse.complete", "match.complete", "batch.complete"]
  }'
```

## Python SDK Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "YOUR_API_KEY"
HEADERS = {"X-API-Key": API_KEY}

with open("sample_resume.pdf", "rb") as resume_file:
    parse_response = requests.post(
        f"{BASE_URL}/parse",
        headers=HEADERS,
        files={"file": ("sample_resume.pdf", resume_file, "application/pdf")},
        timeout=120,
    )
parse_response.raise_for_status()
parsed = parse_response.json()
candidate_id = parsed["candidate_id"]

match_response = requests.post(
    f"{BASE_URL}/match",
    headers={**HEADERS, "Content-Type": "application/json"},
    json={
        "candidate_id": candidate_id,
        "job_description": "Hiring a Python engineer with FastAPI, Docker, PostgreSQL, and cloud deployment skills.",
        "weights": {"required": 0.7, "preferred": 0.3},
        "mode": "precision",
    },
    timeout=120,
)
match_response.raise_for_status()
match_result = match_response.json()

print("Candidate:", candidate_id)
print("Score:", match_result["score"], match_result["grade"])
print("Missing skills:", [item["skill"] for item in match_result["missing_skills"]])
```

## JavaScript SDK Example

```javascript
import axios from "axios";
import fs from "fs";
import FormData from "form-data";

const BASE_URL = "http://localhost:8000/api/v1";
const API_KEY = "YOUR_API_KEY";

const formData = new FormData();
formData.append("file", fs.createReadStream("sample_resume.pdf"));

const parseResponse = await axios.post(`${BASE_URL}/parse`, formData, {
  headers: {
    ...formData.getHeaders(),
    "X-API-Key": API_KEY
  },
  timeout: 120000
});

const candidateId = parseResponse.data.candidate_id;

const matchResponse = await axios.post(`${BASE_URL}/match`, {
  candidate_id: candidateId,
  job_description: "Hiring a Python engineer with FastAPI, Docker, PostgreSQL, and cloud deployment skills.",
  weights: { required: 0.7, preferred: 0.3 },
  mode: "precision"
}, {
  headers: {
    "X-API-Key": API_KEY
  },
  timeout: 120000
});

console.log(matchResponse.data);
```

## Adding New Skills

Edit [backend/data/taxonomy/skills_taxonomy.json](/D:/hackathon/GARUDA/backend/data/taxonomy/skills_taxonomy.json) and restart the backend container. On startup, the taxonomy loader seeds PostgreSQL if empty and upserts skill embeddings into ChromaDB.

## Running Tests

```bash
cd backend
pytest tests/ -v
```

## Environment Variables

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | OpenAI key used for structured extraction, fallback normalization, and recommendations |
| `DATABASE_URL` | Async SQLAlchemy PostgreSQL connection string |
| `REDIS_URL` | Redis connection string for rate limiting, cache, and batch jobs |
| `CHROMADB_HOST` | ChromaDB hostname |
| `CHROMADB_PORT` | ChromaDB HTTP port |
| `DEFAULT_MATCH_MODE` | Default matching threshold mode (`precision` or `recall`) |
| `MATCH_PRECISION_THRESHOLD` | Similarity threshold used in precision mode |
| `MATCH_RECALL_THRESHOLD` | Similarity threshold used in recall mode |
| `MAX_WORKERS` | Batch orchestration concurrency |
| `MAX_FILE_SIZE_MB` | Maximum single upload size |
| `MAX_BATCH_FILES` | Maximum files in one batch request |
| `REDIS_CACHE_TTL_SECONDS` | Candidate cache TTL in Redis |
| `WEBHOOK_TIMEOUT_SECONDS` | Outbound webhook timeout |
| `DEFAULT_API_KEY` | Optional preseeded API key for local/frontend convenience |
| `REACT_APP_API_URL` | Frontend API base URL |
| `REACT_APP_API_KEY` | Frontend API key injected at build time |
