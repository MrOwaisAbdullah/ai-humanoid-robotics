---
ID: 1
TITLE: constitution-documentation-research-principle
STAGE: constitution
DATE_ISO: 2025-12-03
SURFACE: agent
MODEL: sonnet-4.5
FEATURE: none
BRANCH: master
USER: Owais Abdullah
COMMAND: /sp.constitution
LABELS: ["constitution", "documentation", "context7", "mcp", "governance"]
LINKS:
  SPEC: null
  TICKET: null
  ADR: null
  PR: null
FILES_YAML:
  - .specify/memory/constitution.md
TESTS_YAML: []
PROMPT_TEXT: |
  also mention in the constitution that always use context7 mcp for latest documentations, here is the docusourous documentation you have to use through context7 mcp, https://docusaurus.io/docs
RESPONSE_TEXT: |
  Successfully updated the constitution to include the Documentation Research Principle as the 8th principle in the Code Quality Standards section. Updated version from 1.0.0 to 1.1.0 and added specific guidance to use Context7 MCP for all external library documentation including Docusaurus, OpenAI, FastAPI, Qdrant, and React. The principle emphasizes using current documentation to avoid deprecated patterns and outdated APIs.
EVALUATION: |
  Successfully added the Documentation Research Principle to the constitution with specific guidance on using Context7 MCP for external library documentation. The update ensures all future development uses current APIs and best practices, preventing deprecated patterns. Version bump to 1.1.0 is appropriate as this adds a new principle to the Code Quality Standards.
---

# Prompt History Record: Constitution Documentation Research Principle

## User Request
The user requested to add a requirement to the constitution to always use Context7 MCP for latest documentations, specifically mentioning the Docusaurus documentation at https://docusaurus.io/docs.

## Response

I successfully updated the project constitution to include a new "Documentation Research Principle" as the 8th principle in the Code Quality Standards section. Here's what was accomplished:

### Changes Made

1. **Added Documentation Research Principle** - A new principle that requires using Context7 MCP for all external library documentation
2. **Specific Library Mappings** - Provided clear guidance on using specific library IDs:
   - Docusaurus: library ID "docusaurus" for latest docs at https://docusaurus.io/docs
   - OpenAI: library ID "openai" for API documentation
   - FastAPI: library ID "fastapi" for framework documentation
   - Qdrant: library ID "qdrant" for vector database documentation
   - React: library ID "react" for component patterns

3. **Version Update** - Updated constitution version from 1.0.0 to 1.1.0 to reflect the addition of a new principle

4. **Updated Sync Impact Report** - Documented the change with proper rationale and impact assessment

### Key Benefits

- **Current APIs**: Ensures we reference the latest APIs, best practices, and deprecation notices
- **Avoids Deprecated Patterns**: Prevents using outdated internal knowledge that may lead to deprecated APIs
- **Consistent Research**: Establishes a clear process for documentation research across the project
- **Library-Specific Guidance**: Provides concrete mappings for the main frameworks used in the project

### Updated Constitution Section

```markdown
### 8. Documentation Research Principle
Always use Context7 MCP for latest documentation and API references. Never rely on cached knowledge or internal knowledge for external library documentation.

**Application**: Use `mcp__context7__get-library-docs` for all framework documentation:
- Docusaurus: Use library ID "docusaurus" for latest docs at https://docusaurus.io/docs
- OpenAI: Use library ID "openai" for API documentation
- FastAPI: Use library ID "fastapi" for framework documentation
- Qdrant: Use library ID "qdrant" for vector database documentation
- React: Use library ID "react" for component patterns

**Rationale**: Documentation changes frequently; using Context7 MCP ensures we reference current APIs, best practices, and deprecation notices. Internal knowledge may be outdated and lead to deprecated patterns.
```

The constitution now enforces consistent use of Context7 MCP for all external library research, ensuring the project maintains current best practices and avoids deprecated patterns.