# GARUDA Implementation Log

## Status Summary

This file tracks what is fully implemented, what is currently in progress, and what should be tackled next for the hackathon build.

## Every-Time Check

Before marking any slice done, verify:
- Backend route or parser change returns the expected payload shape
- Data is actually persisted and can be fetched back, not just shown optimistically in UI
- Frontend loading, empty, success, and error states all render cleanly
- PRD goal is covered, not just the technical subtask
- End-to-end happy path works once with a real example
- Partial or missing-input fallback still behaves safely
- Scores, badges, and rankings look believable on a real sample
- Focused tests were added or updated for the changed logic
- Backend tests and frontend build were run when the environment allows it
- `IMPLEMENTATION_LOG.md` was updated with implemented work, validation status, blockers, and next step

## Fully Implemented And Working

### Core Platform
- Full repository structure for backend, frontend, Docker, data seeds, tests, and docs
- FastAPI backend with versioned REST API under `/api/v1`
- React frontend with upload, match, taxonomy, and candidate profile pages
- Docker Compose stack for backend, frontend, PostgreSQL, Redis, and ChromaDB
- Root `.env` and backend `.env.example` setup for local and containerized runs

### Resume Parsing Pipeline
- Resume ingestion for PDF, DOCX, and TXT
- Raw text extraction using PyMuPDF, pdfplumber, and python-docx
- LangGraph orchestration pipeline with parse, normalize, embed, and match nodes
- Parsing agent with structured candidate profile output
- Heuristic extraction for low-cost basic fields:
  - name
  - email
  - phone
  - LinkedIn
  - location
  - summary
  - basic skills
- LLM-assisted extraction for harder structured sections
- Graceful fallback to heuristic profile when LLM parsing fails

### Skill Normalization
- Taxonomy seed with 200+ canonical skills and aliases
- Exact alias lookup normalization
- Punctuation-tolerant exact alias lookup for common spacing and symbol variants
- Fuzzy matching with RapidFuzz
- Embedding-based matching through ChromaDB
- LLM fallback for difficult or emerging skills
- In-process caching for repeated LLM skill fallback requests
- Pending taxonomy review storage for low-confidence skills
- Proficiency estimation from resume context
- Rule-based skill inference from YAML rules
- Raw skill cleanup and noise filtering before expensive normalization tiers

### Matching Engine
- Job-description parsing pipeline
- Weighted semantic matching for required and preferred skills
- Experience multiplier support
- Final match score and grade calculation
- Gap analysis with missing skills and upskilling suggestions
- Recommendation generation
- Heuristic job-description parsing fallback for:
  - required skills
  - preferred skills
  - minimum years of experience
  - role level
- Heuristic recommendation fallback when LLM is unavailable

### API And Persistence
- Auth middleware with API key lookup
- Redis-based sliding-window rate limiting
- Prometheus-compatible `/metrics` endpoint with API and agent instrumentation
- Candidate persistence in PostgreSQL
- Match persistence in PostgreSQL
- Execution trace persistence in PostgreSQL
- Taxonomy listing and semantic search endpoints
- Batch parse queue using Redis
- Per-file batch status tracking for queued, processing, done, partial, and failed files
- Concurrent batch execution with worker limits for multi-file runs
- Dead-letter capture for failed batch files in Redis for later inspection or replay
- Webhook registration and dispatch flow
- Structured error responses
- Candidate and job embedding persistence in dedicated ChromaDB collections

### Frontend
- Resume upload UI
- Batch upload UI with polling table
- Candidate profile view
- Match page with score gauge and gap analysis
- Taxonomy browser
- Frontend API key input and local storage support
- Frontend error-state UX for upload, candidate retrieval, batch polling, and match failures
- Partial-result UX for parsed candidates recovered through fallback logic

### LLM Provider Support
- OpenAI support
- Gemini support
- Configurable provider via environment variables

