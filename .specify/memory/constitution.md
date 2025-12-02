<!--
Sync Impact Report:
- Version change: 1.0.0 → 1.0.0 (initial adoption)
- Added sections: Core Development Philosophy, Code Quality Standards, Architecture Principles, Testing Strategy, Performance & Scalability, Documentation Standards, Security & Best Practices, Accessibility & User Experience, Git & Version Control, AI Collaboration Guidelines, Decision-Making Framework, Success Metrics, Bonus Features Strategy
- Templates requiring updates: ✅ All templates aligned with new principles
- Follow-up TODOs: None - all placeholders resolved
-->

# AI-Driven Book with RAG Chatbot Constitution

## Core Development Philosophy

### 1. Specification-First Development (Non-Negotiable)
Every feature begins as a clear spec defining intent, constraints, and acceptance criteria. Specifications are living contracts, not afterthoughts. AI literalness requires precision; vague requirements cause exponential rework.

**Application**: Use Spec-Kit Plus workflow religiously: `/sp.constitution` → `/sp.specify` → `/sp.clarify` → `/sp.plan` → `/sp.tasks` → `/sp.implement`

### 2. Production-First Mindset
Build for production from day one, not "make it work then fix it later". Every component must be deployable, observable, and maintainable. Technical debt compounds; prevention is 10x cheaper than remediation.

**Application**: Consider deployment, monitoring, and error handling in initial design.

### 3. Co-Learning with AI
This is human-AI collaboration, not human commanding AI. Engage in iterative dialogue; AI suggests patterns, human provides constraints and judgment. Best results come from combining AI's pattern recognition with human strategic thinking.

**Application**: Review AI suggestions critically; ask "why?" before accepting; provide context.

## Code Quality Standards (SOLID + DRY)

### 1. Single Responsibility Principle (SRP)
Each module/class/function does ONE thing well. If you can't describe a component's purpose in one sentence, it's doing too much.

**Book Context**: Separate content generation from rendering; separate RAG retrieval from response generation
**Chatbot Context**: Separate embedding logic from vector storage; separate API routing from business logic

### 2. Open/Closed Principle (OCP)
Open for extension, closed for modification. Design components that can be extended without modifying core working code.

**Book Context**: Design chapter templates that can be extended for different content types without modifying core structure
**Chatbot Context**: Design RAG pipeline to support multiple embedding models or vector stores without core rewrites

### 3. Liskov Substitution Principle (LSP)
Subtypes must be substitutable for their base types. Swapping implementations shouldn't break tests or require caller changes.

**Book Context**: If you create specialized chapter types (tutorial, reference, conceptual), they must work wherever base Chapter type works
**Chatbot Context**: Different retrieval strategies (semantic, keyword, hybrid) should be interchangeable

### 4. Interface Segregation Principle (ISP)
Clients shouldn't depend on interfaces they don't use. No component should have unimplemented or N/A methods.

**Book Context**: Don't force all chapter types to implement methods like "generateCodeExamples" if only technical chapters need them
**Chatbot Context**: Separate interfaces for ChatService (user-facing) vs EmbeddingService (internal)

### 5. Dependency Inversion Principle (DIP)
Depend on abstractions, not concretions. Can you swap implementations (e.g., Qdrant → Pinecone) with only config changes?

**Book Context**: Depend on ContentGenerator interface, not specific DocusaurusGenerator implementation
**Chatbot Context**: Depend on VectorStore interface, not Qdrant specifically

### 6. Don't Repeat Yourself (DRY)
Every piece of knowledge has one authoritative representation. If you need to make the same change in multiple files, you've violated DRY.

**Book Context**: Chapter metadata (author, date, tags) defined once and reused
**Chatbot Context**: Chunking logic, embedding generation, error handling - each exists in exactly one place

### 7. Styling Strategy
Use utility-first CSS (Tailwind CSS) for all custom components. Avoid writing custom CSS/CSS Modules unless absolutely necessary for complex animations or Docusaurus internal overrides.

## Architecture Principles

### 1. Separation of Concerns
```
Frontend (Docusaurus)
├── Content (Markdown)
├── Components (React - ChatWidget)
├── Styling (Tailwind CSS)
└── Configuration (docusaurus.config.js)

Backend (FastAPI)
├── API Layer (routes, request/response)
├── Business Logic (RAG pipeline)
├── Data Layer (Qdrant integration)
└── Infrastructure (config, logging, monitoring)
```

### 2. Statelessness Where Possible
- **Frontend**: Chatbot state in React only; no localStorage (violates artifact constraints)
- **Backend**: RESTful APIs are stateless; conversation context passed explicitly
- **Exceptions**: Qdrant vector store maintains persistent embeddings (by design)

### 3. Error Handling Strategy
Every external call must have error handling. Never expose internal errors to users. Always log errors with context. Provide actionable error messages. Implement retries for transient failures (rate limits, network).

```python
try:
    result = await external_service.call()
except SpecificException as e:
    logger.error(f"Context: {e}")
    raise HTTPException(status_code=500, detail="User-friendly message")
```

