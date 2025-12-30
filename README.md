# RAG Base Service

> **Retrieval-Augmented Generation as a Service** - Multi-tenant, Multi-LLM, Open-Source Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-00a393.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Overview

RAG Base Service is a production-ready, **domain-agnostic** RAG (Retrieval-Augmented Generation) platform built with Python and FastAPI. It serves as a reusable core for multiple projects requiring document-based question answering with LLMs.

### Key Features

- ✅ **Multi-Tenant Architecture** - Complete isolation between tenants
- 🔄 **Multi-LLM Support** - OpenAI, Anthropic, DeepSeek, Ollama (local)
- 🎯 **Provider-Agnostic** - Switch LLMs without re-indexing documents
- 💰 **Cost-Optimized** - Intelligent caching, embeddings optimization
- 🐳 **Fully Dockerized** - Development & production ready
- 📦 **Open-Source First** - No vendor lock-in
- 🔒 **Production-Ready** - Authentication, rate limiting, observability
- ⚡ **Async-First** - Built on FastAPI with full async support
- 📊 **Hybrid Search** - Vector + keyword retrieval

---

## 📋 Table of Contents

- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [API Documentation](#-api-documentation)
- [Development](#-development)
- [Deployment](#-deployment)
- [Cost Estimation](#-cost-estimation)
- [Contributing](#-contributing)

---

## 🏗 Architecture

### Technology Stack

**Backend:**
- Python 3.11+
- FastAPI (async web framework)
- Pydantic v2 (validation)
- SQLAlchemy 2.0+ (async ORM)
- Alembic (migrations)

**Data Stores:**
- **PostgreSQL** - Metadata, users, documents
- **Redis** - Caching, rate limiting
- **Qdrant** - Vector embeddings

**LLM Providers:**
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3)
- DeepSeek
- Ollama (local models)

**Embeddings:**
- SentenceTransformers (bge-m3, e5-large)
- Local and self-hosted

### RAG Pipeline

```
Document Upload
    ↓
Document Parser (PDF/DOCX/TXT)
    ↓
Chunking (configurable size/overlap)
    ↓
Embedding Generation (cached)
    ↓
Vector Store (Qdrant)
    ↓
Hybrid Retrieval (vector + keyword)
    ↓
Context Building & Compression
    ↓
LLM Generation (streaming supported)
    ↓
Response + Metadata
```

### Project Structure

```
rag-docs/
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Core config, security, logging
│   ├── domain/           # Business logic & interfaces
│   ├── infrastructure/   # Database, cache, vector store
│   ├── rag/              # RAG pipeline components
│   ├── adapters/         # LLM & external service adapters
│   ├── schemas/          # Pydantic schemas
│   └── main.py           # FastAPI application
│
├── tests/                # Unit & integration tests
├── docker/               # Dockerfiles
├── scripts/              # Utility scripts
├── alembic/              # Database migrations
└── docs/                 # Documentation
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Git

### 1. Clone the Repository

```bash
git clone <repository-url>
cd rag-docs
```

### 2. Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` with your configuration (see [Configuration](#-configuration))

### 3. Start with Docker Compose

**Development:**

```bash
docker-compose -f docker-compose.dev.yml up -d
```

**Production:**

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Access the API

- **API Docs (Swagger):** http://localhost:8000/api/v1/docs
- **Alternative Docs (ReDoc):** http://localhost:8000/api/v1/redoc
- **Health Check:** http://localhost:8000/api/v1/health

### 5. Optional: Pull Ollama Models

```bash
docker exec -it ragbase-ollama-dev ollama pull llama3
docker exec -it ragbase-ollama-dev ollama pull mistral
```

---

## 💻 Installation

### Option A: Docker (Recommended)

See [Quick Start](#-quick-start)

### Option B: Local Development

1. **Install Poetry:**

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. **Install Dependencies:**

```bash
poetry install
```

3. **Start Services (PostgreSQL, Redis, Qdrant):**

```bash
docker-compose -f docker-compose.dev.yml up -d postgres redis qdrant
```

4. **Run Migrations:**

```bash
poetry run alembic upgrade head
```

5. **Start API:**

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## ⚙ Configuration

### Environment Variables

Key configuration in `.env`:

```bash
# Application
SECRET_KEY=your-super-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production

# Database
DATABASE_URL=postgresql+asyncpg://raguser:ragpass@localhost:5432/ragbase

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant
QDRANT_URL=http://localhost:6333

# LLM Providers (Optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=...

# Ollama (Local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3

# Embeddings
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cpu  # cpu, cuda, mps

# RAG Settings
DEFAULT_CHUNK_SIZE=500
DEFAULT_CHUNK_OVERLAP=50
DEFAULT_TOP_K=5

# Cost Optimization
BUDGET_MODE=balanced  # minimal, balanced, premium
ENABLE_COST_TRACKING=True
```

### Budget Modes

- **minimal**: Ollama only (free, local)
- **balanced**: GPT-3.5-turbo + Ollama fallback
- **premium**: GPT-4 primary

---

## 📚 API Documentation

### Authentication

```http
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
```

### Documents

```http
POST   /api/v1/documents/upload
GET    /api/v1/documents
GET    /api/v1/documents/{id}
DELETE /api/v1/documents/{id}
```

### RAG Query

```http
POST /api/v1/query
POST /api/v1/query/stream
GET  /api/v1/query/history
```

### LLM Configuration

```http
GET   /api/v1/llm/providers
POST  /api/v1/llm/config
GET   /api/v1/llm/config
PATCH /api/v1/llm/config
POST  /api/v1/llm/test
```

### Health & Metrics

```http
GET /api/v1/health
GET /api/v1/metrics
```

**Full API documentation available at:** `/api/v1/docs`

---

## 🛠 Development

### Running Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=app --cov-report=html

# Specific test file
poetry run pytest tests/unit/test_config.py
```

### Code Quality

```bash
# Format code
poetry run black app tests

# Lint
poetry run ruff check app tests

# Type checking
poetry run mypy app
```

### Database Migrations

```bash
# Create migration
poetry run alembic revision --autogenerate -m "Description"

# Apply migrations
poetry run alembic upgrade head

# Rollback
poetry run alembic downgrade -1
```

### Development Tools

Access development UIs:

- **PGAdmin:** http://localhost:5050 (admin@ragbase.local / admin)
- **Redis Commander:** http://localhost:8081
- **Qdrant Dashboard:** http://localhost:6333/dashboard

---

## 🚢 Deployment

### Production Checklist

- [ ] Change `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=False`
- [ ] Configure proper CORS origins
- [ ] Use managed databases (optional)
- [ ] Set up SSL/TLS (nginx)
- [ ] Configure monitoring (Prometheus/Grafana)
- [ ] Set up backups
- [ ] Review rate limits
- [ ] Configure log aggregation

### Docker Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Scaling

The service is designed to scale horizontally:

- **API**: Multiple replicas behind load balancer
- **PostgreSQL**: Read replicas
- **Redis**: Cluster mode
- **Qdrant**: Distributed mode

---

## 💰 Cost Estimation

### Monthly Costs (Estimated)

**Minimal (Dev/Testing):**
- Self-hosted infrastructure: ~$20/month (VPS)
- Ollama (local): $0
- **Total: ~$20/month**

**Balanced (Small Production):**
- VPS (8GB RAM): $40/month
- Managed PostgreSQL: $15/month
- Managed Redis: $5/month
- Qdrant Cloud (1GB): $25/month
- OpenAI API (GPT-3.5, ~1M tokens): ~$2/month
- **Total: ~$87/month**

**Premium (Scaled Production):**
- Dedicated server: $160/month
- Managed databases: $70/month
- Qdrant Cloud (10GB): $250/month
- OpenAI API (GPT-4, ~2M tokens): ~$80/month
- **Total: ~$560/month**

### Cost Optimization Features

- ✅ Embedding cache (avoid re-embedding)
- ✅ Query response cache
- ✅ Batch embedding processing
- ✅ Local embeddings (free)
- ✅ Ollama for development/testing
- ✅ Token usage tracking

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards

- Follow PEP 8
- Write tests for new features
- Update documentation
- Use type hints
- Run linters before committing

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- FastAPI for the amazing web framework
- Qdrant for vector search
- SentenceTransformers for embeddings
- The open-source community

---

## 📧 Support

- **Issues:** [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-repo/discussions)
- **Email:** support@example.com

---

**Built with ❤️ for the open-source community**
