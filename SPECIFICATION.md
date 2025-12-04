# SPECIFICATION

## Project Title
AI-Driven Textbook for Physical AI & Humanoid Robotics with Integrated RAG Chatbot

## Overall Goal
To create a comprehensive, AI-driven textbook for a "Physical AI & Humanoid Robotics" course using Docusaurus, integrated with a RAG chatbot for interactive learning, built with FastAPI, Qdrant, and OpenAI. The project will leverage Spec-Kit Plus and Claude Code for spec-driven development, aiming for high quality, accessibility, and potential for advanced features.

---

## 1. Book Requirements (Frontend - Docusaurus)

### 1.1 Content
*   **Topic**: Physical AI & Humanoid Robotics.
*   **Structure**: 10-12 well-structured chapters based on the provided course details (Modules and Weekly Breakdown).
    *   **Module 1**: The Robotic Nervous System (ROS 2)
    *   **Module 2**: The Digital Twin (Gazebo & Unity)
    *   **Module 3**: The AI-Robot Brain (NVIDIA Isaac™)
    *   **Module 4**: Vision-Language-Action (VLA)
    *   **Weekly Breakdown**: Content for each week will be structured into chapters.
*   **Chapter Length**: Each chapter aims for 2000-4000 words.
*   **Learning Outcomes**: Content must address the specified learning outcomes for the course.
*   **Assessments**: Include sections related to the course assessments.

### 1.2 Formatting & Presentation
*   **Platform**: Docusaurus 3.9 for static site generation.
*   **Professional Formatting**: Consistent layout, typography, and styling.
*   **Code Examples**: Include relevant code snippets with syntax highlighting.
*   **Images & Diagrams**: Utilize images and Mermaid diagrams for conceptual clarity.
*   **SEO Optimized**: Proper meta tags, sitemaps, and accessible URLs.
*   **Mobile Responsive**: Fully functional and aesthetically pleasing on various screen sizes (mobile-first design).
*   **Accessible**: WCAG AA compliant.
*   **Modern UI**: Gradient themes with smooth animations as per README.md.

### 1.3 Deployment
*   **Target**: GitHub Pages.
*   **Automation**: Automated deployment via GitHub Actions (CI/CD pipeline).

---

## 2. RAG Chatbot Requirements (Backend - FastAPI & Frontend Integration)

### 2.1 Core Functionality
*   **Embedding**: Embedded within the book interface (React ChatWidget component).
*   **Contextual Q&A**: Must be able to answer user questions about the book's content.
*   **Text Selection Q&A**: Ability to highlight text in the book and ask specific questions based on the selected context.

### 2.2 Backend (FastAPI)
*   **Framework**: FastAPI with Python 3.11+.
*   **RAG Pipeline**:
    *   **Embedder**: OpenAI `text-embedding-3-small`.
    *   **Vector Database**: Qdrant Cloud Free Tier (to store book content embeddings).
    *   **Generator**: OpenAI `gpt-4o-mini` for response generation.
    *   **Chunking**: Intelligent document chunking and overlap management.
*   **API Endpoints**:
    *   `/api/v1/chat`: General chat endpoint.
    *   `/api/v1/chat/selection`: Endpoint for text selection-based Q&A.
    *   `/api/v1/embed`: Endpoint for document ingestion (to populate Qdrant).
    *   `/api/v1/health`: Health check endpoint.
*   **Streaming Responses**: Implement real-time token streaming for better User Experience.
*   **Error Handling**: Robust error handling, rate limiting, and security best practices.
*   **Configuration**: Environment variable management (OpenAI keys, Qdrant URL/Key, etc.).
*   **Deployment**: Render/Vercel (using free tier).

### 2.3 Frontend Integration (React ChatWidget)
*   **Component**: React ChatWidget component within Docusaurus.
*   **Features**:
    *   Text selection detection and context submission.
    *   Display streaming responses.
    *   Mobile-responsive UI.
    *   Accessible (WCAG AA).
    *   Modern UI.

---

## 3. General Project Requirements

