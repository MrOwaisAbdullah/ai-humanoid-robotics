---
id: 0010
title: Constitutional Enhancements for Fact-Checking and Agent Usage
stage: constitution
date: 2025-12-04
surface: agent
model: claude-3-5-sonnet-20241022
feature: 002-robotics-textbook
branch: 002-robotics-textbook
user: K TECH
command: Update constitution and CLAUDE.md to include subagent usage guidelines
labels: ["constitution", "fact-checking", "mcp-tools", "subagents", "specialized-agents", "governance"]
links:
  spec: .specify/memory/constitution.md
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
  - CLAUDE.md
tests:
  - Constitution completeness validation
  - CLAUDE.md alignment with constitution principles
  - MCP tool integration verification
  - Agent usage guidelines clarity assessment
---

## Prompt

Update constitution and CLAUDE.md to mention using subagents and agent skills when appropriate, based on successful fact-checking demonstration using specialized agents.

## Response snapshot

Successfully enhanced constitution and CLAUDE.md with comprehensive guidelines for using specialized agents and MCP tools for fact-checking. Added Documentation Research & Fact-Checking Principle mandating Web Search for technical data verification and expanded AI Collaboration Guidelines with detailed agent selection criteria and usage patterns.

## Outcome

- ✅ Impact: Institutionalized fact-checking requirements and specialized agent usage in project governance, preventing future technical inaccuracies
- 🧪 Tests: Constitution guidelines comprehensive and actionable, CLAUDE.md updated with practical agent usage examples, MCP tool integration clearly documented
- 📁 Files: Enhanced constitution.md (version 1.2.0) with fact-checking mandate and expanded AI Collaboration Guidelines, updated CLAUDE.md with Section 4 on specialized agents
- 🔁 Next prompts: Continue with T015 (budget calculator implementation) using appropriate specialized agents, then proceed to Phase 4 content creation with maintained fact-checking standards
- 🧠 Reflection: Successful demonstration of constitutional evolution based on practical experience - fact-checking incident revealed critical need for explicit MCP tool usage guidelines and agent selection criteria

## Evaluation notes (flywheel)

- Failure modes observed: None - constitutional updates comprehensive and address identified governance gaps
- Graders run and results (PASS/FAIL): PASS - Enhanced governance framework ready for project-wide adoption with clear fact-checking and agent usage standards
- Prompt variant (if applicable): Constitutional enhancement - successfully updated both constitution.md and CLAUDE.md with coordinated improvements based on practical project experience
- Next experiment (smallest change to try): Implement T015 budget calculator using content-writer or general-purpose agent following new constitutional guidelines for agent selection and fact-checking