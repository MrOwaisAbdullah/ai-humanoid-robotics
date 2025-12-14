# Implementation Plan: OpenAI Translation System

**Branch**: `002-openai-translation` | **Date**: 2025-12-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-openai-translation/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This plan implements a robust translation system that replaces the broken Gemini-based translation with OpenAI Agents SDK using Gemini API. The system translates complete book pages from English to Urdu while preserving formatting and handling code blocks appropriately. Key features include intelligent caching, progress tracking, and streaming responses.

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript/React 18+ (Frontend)
**Primary Dependencies**: OpenAI Agents SDK, Gemini API, FastAPI, SQLAlchemy, React
**Storage**: SQLite (development), PostgreSQL (production), Redis (caching)
**Testing**: pytest (backend), Jest/React Testing Library (frontend)
**Target Platform**: Web (Hugging Face Spaces deployment)
**Project Type**: Full-stack web application with translation service
**Performance Goals**: <3 second response time, 95% cache hit rate, 99.9% uptime
**Constraints**: Rate limited API calls, content size <100k chars, concurrent users <1000
**Scale/Scope**: Support book translation, handle 5000-word pages, maintain session state

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── translation_openai.py      # OpenAI translation data models
│   │   └── __init__.py
│   ├── services/
│   │   ├── openai_translation/
│   │   │   ├── agent.py             # OpenAI translation agent
│   │   │   ├── client.py            # Gemini API client configuration
│   │   │   ├── service.py          # Main translation service
│   │   │   └── __init__.py
│   │   ├── content_extractor.py    # Content extraction from pages
│   │   ├── content_reconstructor.py # Rebuild HTML after translation
│   │   ├── code_block_handler.py  # Preserve code blocks
│   │   ├── content_chunker.py     # Chunk large content
│   │   ├── chunk_processor.py     # Process translation chunks
│   │   ├── parallel_executor.py   # Parallel translation execution
│   │   └── cache_service.py       # Translation cache management
│   ├── api/
│   │   └── v1/
│   │       └── translation.py      # Translation API endpoints
│   └── utils/
│       ├── translation_errors.py # Error handling utilities
│       └── logger.py              # Logging configuration
├── tests/
│   ├── test_translation.py         # Translation service tests
│   ├── test_formatting.py          # Formatting preservation tests
│   ├── test_chunking.py           # Large content handling tests
│   └── test_cache.py              # Cache functionality tests
├── migrations/
│   └── versions/                  # Database migrations
├── pyproject.toml                  # Python dependencies
├── .env.example                    # Environment variables template
└── main.py                        # FastAPI application entry

frontend/
├── src/
│   ├── components/
│   │   ├── DocItem/
│   │   │   └── AIFeaturesBar.tsx  # Translation button component
│   │   └── ...
│   ├── services/
│   │   └── translationAPI.ts       # Frontend translation service
│   ├── pages/
│   │   └── ...
│   ├── contexts/
│   │   └── ...
│   └── ...
├── package.json                    # Node.js dependencies
└── ...

docs/
├── deployment.md                   # Hugging Face Spaces deployment guide
└── README.md                      # Project documentation
```

**Structure Decision**: Web application with separate backend (Python/FastAPI) and frontend (React/TypeScript)

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
