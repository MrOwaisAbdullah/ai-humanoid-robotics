---
title: Chat Widget Demo
description: Demo page for the ChatKit integration
---

# Chat Widget Demo

This page demonstrates the ChatKit integration with the Physical AI & Humanoid Robotics book.

## How to Use

1. Look for the chat button in the bottom-right corner of the page (🤖 icon)
2. Click on it to open the chat widget
3. Ask questions about the book content, for example:
   - "What is forward kinematics?"
   - "Explain the Jacobian matrix"
   - "What are the types of robot actuators?"

## Features

- **Glassmorphism Design**: Modern frosted glass effect that adapts to light/dark themes
- **Text Selection**: Highlight any text on the page and click "Ask AI about this"
- **Session Persistence**: Your chat history is saved locally in your browser
- **Mobile Responsive**: Full-screen chat experience on mobile devices

## Technical Details

The chat widget is powered by:
- OpenAI ChatKit React SDK for the chat interface
- FastAPI backend for session management
- RAG (Retrieval-Augmented Generation) for book-specific responses

> **Note**: Make sure your OpenAI API key is configured in the backend's `.env` file for the chat to work properly.