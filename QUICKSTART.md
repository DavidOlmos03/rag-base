# RAG Base Service - Quick Start Guide

Get the RAG Base Service running in **5 minutes**!

## Prerequisites

- Docker & Docker Compose installed
- Git
- **Ollama installed locally** (https://ollama.ai)

## 🚀 Start in 4 Steps

### 1. Clone and Configure

```bash
git clone <repository-url>
cd rag-docs
cp .env.example .env
```

**Important:** Edit `.env` and ensure the security keys have at least 32 characters:
```bash
SECRET_KEY=dev-secret-key-12345678901234567890123456789012
JWT_SECRET_KEY=dev-jwt-secret-key-1234567890123456789012
```

### 2. Start All Services

```bash
docker-compose -f docker-compose.dev.yml up -d
```

This starts:
- ✅ FastAPI (port 8000)
- ✅ PostgreSQL (port 5432)
- ✅ Redis (port 6379)
- ✅ Qdrant (port 6333)
- ✅ PGAdmin (port 5050)
- ✅ Redis Commander (port 8081)

**Note:** The project uses your **local Ollama instance** (not a Docker container) for better performance.

### 3. Initialize Database

```bash
docker exec -it ragbase-api-dev poetry run python scripts/init_db.py
```

### 4. Access the API

**API Documentation:** http://localhost:8000/api/v1/docs

**Test the health endpoint:**
```bash
curl http://localhost:8000/api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "service": "RAG Base Service",
  "version": "0.1.0"
}
```

## 🎯 Next Steps

### Pull Ollama Models (for local LLM)

The default model is **phi3:mini**. Pull it using your local Ollama:

```bash
ollama pull phi3:mini
```

Optional models you can also try:
```bash
ollama pull llama3
ollama pull mistral
ollama pull qwen2.5
```

Verify installed models:
```bash
ollama list
```

### Access Development Tools

- **API Docs (Swagger):** http://localhost:8000/api/v1/docs
- **API Docs (ReDoc):** http://localhost:8000/api/v1/redoc
- **PGAdmin:** http://localhost:5050
  - Email: `admin@ragbase.local`
  - Password: `admin`
- **Redis Commander:** http://localhost:8081
- **Qdrant Dashboard:** http://localhost:6333/dashboard

### Test Credentials (Development Only)

After running `init_db.py`:
- **Email:** test@example.com
- **Password:** testpassword123

## 📝 Common Commands

### View Logs

```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f api
```

### Stop Services

```bash
docker-compose -f docker-compose.dev.yml down
```

### Restart API Only

```bash
docker-compose -f docker-compose.dev.yml restart api
```

### Access API Container

```bash
docker exec -it ragbase-api-dev bash
```

## 🧪 Local Development (without Docker)

### 1. Install Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Install Dependencies

```bash
poetry install
```

### 3. Start Infrastructure Only

```bash
docker-compose -f docker-compose.dev.yml up -d postgres redis qdrant
```

**Note:** Ollama should be running locally on your system.

### 4. Run Migrations

```bash
poetry run alembic upgrade head
```

### 5. Start API

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🐛 Troubleshooting

### Verify Ollama is running

```bash
# Check if Ollama is running locally
curl http://localhost:11434/api/version

# If not running, start it
ollama serve
```

### Services won't start

```bash
# Check status
docker-compose -f docker-compose.dev.yml ps

# Rebuild
docker-compose -f docker-compose.dev.yml up -d --build
```

### Database connection errors

```bash
# Check PostgreSQL logs
docker-compose -f docker-compose.dev.yml logs postgres

# Restart database
docker-compose -f docker-compose.dev.yml restart postgres
```

### Port already in use

Edit `docker-compose.dev.yml` and change the port mappings:
```yaml
ports:
  - "8001:8000"  # Changed from 8000:8000
```

### Ollama connection errors

If the API can't connect to Ollama:
1. Verify Ollama is running: `curl http://localhost:11434/api/version`
2. Check that phi3:mini is installed: `ollama list`
3. Verify the model works: `ollama run phi3:mini "Hello"`

## 📚 What's Next?

1. **Read the full README:** Check `README.md` for detailed documentation
2. **Check implementation status:** See `IMPLEMENTATION_STATUS.md`
3. **Start developing:** Follow patterns in existing code
4. **Run tests:** `poetry run pytest` (when tests are implemented)

## 🆘 Need Help?

- Check logs: `docker-compose -f docker-compose.dev.yml logs -f`
- Review configuration: `.env` file
- Read documentation: `README.md`
- Check status: `IMPLEMENTATION_STATUS.md`

---

**You're all set! Start building your RAG application! 🚀**
