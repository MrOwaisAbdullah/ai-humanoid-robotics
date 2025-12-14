# Implementation Plan: Urdu Translation Improvements and Personalization

**Branch**: `001-urdu-translation-fix` | **Date**: 2025-12-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-urdu-translation-fix/spec.md`

## Summary

This plan implements high-quality Urdu translation with AI-powered personalization features. The solution uses Google Gemini LLM for translation, server-side caching with localStorage fallback, and requires authentication for personalization. Key features include: full-screen focus mode for translations, automatic handling of code blocks, quality feedback mechanism, and content chunking for large documents. Always use Context 7 mcp for the latest documentationa and implementation.

## Technical Context

**Language/Version**: TypeScript/React 18+ (frontend), Python 3.11+ (backend)
**Primary Dependencies**: Google Gemini API, FastAPI (backend), React/Docusaurus (frontend), Framer Motion (animations)
**Storage**: SQLite database for cache and user preferences, localStorage for fallback
**Testing**: Jest/React Testing Library (frontend), pytest (backend)
**Target Platform**: Web application (responsive design)
**Project Type**: Web application with existing frontend and backend
**Performance Goals**: Translation in <3 seconds, content switching in <1 second, 70% cache hit rate
**Constraints**: 50,000 characters per translation request with automatic chunking
**Scale/Scope**: Support for concurrent users, 99% uptime requirement

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Mandatory Gates
✅ **Specification-First Development**: Feature has clear spec with acceptance criteria
✅ **Production-First Mindset**: Design includes caching, error handling, and monitoring
✅ **SOLID Principles**: Component design follows SRP, OCP, DIP
✅ **Statelessness**: Translation API is stateless, context passed explicitly
✅ **Error Handling**: All external calls have error handling planned
✅ **Configuration Management**: Using environment variables for API keys
✅ **API Design**: RESTful endpoints planned with versioning
✅ **TDD**: Testing strategy defined before implementation
✅ **Performance**: Performance targets align with constitution (<3s translation)
✅ **Documentation**: All components will have comprehensive documentation
✅ **Security**: API security considerations included
✅ **Accessibility**: WCAG AA compliance for focus mode UI
✅ **Git Standards**: Following commit message convention

### Architecture Compliance
✅ **Separation of Concerns**: Clear frontend/backend separation
✅ **Modular Design**: Translation, caching, personalization as separate modules
✅ **Dependency Inversion**: Depending on abstractions (TranslationService interface)

## Project Structure

### Documentation (this feature)

```text
specs/001-urdu-translation-fix/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   └── api.yaml         # OpenAPI specification
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── translation.py          # Translation data model
│   │   ├── personalization.py     # User preferences model
│   │   └── content_localization.py # Content tracking model
│   ├── services/
│   │   ├── translation_service.py # Gemini LLM integration
│   │   ├── cache_service.py      # Translation caching
│   │   └── personalization_service.py # Content adaptation
│   ├── api/
│   │   └── v1/
│   │       └── translation.py    # Translation endpoints
│   └── utils/
│       ├── text_processor.py     # Content chunking
│       └── technical_terms.py    # Term transliteration
└── tests/
    ├── unit/
    ├── integration/
    └── contract/

frontend/
├── src/
│   ├── components/
│   │   └── Localization/
│   │       ├── FocusMode.tsx      # Full-screen translation modal
│   │       ├── Personalization.tsx # Personalization UI
│   │       └── TranslationFeedback.tsx # Thumbs up/down
│   ├── contexts/
│   │   ├── LocalizationContext.tsx # Language context
│   │   └── FocusModeContext.tsx   # Focus mode state
│   ├── services/
│   │   ├── translationAPI.ts     # API client
│   │   └── cache.ts              # Local storage fallback
│   └── theme/
│       └── DocItem/
│           └── AIFeaturesBar.tsx  # Translate button
└── tests/
    ├── components/
    └── integration/
```

**Structure Decision**: Web application with existing backend (FastAPI) and frontend (React/Docusaurus). The translation feature integrates with the existing AI features bar and uses the established pattern of contexts for state management.

## Complexity Tracking

No constitution violations identified. The design follows all mandated principles:

- ✅ Single responsibility for each component
- ✅ Clear separation of concerns
- ✅ Proper abstraction layers
- ✅ Testable, modular design

The complexity is justified by the feature requirements and does not violate any constitution principles.

## Phase 0 Complete: Research & Decisions

✅ **Technical Research Completed**:
- Selected Google Gemini API for translation
- Designed hybrid caching strategy (server-side + localStorage)
- Established code block handling approach
- Defined content chunking parameters (50,000 char limit)
- Planned personalization via prompt engineering

✅ **Architecture Decisions Made**:
- RESTful API design with versioning
- Event-driven feedback system
- Modular component structure
- Performance optimization strategies

## Phase 1 Complete: Design & Contracts

✅ **Data Model Designed**:
- Translation entity with caching support
- PersonalizationProfile for user preferences
- ContentLocalization tracking
- TranslationFeedback for quality metrics
- Proper indexing and relationships defined

✅ **API Contracts Created**:
- OpenAPI 3.0 specification
- Translation endpoints
- Personalization endpoints
- Feedback system
- Cache management

✅ **Quickstart Guide Prepared**:
- Local setup instructions
- Testing procedures
- Common troubleshooting
- Deployment considerations