### 4. Configuration Management
Never hardcode; always use environment variables. Secrets in environment variables only. Separate configs for dev/staging/prod. Validate config at startup (fail fast). Document all required environment variables.

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    qdrant_url: str
    qdrant_api_key: str

    class Config:
        env_file = ".env"
```

### 5. API Design Principles
RESTful, consistent, predictable. Versioned APIs (/v1). Consistent naming (plural nouns for resources). HTTP status codes used correctly (200, 201, 400, 401, 404, 500). Request/response schemas documented.

```python
POST /api/v1/chat          # General chat
POST /api/v1/chat/selection # Text selection Q&A
POST /api/v1/embed         # Document ingestion
GET  /api/v1/health        # Health check
```

## Testing Strategy

### 1. Test-Driven Development (TDD)
Write tests before implementation. For RAG pipeline: test chunking → test embedding → test retrieval → test generation. Tests define success criteria; writing tests first clarifies requirements. Exemption: Rapid prototyping phase (Day 1); implement TDD from Day 2 onward.

### 2. Testing Pyramid
```
         /\
        /  \  E2E Tests (5-10%)
       /____\
      /      \  Integration Tests (20-30%)
     /________\
    /          \  Unit Tests (60-70%)
   /____________\
```

**Book Context**:
- Unit: Test markdown parsing, frontmatter validation
- Integration: Test Docusaurus build pipeline
- E2E: Test deployed site navigation

**Chatbot Context**:
- Unit: Test chunking algorithm, embedding generation
- Integration: Test RAG pipeline (retrieve + generate)
- E2E: Test full chat flow including streaming

### 3. What to Test
Always Test: Business logic (RAG retrieval ranking, content relevance scoring), Error handling paths (API failures, invalid input), Edge cases (empty queries, very long documents).

Don't Over-Test: Third-party library internals (trust OpenAI SDK, Qdrant client), Configuration loading (unless complex logic), Simple getters/setters.

## Performance & Scalability

### 1. Book Performance
Target: Docusaurus site loads in < 2 seconds on 3G. Practices: Image optimization (WebP, lazy loading), Code splitting (React.lazy for chatbot), Minimal JavaScript bundle size, Static site generation (pre-rendered HTML).

### 2. Chatbot Performance
Target: First response in < 3 seconds; streaming tokens < 100ms latency. Practices: Efficient chunking (800-1000 tokens, minimize overlap), Caching: Cache embeddings, cache frequent queries, Parallel processing: Embed multiple chunks concurrently, Connection pooling: Reuse Qdrant connections.

### 3. Cost Optimization
OpenAI: Use text-embedding-3-small (cheaper), batch embeddings, cache responses. Qdrant: Use free tier efficiently (1GB limit), optimize vector dimensions if needed. Deployment: Use free tiers (Vercel/Render) with smart caching.

## Documentation Standards

### 1. README.md Must Include
Project title with brief description (1-2 sentences). Features list. Architecture diagram or high-level description. Step-by-step local setup instructions. How to deploy frontend and backend. List all required environment variables with descriptions. API endpoints with request/response examples. Troubleshooting section with common issues and solutions.

### 2. Code Comments Philosophy
Don't comment WHAT: Code should be self-documenting through clear naming. Do comment WHY: Explain non-obvious decisions, trade-offs, constraints.

```python
# Bad
# Increment counter
counter += 1

