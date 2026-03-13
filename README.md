# Quillflow — Multi-Agent Blog Generation System with Quality Assurance

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen)](https://YOUR-URL.onrender.com)

A production-grade, agentic AI blog generation system that uses a 7-node LangGraph pipeline to outline, write, self-review, and refine publish-ready blog content from a single topic. Features a real-time streaming frontend with pipeline visualization.

## Overview

Quillflow replaces the traditional "single-prompt → single-response" approach with a multi-agent pipeline where each stage is handled by a specialized node. The system plans content through an outline, writes section-by-section, self-reviews using an LLM-as-judge pattern, and iteratively rewrites until quality thresholds are met — all orchestrated by LangGraph.

**What makes it agentic:**

- **Decision-making** — Conditional routing based on quality scores (pass/rewrite)
- **Self-evaluation** — LLM-as-judge scores content 1–10 on coherence, depth, and engagement
- **Iterative refinement** — Automatic rewrites with review feedback, capped at 2 iterations
- **Multi-model orchestration** — Routes between fast (8B) and quality (70B) models per task

## Key Features

- **7-Node Agentic Pipeline** — Outline → Title → Intro → Sections → Takeaways → Review → (conditional rewrite)
- **Dual Model Strategy** — LLaMA 3.1 8B for speed-critical tasks, LLaMA 3.3 70B for quality-critical tasks
- **Self-Review Loop** — LLM-as-judge with automatic rewrite routing for scores < 7/10
- **Multi-Language Support** — Generate blogs in English, Hindi, Spanish, French, German, Japanese
- **Real-Time Pipeline Visualization** — SSE streaming shows each node completing live in the browser
- **BYOK (Bring Your Own Key)** — Users provide their own Groq API key; no server-side key storage
- **Structured Output** — Pydantic models enforce schema at every pipeline stage
- **Retry with Exponential Backoff** — Automatic retry on LLM failures (max 2 retries)
- **27 Automated Tests** — Unit, integration, and API tests with CI/CD via GitHub Actions

## System Architecture

```
                    ┌──────────────┐
                    │   __start__  │
                    └──────┬───────┘
                           ↓
                ┌────────────────────┐
                │  Outline Generation │  ← fast_llm (8B)
                └──────────┬─────────┘
                           ↓
                ┌────────────────────┐
                │   Title Creation    │  ← fast_llm (8B)
                └──────────┬─────────┘
                           ↓
                ┌────────────────────┐
                │  Intro Generation   │  ← quality_llm (70B)
                └──────────┬─────────┘
                           ↓
              ┌──────────────────────────┐
         ┌──→ │   Section Generation      │  ← quality_llm (70B)
         │    └──────────┬───────────────┘
         │               ↓
         │    ┌────────────────────┐
         │    │   Takeaways & CTA   │  ← quality_llm (70B)
         │    └──────────┬─────────┘
         │               ↓
         │    ┌────────────────────┐
         │    │      Review         │  ← quality_llm (70B)
         │    └───┬──────────┬─────┘
         │        │          │
         │   score < 7   score ≥ 7
         │   (rewrite)    (pass)
         │        │          │
         └────────┘    ┌─────┴──────┐
                       │  __end__   │  (or Translation → __end__)
                       └────────────┘
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| AI Orchestration | LangGraph | Multi-agent graph with conditional routing |
| LLM Framework | LangChain | Structured output, prompt management |
| LLM Provider | Groq (LLaMA 3.3 70B, LLaMA 3.1 8B) | Fast inference with dual model strategy |
| Data Validation | Pydantic | Blog schema, request validation |
| API | FastAPI | REST + SSE streaming endpoints |
| Server | Uvicorn | ASGI server |
| Frontend | HTML / CSS / JavaScript | Glassmorphism UI with real-time pipeline viz |
| Testing | pytest | 27 tests (unit + integration + API) |
| Containerization | Docker | Production deployment |
| CI/CD | GitHub Actions | Automated test + Docker build pipeline |

## Project Structure

```
├── app.py                          # FastAPI application (REST + SSE endpoints)
├── Dockerfile                      # Production container (Python 3.13-slim)
├── requirements.txt                # Python dependencies
├── static/
│   ├── index.html                  # Single-page frontend (landing + results)
│   ├── style.css                   # Glassmorphism dark theme + animations
│   └── script.js                   # SSE streaming, pipeline viz, state management
├── src/
│   ├── graphs/
│   │   └── graph_builder.py        # LangGraph wiring (topic + language graphs)
│   ├── llms/
│   │   └── groqllm.py              # Dual LLM configuration (8B fast + 70B quality)
│   ├── nodes/
│   │   └── blog_node.py            # 7 pipeline nodes + review decision logic
│   ├── states/
│   │   └── blogstate.py            # Pydantic models (Blog, BlogOutline, ReviewResult)
│   └── utils/
│       ├── logger.py               # Structured logging
│       └── retry.py                # Retry with exponential backoff
├── tests/
│   ├── conftest.py                 # Shared fixtures (mock LLMs, sample data)
│   ├── test_nodes.py               # 22 unit tests for all 7 nodes
│   ├── test_pipeline.py            # 2 integration tests (full pipeline + review loop)
│   └── test_api.py                 # 3 API endpoint tests
└── .github/
    └── workflows/
        └── ci.yml                  # CI pipeline: test → Docker build
```

## How It Works

### Pipeline Execution

1. **Outline Generation** — Produces 3–5 structured sections with key points per section using the fast model
2. **Title Creation** — Generates SEO-optimized title and meta description from the outline
3. **Intro Generation** — Writes a hook-driven introduction using the quality model
4. **Section Generation** — Writes each section independently using outline key points as guidance
5. **Takeaways & CTA** — Extracts key takeaways and generates a closing call-to-action
6. **Review** — LLM-as-judge scores the blog 1–10; returns feedback if score < 7
7. **Conditional Routing** — Scores ≥ 7 pass to end; scores < 7 route back to section rewrite (max 2 loops)
8. **Translation** *(optional)* — Translates the complete blog while preserving structure and formatting

### Real-Time Streaming

The frontend connects to `POST /blogs/stream` which uses LangGraph's `graph.stream()` to yield per-node results. Each node completion is sent as a Server-Sent Event (SSE), updating the pipeline visualization, blog content, and review score in real time.

## Setup & Installation

### Prerequisites

- Python 3.13+
- [Groq API Key](https://console.groq.com/) (free tier available)

### Install

```bash
git clone https://github.com/ShubhamPawar-3333/Multi-Agent-Blog-Generation-System.git
cd Multi-Agent-Blog-Generation-System

python -m venv .venv
source .venv/Scripts/activate    # Windows
# source .venv/bin/activate      # macOS/Linux

pip install -r requirements.txt
```

### Environment Variables

Create `.env` in project root (only needed for LangSmith tracing, optional):

```env
LANGCHAIN_API_KEY=your_langchain_key
```

> **Note:** The Groq API key is provided by the user through the frontend — no server-side key required.

### Run

```bash
python app.py
```

Open `http://localhost:8000` in your browser.

### Run Tests

```bash
pytest tests/ -v
```

### Docker

```bash
docker build -t quillflow .
docker run -p 8000:8000 quillflow
```

### Live Demo

Visit [https://YOUR-URL.onrender.com](https://YOUR-URL.onrender.com)

## Usage

### Web Interface

1. Enter your **Groq API key** in the top-right input
2. Type a **blog topic** (e.g., "AI in Healthcare")
3. Optionally select a **language** for translation
4. Click **Generate Blog** and watch the pipeline execute in real time
5. Copy the generated blog with one click

### API (Direct)

```bash
# Standard endpoint
curl -X POST http://localhost:8000/blogs \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI in Healthcare", "language": "hindi", "api_key": "your-groq-key"}'

# Streaming endpoint (SSE)
curl -X POST http://localhost:8000/blogs/stream \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI in Healthcare", "api_key": "your-groq-key"}'
```

## Future Improvements

- **Async Execution** — `asyncio.to_thread()` for concurrent request handling
- **Web Search Integration** — Tavily/SerpAPI for research-backed content
- **Human-in-the-Loop** — Manual review/edit checkpoint before publishing
- **Dynamic Section Count** — Adjust depth based on topic complexity
- **Intelligent Model Selection** — Auto-select model based on topic difficulty
