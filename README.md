# 📚 **AI-Driven Book with RAG Chatbot - Hackathon Project**

[![Docusaurus](https://img.shields.io/badge/Docusaurus-3.9-green.svg)](https://docusaurus.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688.svg)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-Embeddings%20%26%20GPT--4o--mini-412991.svg)](https://openai.com/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-DC244C.svg)](https://qdrant.tech/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Deploy to Hugging Face Spaces](https://img.shields.io/badge/Deploy-HF%20Spaces-blue)](https://huggingface.co/spaces/mrowaisabdullah/ai-humanoid-robotics)
[![GitHub Pages](https://img.shields.io/badge/Deploy-GitHub%20Pages-blue)](https://mrowaisabdullah.github.io/ai-humanoid-robotics/)

> **GIAIC Saturday Afternoon Students - AI/Spec-Driven Hackathon 1**  
> Submission Deadline: Sunday, Dec 7th @ 11:59 PM

---

## 🎯 **Project Overview**

A comprehensive, production-ready educational book built using **Spec-Driven Development** with Claude Code, featuring an embedded RAG (Retrieval-Augmented Generation) chatbot for interactive Q&A.

### **Key Features**

- 📖 **10+ Chapter Educational Book** - Built with Docusaurus 3.9
- 🤖 **Intelligent RAG Chatbot** - Answers questions about book content
- ✨ **Text Selection Q&A** - Highlight text and ask specific questions
- 🚀 **Streaming Responses** - Real-time token streaming for better UX
- 📱 **Fully Responsive** - Mobile-first design
- ♿ **Accessible** - WCAG AA compliant
- 🎨 **Modern UI** - Gradient themes with smooth animations
- 🔒 **Production-Ready** - Error handling, rate limiting, security best practices

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Pages (Frontend)                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Docusaurus 3.9 (Static Site)             │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │        React ChatWidget Component            │  │   │
│  │  │  • Text Selection Detection                  │  │   │
│  │  │  • Streaming Response Display                │  │   │
│  │  │  • Mobile-Responsive UI                      │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────────────────┐
│            Hugging Face Spaces (Backend - FastAPI)         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  RAG Pipeline                        │   │
│  │  ┌────────────┐  ┌──────────┐  ┌───────────────┐  │   │
│  │  │  Embedder  │→ │ Qdrant   │→ │   Generator   │  │   │
│  │  │  (OpenAI)  │  │ (Vector  │  │   (OpenAI     │  │   │
│  │  │            │  │  Search) │  │   GPT-4o-mini)│  │   │
│  │  └────────────┘  └──────────┘  └───────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 🌐 **Live Demo**

- **📖 Book**: https://mrowaisabdullah.github.io/ai-humanoid-robotics/
- **💬 Chat API**: https://mrowaisabdullah-ai-humanoid-robotics.hf.space
- **🚀 Health Check**: https://mrowaisabdullah-ai-humanoid-robotics.hf.space/health

---

## 🚀 **Quick Start**

### **Prerequisites**

- Node.js 18.x or higher
- Python 3.11 or higher
- Git
- Claude Code (with free Gemini API or GLM-4-6)
- Spec-Kit Plus

### **Installation**

1. **Clone the repository**
   ```bash
   git clone https://github.com/mrowaisabdullah/ai-book.git
   cd ai-book
   ```

2. **Install Spec-Kit Plus**
   ```bash
   pip install specifyplus
   # or
   uv tool install specifyplus
   ```

3. **Initialize Project**
   ```bash
   # Verify installation
   specifyplus check
   
   # Initialize (if starting fresh)
   specifyplus init . --ai claude --force
   ```

4. **Install Frontend Dependencies**
   ```bash
   npm install
   
   # Install Tailwind CSS v4
   npm install --save-dev tailwindcss @tailwindcss/postcss postcss
   ```

5. **Configure Tailwind v4**
   
   *Create `src/plugins/tailwind-config.js`:*
   ```javascript
   module.exports = function tailwindPlugin(context, options) {
     return {
       name: "tailwind-plugin",
       configurePostCss(postcssOptions) {
         postcssOptions.plugins.push(require("@tailwindcss/postcss"));
         return postcssOptions;
       },
     };
   };
   ```

   *Update `docusaurus.config.js` to register the plugin:*
   ```javascript
   export default {
     // ...
     plugins: [
       './src/plugins/tailwind-config.js',
     ],
     // ...
   };
   ```

   *Update `src/css/custom.css`:*
   ```css
   @import "tailwindcss";
   ```

6. **Install Backend Dependencies**
   ```bash
   cd chatbot
   pip install -r requirements.txt
   ```

---

## ⚙️ **Configuration**

### **Environment Variables**

#### **Frontend** (`.env`)

```bash
# Chatbot API endpoint
REACT_APP_CHATBOT_API_URL=https://your-backend.vercel.app
```

#### **Backend** (`chatbot/.env`)

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_COMPLETION_MODEL=gpt-4o-mini

# Qdrant Configuration
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key-here
QDRANT_COLLECTION_NAME=book_content

# API Configuration
ALLOWED_ORIGINS=https://mrowaisabdullah.github.io,http://localhost:3000

# RAG Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=5
```

### **Get Your API Keys**

1. **OpenAI API Key**: https://platform.openai.com/api-keys
2. **Qdrant Cloud**: https://cloud.qdrant.io/ (Free tier available)

---

## 🚀 **Deployment**

### **Production URLs**
- 📖 **Frontend**: https://mrowaisabdullah.github.io/ai-humanoid-robotics/
- 💬 **Backend API**: https://mrowaisabdullah-ai-humanoid-robotics.hf.space

### **Automated Deployment**

The application is configured for automatic deployment:

1. **Backend to Hugging Face Spaces**
   - Push changes to `backend/` directory
   - GitHub Actions deploys to HF Spaces
   - Requires `HF_TOKEN` secret in GitHub repo

2. **Frontend to GitHub Pages**
   - Push changes to `src/` or `docs/`
   - GitHub Actions builds and deploys
   - No additional configuration needed

### **Manual Deployment**

For manual deployment or local testing:

1. **Backend**:
   ```bash
   cd backend
   chmod +x scripts/deploy_hf.sh
   ./scripts/deploy_hf.sh mrowaisabdullah-ai-humanoid-robotics
   ```

2. **Frontend**:
   ```bash
   npm run build
   npm run deploy:gh
   ```

### **Environment Setup**
Copy `.env.example` to `.env` and configure:
- `OPENAI_API_KEY`: Your OpenAI API key
- `QDRANT_URL`: Your Qdrant instance URL
- `REACT_APP_CHAT_API_URL`: Production backend URL

### **Detailed Guide**
See [Deployment Guide](docs/deployment.md) for complete instructions.

---

## 🎓 **Development Workflow (Spec-Driven)**

This project follows **Spec-Driven Development** methodology using Spec-Kit Plus.

### **Step 1: Constitution**

Define project principles and standards:

```bash
claude  # Start Claude Code
```

```
/constitution
Create principles focused on:
- Clean, maintainable code following SOLID principles
- Comprehensive documentation
- User-centric design
- Performance optimization
- Accessibility standards (WCAG AA)
- RAG system accuracy
- Rapid development without compromising quality
```

### **Step 2: Specification**

Define what to build:

```
/specify
Build a comprehensive book on [TOPIC - announced Dec 3rd 8PM].

Book Requirements:
- 10-12 well-structured chapters
- Professional formatting with code examples
- Images and diagrams (Mermaid)
- SEO optimized
- Mobile responsive
- Deployed to GitHub Pages

RAG Chatbot Requirements:
- Embedded chatbot in book interface
- Answer questions about book content
- Support text selection Q&A
- FastAPI backend
- Qdrant Cloud vector database
- OpenAI embeddings and completions
- Streaming responses
- Error handling

[See SPECIFICATION.md for full details]
```

### **Step 3: Clarification**

```
/clarify
```

Answer Claude's questions to refine requirements.

### **Step 4: Planning**

```
/plan
Tech Stack:
- Frontend: Docusaurus 3.9 + React + TypeScript + Tailwind CSS
- Backend: FastAPI + Python 3.11
- Vector DB: Qdrant Cloud (free tier)
- Embeddings: OpenAI text-embedding-3-small
- LLM: OpenAI GPT-4o-mini
- Deployment: GitHub Pages (frontend) + Render/Vercel (backend)
```

### **Step 5: Task Breakdown**

```
/tasks
```

### **Step 6: Implementation**

```
/implement
```

Claude Code will execute all tasks automatically.

---

## 🤖 **Claude Code Subagents & Skills**

This project leverages **5 specialized subagents** and **3 reusable skills** for efficient development:

### **Subagents** (`.claude/agents/`)

1. **Docusaurus Architect** - Docusaurus configuration, deployment, SEO
2. **RAG Specialist** - RAG pipeline, embeddings, vector search
3. **ChatKit Integrator** - React chatbot UI, streaming, state management
4. **Content Writer** - Educational content creation, technical writing
5. **Deployment Engineer** - CI/CD, GitHub Actions, cloud deployment

### **Skills** (`.claude/skills/`)

1. **Book Structure Generator** - Chapter templates, sidebar configuration
2. **RAG Pipeline Builder** - Complete RAG implementation templates
3. **Chatbot Widget Creator** - Ready-to-use React components

**Learn more:** [SUBAGENTS.md](./SUBAGENTS.md) | [SKILLS.md](./SKILLS.md)

---

## 📂 **Project Structure**

```
.
├── .claude/
│   ├── agents/              # 5 specialized subagents
│   │   ├── docusaurus-architect.md
│   │   ├── rag-specialist.md
│   │   ├── chatkit-integrator.md
│   │   ├── content-writer.md
│   │   └── deployment-engineer.md
│   └── skills/              # 3 reusable skills
│       ├── book-structure-generator/
│       ├── rag-pipeline-builder/
│       └── chatbot-widget-creator/
├── .github/
│   └── workflows/
│       └── deploy.yml       # GitHub Actions CI/CD
├── .specify/
│   ├── memory/
│   │   └── constitution.md  # Project principles
│   ├── specs/               # Feature specifications
│   └── templates/           # Spec templates
├── docs/                    # Book chapters (Markdown)
│   ├── index.md
│   ├── part-1-foundation/
│   ├── part-2-core/
│   ├── part-3-advanced/
│   └── appendices/
├── src/
│   ├── components/
│   │   └── ChatWidget/      # React chatbot component
│   ├── css/
│   │   └── custom.css       # Custom theming
│   └── theme/
│       └── Root.tsx         # Global component injection
├── static/                  # Images, assets
├── chatbot/                 # FastAPI backend
│   ├── api/
│   │   ├── main.py          # FastAPI app
│   │   └── routes/
│   │       ├── chat.py      # Chat endpoints
│   │       ├── embed.py     # Document ingestion
│   │       └── health.py    # Health checks
│   ├── rag/
│   │   ├── chunker.py       # Document chunking
│   │   ├── embedder.py      # OpenAI embeddings
│   │   ├── retriever.py     # Qdrant retrieval
│   │   ├── generator.py     # Response generation
│   │   └── pipeline.py      # RAG orchestration
│   ├── core/
│   │   ├── config.py        # Settings management
│   │   ├── logging_config.py
│   │   └── errors.py
│   ├── tests/
│   ├── scripts/
│   │   └── ingest_documents.py
│   └── requirements.txt
├── docusaurus.config.js     # Docusaurus configuration
├── sidebars.js              # Sidebar navigation
├── src/
│   ├── plugins/
│   │   └── tailwind-config.js # Tailwind PostCSS plugin
│   └── css/
│       └── custom.css       # Tailwind @import
├── package.json
└── README.md
```

---

## 🛠️ **Local Development**

### **Frontend (Docusaurus)**

```bash
# Start development server
npm start

# Build for production
npm run build

# Serve production build
npm run serve
```

Visit: http://localhost:3000

### **Backend (FastAPI)**

```bash
cd chatbot

# Run development server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Or with script
python scripts/run_dev.py
```

API docs: http://localhost:8000/docs

### **Ingest Book Content**

```bash
cd chatbot

# Ingest all markdown files into Qdrant
python scripts/ingest_documents.py
```

This will:
1. Read all `.md` files from `docs/`
2. Chunk documents intelligently
3. Generate embeddings via OpenAI
4. Store in Qdrant vector database

---

## 🚀 **Deployment**

### **Frontend (GitHub Pages)**

Automatic deployment via GitHub Actions on push to `main`:

```bash
git add .
git commit -m "Update book content"
git push origin main
```

GitHub Actions will:
1. Build Docusaurus site
2. Deploy to `gh-pages` branch
3. Available at: `https://mrowaisabdullah.github.io/ai-book`

**Manual deployment:**
```bash
npm run deploy
```

### **Backend (Render)**

1. **Connect Repository**
   - Go to https://render.com
   - Create new Web Service
   - Connect GitHub repo

2. **Configure Service**
   - Build Command: `pip install -r chatbot/requirements.txt`
   - Start Command: `cd chatbot && uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - Add environment variables (see Configuration)

3. **Deploy**
   - Render auto-deploys on push to `main`

**Alternative: Vercel**
```bash
cd chatbot
vercel --prod
```

---

## 🧪 **Testing**

### **Frontend Tests**

```bash
npm test
```

### **Backend Tests**

```bash
cd chatbot
pytest tests/ -v
```

### **RAG System Test**

```bash
cd chatbot
python scripts/test_rag.py
```

Expected output:
```
✓ Document ingestion: 150 chunks created
✓ Query retrieval: Top 5 relevant chunks retrieved
✓ Response generation: Streaming successful
✓ Text selection Q&A: Context properly filtered
```

---

## 📊 **Performance Metrics**

### **Target Metrics**

| Metric | Target | Current |
|--------|--------|---------|
| Lighthouse Performance | 90+ | TBD |
| Lighthouse Accessibility | 90+ | TBD |
| First Contentful Paint | < 1.5s | TBD |
| RAG Retrieval Latency | < 500ms | TBD |
| First Token Latency | < 1s | TBD |
| Streaming Token Latency | < 100ms | TBD |

### **Cost Estimates**

| Service | Usage | Cost (Monthly) |
|---------|-------|----------------|
| OpenAI Embeddings | ~30K words | ~$0.05 |
| OpenAI Completions | ~1K queries | ~$0.50 |
| Qdrant Cloud | Free tier | $0 |
| Vercel/Render | Free tier | $0 |
| **Total** | | **~$0.55/month** |

---

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Frontend: Chatbot not loading**

```bash
# Check API URL
echo $REACT_APP_CHATBOT_API_URL

# Test backend connectivity
curl https://your-backend.vercel.app/api/v1/health
```

#### **Backend: CORS errors**

```python
# Verify ALLOWED_ORIGINS in chatbot/.env
ALLOWED_ORIGINS=https://mrowaisabdullah.github.io,http://localhost:3000
```

#### **RAG: Low relevance scores**

```python
# Adjust chunk size in chatbot/.env
CHUNK_SIZE=800  # Try smaller chunks
CHUNK_OVERLAP=200

# Re-ingest documents
python scripts/ingest_documents.py
```

#### **Deployment: GitHub Pages 404**

```javascript
// Check baseUrl in docusaurus.config.js
baseUrl: '/ai-book/',  // Must match repository name
```

---

## 📚 **Documentation**

- **[SPECIFICATION.md](./SPECIFICATION.md)** - Complete project specifications
- **[SUBAGENTS.md](./SUBAGENTS.md)** - Subagent documentation and usage
- **[SKILLS.md](./SKILLS.md)** - Reusable skills library
- **[API.md](./API.md)** - Backend API documentation
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Detailed deployment guide
- **[CONTRIBUTING.md](./CONTRIBUTING.md)** - Contribution guidelines

---

## 🏆 **Hackathon Deliverables**

### **Required**

- ✅ AI/Spec-Driven Book (10+ chapters)
- ✅ RAG Chatbot Integration
- ✅ Text Selection Q&A Feature
- ✅ GitHub Pages Deployment
- ✅ FastAPI Backend
- ✅ Qdrant Vector Database
- ✅ OpenAI Embeddings & Completions

### **Bonus Features**

- ✅ Custom Subagents (5 specialized)
- ✅ Reusable Skills (3 template libraries)
- ✅ Streaming Responses
- ✅ Mobile-Responsive UI
- ✅ WCAG AA Accessibility
- ✅ Production-Ready Error Handling
- ✅ CI/CD Pipeline (GitHub Actions)
- ✅ Comprehensive Documentation

---

## 📈 **Project Timeline**

| Day | Date | Tasks |
|-----|------|-------|
| **Day 0** | Dec 2 | Setup, subagents/skills creation, practice |
| **Day 1** | Dec 3 | Constitution, specification, planning (after 8 PM) |
| **Day 2** | Dec 4 | Book content creation (10 chapters) |
| **Day 3** | Dec 5 | RAG backend development |
| **Day 4** | Dec 6 | Frontend integration, deployment |
| **Day 5** | Dec 7 | Testing, polish, submission |

---

## 👥 **Team**

- **Developer**: Owais Abdullah
- **Mentor**: Claude Code (with Spec-Kit Plus)
- **Subagents**: 5 specialized AI assistants
- **Skills**: 3 reusable template libraries

---

## 🙏 **Acknowledgements**

- **GIAIC** - For organizing the hackathon
- **Panaversity** - For Spec-Kit Plus and AI-Native methodology
- **Anthropic** - For Claude Code and subagent capabilities
- **OpenAI** - For embeddings and completion APIs
- **Qdrant** - For vector database infrastructure
- **Docusaurus Team** - For excellent documentation framework

---

## 📄 **License**

MIT License - see [LICENSE](LICENSE) for details

---

## 🔗 **Links**

- **Live Demo**: https://mrowaisabdullah.github.io/ai-book
- **API Documentation**: https://[backend-url]/docs
- **GitHub Repository**: https://github.com/mrowaisabdullah/ai-book
- **Hackathon Submission**: [Form Link]

---

## 📞 **Contact**

- **Email**: your.email @example.com
- **GitHub**: [ @mrowaisabdullah](https://github.com/mrowaisabdullah)
- **WhatsApp Group**: [Hackathon Group Link]

---

<div align="center">

**Built with ❤️ using Spec-Driven Development**

[Docusaurus](https://docusaurus.io/) • [FastAPI](https://fastapi.tiangolo.com/) • [OpenAI](https://openai.com/) • [Qdrant](https://qdrant.tech/) • [Claude Code](https://claude.ai/code)

**⭐ Star this repo if you find it helpful!**

</div>

---

## 🚧 **Project Status**

- [ ] Environment setup complete
- [ ] Subagents & skills created
- [ ] Constitution defined
- [ ] Book topic announced (Dec 3, 8 PM)
- [ ] Specification complete
- [ ] Book content (10 chapters)
- [ ] RAG backend implemented
- [ ] Chatbot frontend integrated
- [ ] Frontend deployed (GitHub Pages)
- [ ] Backend deployed (Render/Vercel)
- [ ] End-to-end testing complete
- [ ] Documentation complete
- [ ] Submitted (Dec 7, 11:59 PM)

---

**Last Updated**: December 2, 2024