### 3.1 Spec-Driven Development (SDD)
*   Utilize Spec-Kit Plus for the entire development workflow.
*   Follow the `/sp.constitution` → `/sp.specify` → `/sp.clarify` → `/sp.plan` → `/sp.tasks` → `/sp.implement` cycle.
*   Maintain Prompt History Records (PHRs) and Architectural Decision Records (ADRs) where applicable.

### 3.2 Claude Code Integration
*   Leverage Claude Code Subagents for specialized tasks (e.g., Docusaurus Architect, RAG Specialist, Content Writer).
*   Utilize reusable Agent Skills (e.g., Book Structure Generator, RAG Pipeline Builder, Chatbot Widget Creator).

### 3.3 Documentation
*   Comprehensive `README.md` including setup, deployment, troubleshooting, API documentation.
*   Clear inline documentation (docstrings) for all public functions.
*   Comments explaining non-obvious decisions.

### 3.4 Testing
*   Unit, Integration, and E2E tests for both frontend and backend.
*   Specific tests for RAG system accuracy and performance.

---

## 4. Bonus Features (Prioritized if Core Requirements are Met)

### 4.1 Reusable Intelligence (Claude Code) - Up to 50 extra points
*   **Custom Subagents**: (5 specialized subagents already outlined in README.md).
*   **Reusable Skills**: (3 reusable skills already outlined in README.md).
*   **Documentation**: Thorough documentation on how subagents and skills were used, including their purpose, functionality, and reusability.

### 4.2 User Authentication & Personalization - Up to 50 extra points
*   **Signup/Signin**: Implement using Better Auth (`https://www.better-auth.com/`).
*   **User Background**: At signup, ask questions about software and hardware background.
*   **Personalized Content**: Logged-in users can personalize chapter content based on their background (e.g., beginner vs. advanced explanations, different code examples). This requires a button at the start of each chapter.

### 4.3 Multilingual Support - Up to 50 extra points
*   **Urdu Translation**: Logged-in users can translate chapter content into Urdu via a button at the start of each chapter.

---

## 5. Non-Functional Requirements

### 5.1 Performance
*   **Book**: Lighthouse Performance 90+, First Contentful Paint < 1.5s.
*   **Chatbot**: RAG Retrieval Latency < 500ms, First Token Latency < 1s, Streaming Token Latency < 100ms.

### 5.2 Reliability
*   Robust error handling for API calls, network issues, and LLM responses.
*   Graceful degradation if external services (OpenAI, Qdrant) are unavailable.

### 5.3 Security
*   API keys managed via environment variables (never hardcoded/committed).
*   CORS properly configured.
*   Input validation on all API endpoints.

### 5.4 Maintainability
*   Clean code adhering to SOLID principles and DRY.
*   Comprehensive testing suite.
*   Clear project structure.

### 5.5 Cost Optimization
*   Utilize free tiers for Qdrant, Vercel/Render.
*   Efficient OpenAI usage (e.g., `text-embedding-3-small`, `gpt-4o-mini`).

---

## 6. Project Timeline (Adjusted from README.md to reflect current date)

*   **Day 0 (Dec 3)**: Setup, constitution, **specification (current step)**.
*   **Day 1 (Dec 4)**: Clarification, planning, detailed tasks for Docusaurus & Book Content.
*   **Day 2 (Dec 5)**: Implement Docusaurus setup, start book content creation (Chapters 1-5).
*   **Day 3 (Dec 6)**: Continue book content creation (Chapters 6-10), start RAG backend development.
*   **Day 4 (Dec 7)**: Finish RAG backend, start frontend integration, deployment.
*   **Day 5 (Dec 8)**: Integration testing, polish, bonus features (if time), submission.

---

## 7. Acceptance Criteria (High-Level)

*   Book is accessible via GitHub Pages link.
*   Book contains 10-12 chapters on "Physical AI & Humanoid Robotics".
*   RAG Chatbot is embedded in the book and answers questions accurately.
*   Text selection Q&A works.
*   Frontend and Backend deployed.
*   All required API keys are configured via environment variables.
*   Project adheres to Spec-Driven Development principles.
*   All bonus features implemented and documented (if time permits).