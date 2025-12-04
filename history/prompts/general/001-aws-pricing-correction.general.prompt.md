---
id: 001
title: AWS g5.2xlarge Pricing Correction
stage: general
date: 2025-12-04
surface: agent
model: glm-4.6
feature: none
branch: 001-docusaurus-setup
user: user
command: N/A
labels: ["aws", "pricing", "correction", "infrastructure"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - docs/lab-infrastructure/cloud-alternatives/index.mdx
  - static/hardware-guides/aws-setup/launch-robotics-instance.sh
  - static/hardware-guides/aws-setup/README.md
tests:
  - N/A
---

## Prompt

I need to correct critical factual errors in lab infrastructure content. Please update the AWS g5.2xlarge instance pricing in these files:

**ERRORS TO FIX:**
1. AWS g5.2xlarge on-demand pricing: Change from $1.51 to $1.006-2.112/hour (varies by region)
2. AWS g5.2xlarge spot pricing: Change from $0.60 to $0.25-0.50/hour
3. Update monthly cost estimates accordingly (10 hours/week usage)

**FILES TO UPDATE:**
- `docs/lab-infrastructure/cloud-alternatives/index.mdx` - Update pricing tables and cost calculations
- `static/hardware-guides/aws-setup/launch-robotics-instance.sh` - Update SPOT_PRICE from 0.60 to 0.50
- `static/hardware-guides/aws-setup/README.md` - Update cost estimates and pricing information

**VERIFIED DATA:**
- AWS g5.2xlarge on-demand: $1.006-2.112/hour depending on region
- AWS g5.2xlarge spot: $0.25-0.50/hour (typical 60-80% off on-demand)
- Monthly cost (10 hrs/week): ~$40/month spot, ~$43/month on-demand (not $60-150)

Please make precise corrections ensuring educational accuracy for budget planning. Focus on pricing sections, cost calculations, and budget estimates throughout the files.

## Response snapshot

I'll help you correct the AWS g5.2xlarge instance pricing errors across these files. Let me first examine the current content to understand the scope of corrections needed, then update all three files with the accurate pricing information.

The files have been successfully updated with corrected pricing:
- On-demand pricing changed from $1.51 to $1.006-2.112/hour
- Spot pricing changed from $0.60 to $0.25-0.50/hour
- Monthly estimates updated from $60-150 to $40-43/month
- All cost calculations and budget estimates updated accordingly

## Outcome

- ✅ Impact: Corrected critical factual pricing errors across three documentation files, ensuring accurate budget planning for students
- 🧪 Tests: N/A
- 📁 Files: 3 files updated with accurate pricing information
- 🔁 Next prompts: None needed
- 🧠 Reflection: Important to verify all numerical data in educational content, especially pricing that directly impacts student budget decisions

## Evaluation notes (flywheel)

- Failure modes observed: Initial pricing data was significantly inaccurate, potentially causing budget planning errors for students
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Implement automated price verification checks for AWS pricing in documentation