### TalentOS V3 Recruiter Slice
- JWT-based recruiter auth with register and login endpoints
- JWT-based employee auth entry with register and login support
- V3 schema extension for users, recruiters, employees, job_postings, candidate_applications, and related tables
- Job Posting Agent for raw-JD or structured recruiter job creation
- Geocoding service with Redis caching plus haversine distance filtering
- Role Matcher for location-aware recruiter ranking with verification-weighted scoring and project relevance
- Recruiter endpoints for job CRUD, run-matching, ranked candidate retrieval, and pipeline stage updates
- Recruiter frontend pages for console access, job creation, and pipeline board review
- TalentOS landing page with recruiter and employee entry points
- Role-aware dashboard routing so recruiter and employee users land on different dashboards
- Global logout action for JWT-authenticated TalentOS sessions
- Match hub page that now lists recruiter-posted jobs instead of only the old V2 ad-hoc match view
- Manual-vs-paste recruiter job creation mode so structured skill input is not silently ignored

### Validation And Stability Work Already Done
- Pytest setup and import-path fixes
- ChromaDB Docker version pinning
- Docker path fixes for taxonomy files
- CPU-only PyTorch install in backend Docker image
- CORS preflight fixes for browser uploads
- Postgres-safe webhook event query fix
- Heuristic LLM-skip gates for simple resume parsing and strong JD parsing
- Heuristic-first match recommendations to reduce recurring LLM usage
- OpenAI-compatible base URL support for local providers such as LM Studio
- Backend batch-status tests expanded for per-file status updates
- Initial Alembic revision added for the database schema
- Migration-first startup path with Alembic support and `create_all` fallback
- Docker runtime aligned with backend health checks, frontend health checks, and 4-worker uvicorn startup
- Frontend production build validated successfully after UX changes
- Unit test suite passing locally in Python 3.11 environment

## Currently In Progress

### TalentOS V3 Expansion
- Priority 1 recruiter flow is now implemented and ready for live demo:
  - recruiter registration and login
  - job creation
  - run matching
  - ranked recruiter candidate list
  - pipeline stage movement
- Landing flow now supports both recruiter and employee entry
- Match navigation now routes recruiters to their posted jobs
- Next V3 build slice is Priority 2:
  - GitHub social scraping
  - skill verification profiles
  - employee-facing verified profile and job-board flow
- Candidate profile overview now surfaces both LinkedIn and GitHub links directly in the contact panel
- Candidate profile overview now includes a top-projects section so project evidence is visible without leaving the main tab

### End-To-End Runtime Validation
- Real single-resume parse flow is working end to end through frontend and backend
- Candidate profile retrieval and normalized skill retrieval are working after upload
- Continuing live validation of match flow against real job descriptions

### Parse Quality Hardening
- Improving reliability of parsed output on real-world resume layouts
- Reducing unnecessary LLM usage for simple extraction tasks
- Surfacing cleaner failure messages for partial pipeline failures

### Normalization Performance Hardening
- Reducing Gemini usage inside the normalization stage
- Cutting normalization latency on real resumes with larger skill lists
- Improving local matching coverage before LLM fallback

### Matching Quality Hardening
- Validating real-world semantic match scores
- Checking recommendation quality and gap analysis quality on actual test cases
- Refining heuristic and LLM blending in the matching pipeline

## Next Planned Work

### Product Validation
- Test multiple real resumes end to end
- Validate parsed profile accuracy field by field
- Validate match results on multiple job descriptions
- Verify taxonomy browser and candidate skills views with live data
- Measure and improve normalization latency on larger resumes
- Re-parse one resume containing a GitHub link and confirm the candidate profile stores and displays it correctly
- Verify project cards render well for resumes with 0, 1, and multiple extracted projects

### PRD Alignment Improvements
- Strengthen webhook delivery validation with real test endpoints
- Expand test coverage for API routes and agent failure cases

### Demo And Evaluation Readiness
- Finalize a clean demo flow:
  - upload resume
  - show parsed profile
  - show normalized skills
  - run job match
  - show score and gaps
- Finalize the TalentOS recruiter demo flow:
  - register recruiter
  - create Ahmedabad React role
  - run matching
  - show ranked local-first pipeline
- Prepare judging explanation, feature summary, and architecture walkthrough

## Notes

- The project is already beyond scaffolding and is now in validation-and-refinement mode.
- Current priority is not creating new modules blindly, but making sure the implemented PRD features behave correctly on real inputs.