# Good
# Use exponential backoff to avoid rate limiting (OpenAI has 3 RPM limit on free tier)
await asyncio.sleep(2 ** attempt)
```

### 3. Inline Documentation
Comprehensive docstrings for all public functions with Args, Returns, and Notes sections explaining non-obvious decisions, trade-offs, or constraints.

```python
def chunk_document(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split document into overlapping chunks for embedding.

    Args:
        text: Input document text
        chunk_size: Target tokens per chunk (not characters - approximate)
        overlap: Tokens to overlap between chunks (preserves context)

    Returns:
        List of text chunks with metadata preserved

    Note:
        Uses tiktoken for accurate token counting. Overlap prevents
        information loss at chunk boundaries, critical for RAG accuracy.
    """
```

## Security & Best Practices

### 1. API Security
Never commit secrets: Use .env files (gitignored). CORS properly configured: Only allow your frontend domain. Rate limiting: Prevent abuse (use slowapi middleware). Input validation: Use Pydantic models for all API inputs.

### 2. Dependency Management
Pin versions: Exact versions in requirements.txt for reproducibility. Security updates: Regular `pip audit` checks for vulnerabilities. Minimal dependencies: Only add what's truly needed.

### 3. Error Exposure
Production: Generic error messages to users. Logs: Detailed errors with stack traces (never exposed to users). Monitoring: Track error rates, set up alerts.

## Accessibility & User Experience

### 1. Book Accessibility
WCAG AA compliance: Proper headings hierarchy (h1 → h2 → h3). Alt text: All images have descriptive alt text. Color contrast: Text meets 4.5:1 contrast ratio. Keyboard navigation: All features accessible without mouse.

### 2. Chatbot UX
Loading states: Show spinner during API calls. Error states: Friendly error messages with retry options. Streaming: Show tokens as they arrive (better perceived performance). Mobile responsive: Touch-friendly button sizes (44x44px minimum).

### 3. Progressive Enhancement
Core content works without JS: Docusaurus site readable even if chatbot fails. Graceful degradation: If RAG backend is down, show helpful error, don't break site.

## Git & Version Control

### 1. Commit Message Convention
```
type(scope): subject

body (optional)

footer (optional)
```

Types: feat, fix, docs, style, refactor, test, chore

Examples:
```
feat(rag): add text selection Q&A endpoint
fix(chatbot): resolve streaming timeout issue
docs(readme): add deployment instructions
```

### 2. Branch Strategy
`main`: Production-ready code only
`develop`: Integration branch (optional for solo dev)
`feature/xxx`: Feature branches (merged via PR)

### 3. PR Requirements (Self-Review Checklist)
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No hardcoded secrets
- [ ] Error handling in place
- [ ] Performance acceptable
- [ ] Accessibility considered

## AI Collaboration Guidelines

### 1. When to Use Subagents
Complex, specialized tasks: RAG architecture, Docusaurus configuration. Need separate context: Keep main conversation focused on high-level coordination. Reusable expertise: Package knowledge for future use.

### 2. When to Use Skills
Repeatable patterns: Book structure generation, API endpoint scaffolding. Template-driven work: Chapter templates, component boilerplates. Knowledge packaging: Chunk strategies, deployment scripts.

### 3. Prompt Quality
Good Prompt includes specific success criteria, clear step-by-step instructions, and expected outcomes. Bad prompt is vague like "Make RAG thing work."

## Decision-Making Framework

When Faced with Trade-offs, Prioritize:
1. **Correctness** > Speed (RAG accuracy more important than milliseconds)
2. **Simplicity** > Cleverness (readable code > clever tricks)
3. **User Experience** > Developer Convenience (streaming responses > simpler implementation)
4. **Maintainability** > Lines of Code (clear structure > ultra-compact code)
5. **Security** > Features (don't expose secrets for convenience)

Red Flags (Stop and Reconsider):
- ❌ "I'll refactor this later" (you won't)
- ❌ "Just hardcode it for now" (it'll stay hardcoded)
- ❌ "Users won't notice" (they will)
- ❌ "This works on my machine" (it won't in production)
- ❌ "Let's skip tests to save time" (you'll lose more time debugging)

## Success Metrics

### Book Quality
- [ ] 10+ chapters, each 2000-4000 words
- [ ] Clear hierarchy (Introduction → Core Concepts → Advanced → Conclusion)
- [ ] Code examples with syntax highlighting
- [ ] Diagrams/illustrations where helpful
- [ ] Mobile-responsive, accessible
- [ ] Lighthouse score: 90+ (Performance, Accessibility, Best Practices, SEO)

### Chatbot Quality
- [ ] Answers questions accurately (test with 20 sample questions)
- [ ] Text selection Q&A works correctly
- [ ] Streaming responses (< 100ms token latency)
- [ ] Graceful error handling (no crashes)
- [ ] Mobile-friendly UI
- [ ] Response relevance score: 8/10 (based on ground truth evaluation)

### Deployment Quality
- [ ] GitHub Pages deployment automated (GitHub Actions)
- [ ] Backend deployed on free tier (Vercel/Render)
- [ ] Environment variables documented
- [ ] Health check endpoint responds
- [ ] CORS configured correctly
- [ ] SSL/TLS enabled

### Documentation Quality
- [ ] README comprehensive (setup, deployment, troubleshooting)
- [ ] API documented (request/response examples)
- [ ] Architecture diagram included
- [ ] Environment variables listed
- [ ] Subagents and Skills documented

## Bonus Features Strategy

### Showcase Reusable Intelligence
1. **Document subagents clearly**: Create SUBAGENTS.md listing each with purpose, tools, reusability
2. **Document skills comprehensively**: Create SKILLS.md with templates, examples, time savings
3. **Provide evidence**: Before/after metrics (time saved, lines of code reduced)

### Additional Features (If Time Permits)
Multi-language support (i18n), Export book as PDF, Voice input for chatbot, Conversation history persistence, Feedback system for responses, Analytics dashboard.

## Governance

This constitution supersedes all other practices. Amendments require documentation, approval, and migration plan. All PRs/reviews must verify compliance with these principles. Complexity must be justified and documented.

**Amendment Procedure**:
1. Propose changes with rationale
2. Update version according to semantic versioning (MAJOR.MINOR.PATCH)
3. Update date stamps
4. Verify template consistency
5. Document changes in Sync Impact Report

**Versioning Policy**:
- MAJOR: Backward incompatible governance or principle removals or redefinitions
- MINOR: New principle/section added or materially expanded guidance
- PATCH: Clarifications, wording, typo fixes, non-semantic refinements

**Compliance Review**: Every feature implementation must reference specific constitution principles that guided design decisions.

**Version**: 1.0.0 | **Ratified**: 2025-12-03 | **Last Amended**: 2025-12-03