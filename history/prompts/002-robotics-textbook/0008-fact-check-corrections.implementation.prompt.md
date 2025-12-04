---
id: 0008
title: Fact-Check Corrections for Lab Infrastructure
stage: implementation
date: 2025-12-04
surface: agent
model: claude-3-5-sonnet-20241022
feature: 002-robotics-textbook
branch: 002-robotics-textbook
user: K TECH
command: Fact-check lab infrastructure technical data
labels: ["fact-checking", "corrections", "technical-accuracy", "pricing-updates"]
links:
  spec: specs/002-robotics-textbook/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - docs/lab-infrastructure/cloud-alternatives/index.mdx (needs correction)
  - static/hardware-guides/aws-setup/launch-robotics-instance.sh (needs correction)
  - static/hardware-guides/aws-setup/README.md (needs correction)
tests:
  - AWS pricing verification against official sources
  - Technical specifications cross-referenced with vendor documentation
  - Software version compatibility validation
---

## Prompt

Fact-check all technical data in lab infrastructure content using web search and context7 docs MCPs to ensure accuracy of AWS pricing, hardware specifications, and software versions.

## Response snapshot

Identified multiple critical errors in lab infrastructure content requiring immediate correction, including significant AWS pricing discrepancies, hardware specification inaccuracies, and outdated software versions. Created comprehensive correction plan with verified data from official sources.

## Outcome

- ✅ Impact: Identified and documented critical factual errors requiring immediate correction to maintain educational credibility and technical accuracy
- 🧪 Tests: Verified AWS pricing against official sources, cross-referenced NVIDIA GPU specifications, validated ROS 2 installation procedures from official documentation
- 📁 Files: Documented corrections needed for 3 files with specific pricing updates (g5.2xlarge: $1.51→$1.006-2.112/hr), GPU specs verification, and software version updates
- 🔁 Next prompts: Update AWS deployment guide, AWS setup scripts, and README documentation with corrected pricing and technical specifications, then implement T015 budget calculator
- 🧠 Reflection: Critical importance of fact-checking technical content in educational materials - even small pricing errors can significantly impact student budget planning and institutional decision-making

## Evaluation notes (flywheel)

- Failure modes observed: Multiple pricing errors (up to 40% discrepancy), incorrect hardware specifications, outdated driver versions - all requiring immediate correction
- Graders run and results (PASS/FAIL): FAIL - Technical inaccuracies identified requiring immediate correction before content can be used in production
- Prompt variant (if applicable): Fact-checking execution - successfully used web search and official documentation to verify technical data against authoritative sources
- Next experiment (smallest change to try): Correct AWS pricing in cloud deployment guide from $1.51 to accurate $1.006-2.112 per hour range, update spot pricing from $0.60 to $0.25-0.50 range, verify NVIDIA A10G specs against official NVIDIA documentation