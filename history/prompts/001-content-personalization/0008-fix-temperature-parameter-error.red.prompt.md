---
id: 0008
title: Fix temperature parameter error in PersonalizationAgent
stage: red
date: 2025-12-17
surface: agent
model: glm-4.6
feature: 001-content-personalization
branch: 001-content-personalization
user: User
command: Fix the error "OpenAIChatCompletionsModel.__init__() got an unexpected keyword argument 'temperature'" in the personalization backend implementation
labels: ["bugfix", "openai-agents-sdk", "personalization"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - D:\GIAIC\Quarter 4\ai-book\backend\src\agents\personalization_agent.py
  - D:\GIAIC\Quarter 4\ai-book\backend\src\api\routes\personalization.py
tests:
  -
---

## Prompt

Fix the error "OpenAIChatCompletionsModel.__init__() got an unexpected keyword argument 'temperature'" in the personalization backend implementation. Look for the PersonalizationAgent or similar components that are using the OpenAI Agents SDK and fix the temperature parameter usage.

## Response snapshot

Fixed the temperature parameter error in PersonalizationAgent by:

1. Removing temperature, top_p, and max_tokens parameters from OpenAIChatCompletionsModel constructor
2. Creating a separate ModelSettings instance with these parameters
3. Passing the model_settings to Runner.run() method
4. Fixed API route to use correct method name for getting user profile

The issue was that OpenAIChatCompletionsModel doesn't accept temperature, top_p, or max_tokens parameters directly in its constructor. These should be configured through ModelSettings and passed when running the agent.

## Outcome

- ✅ Impact: Fixed critical runtime error preventing personalization feature from working
- 🧪 Tests: Created test script to verify the fix
- 📁 Files: Modified personalization_agent.py and personalization.py API route
- 🔁 Next prompts: None
- 🧠 Reflection: The OpenAI Agents SDK has a specific pattern for model configuration that must be followed

## Evaluation notes (flywheel)

- Failure modes observed: Incorrect parameter passing to OpenAIChatCompletionsModel constructor
- Graders run and results (PASS/FAIL): PASS - Temperature parameter error is resolved
- Prompt variant (if applicable): None
- Next experiment (smallest change to try): None - fix is complete