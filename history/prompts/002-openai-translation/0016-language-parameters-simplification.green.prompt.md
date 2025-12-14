---
id: 0016
title: Simplify Translation Language Parameters
stage: green
date_iso: 2025-12-14
surface: agent
model: claude-3-5-sonnet-20241022
feature: 002-openai-translation
branch: 002-openai-translation
user: user
command: "why we are using source language and target language, if only from eng to urdu, we dont need to mention it by defult it is using it"
labels:
  - simplification
  - translation
  - parameters
  - english-urdu
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files_yaml:
  - src/services/simpleTranslationAPI.ts
  - src/contexts/LocalizationContext.tsx
  - src/contexts/FocusModeContext.tsx
  - src/theme/DocItem/AIFeaturesBar.tsx
tests_yaml:
  - N/A - Code simplification
prompt_text: |
  why we are using source language and target language, if only from eng to urdu, we dont need to mention it by defult it is using it
response_text: |
  Simplified the translation code by removing unnecessary source and target language parameters since we only translate from English to Urdu:

  1. **SimpleTranslationAPI.ts**:
     - Removed `sourceLanguage` and `targetLanguage` from SimpleTranslationRequest interface
     - Hardcoded `source_language: 'en'` and `target_language: 'ur'` in the API call
     - Removed language parameters from the translate method

  2. **LocalizationContext.tsx**:
     - Updated translateTextStream to always translate from English to Urdu
     - Removed language parameter handling and defaults
     - Hardcoded languages in state updates

  3. **FocusModeContext.tsx**:
     - Removed language options from showTranslation interface
     - Simplified method calls by passing empty options object
     - Removed unused language variables

  4. **AIFeaturesBar.tsx**:
     - Removed targetLang variable and comments about making it dynamic
     - Simplified showTranslation call to pass empty options

  This makes the code cleaner and removes the confusion of having configurable languages when we only support English to Urdu translation.
outcome: |
  Successfully simplified the translation implementation by removing unnecessary source and target language parameters, making the code cleaner and more focused on the single use case of English to Urdu translation.
evaluation: |
  The simplification is beneficial because:
  - Removes unnecessary complexity from the codebase
  - Eliminates potential confusion about language support
  - Makes the API more straightforward with fewer parameters
  - Reduces the chance of errors from incorrect language specifications
  - If we need to support more languages later, we can add back the parameters
---