# GARUDA Implementation Log

## Status Summary

This file tracks what is fully implemented, what is currently in progress, and what should be tackled next for the hackathon build.

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
- Candidate persistence in PostgreSQL
- Match persistence in PostgreSQL
- Execution trace persistence in PostgreSQL
- Taxonomy listing and semantic search endpoints
- Batch parse queue using Redis
- Webhook registration and dispatch flow
- Structured error responses

### Frontend
- Resume upload UI
- Batch upload UI with polling table
- Candidate profile view
- Match page with score gauge and gap analysis
- Taxonomy browser
- Frontend API key input and local storage support

### LLM Provider Support
- OpenAI support
- Gemini support
- Configurable provider via environment variables

### Validation And Stability Work Already Done
- Pytest setup and import-path fixes
- ChromaDB Docker version pinning
- Docker path fixes for taxonomy files
- CPU-only PyTorch install in backend Docker image
- CORS preflight fixes for browser uploads
- Postgres-safe webhook event query fix
- Unit test suite passing locally in Python 3.11 environment

## Currently In Progress

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

### PRD Alignment Improvements
- Strengthen webhook delivery validation with real test endpoints
- Further improve batch-processing reliability with real multi-file runs
- Improve profile and match UX for error states and partial results
- Expand test coverage for API routes and agent failure cases

### Demo And Evaluation Readiness
- Finalize a clean demo flow:
  - upload resume
  - show parsed profile
  - show normalized skills
  - run job match
  - show score and gaps
- Prepare judging explanation, feature summary, and architecture walkthrough

## Notes

- The project is already beyond scaffolding and is now in validation-and-refinement mode.
- Current priority is not creating new modules blindly, but making sure the implemented PRD features behave correctly on real inputs.
