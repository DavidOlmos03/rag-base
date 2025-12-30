# Contributing to RAG Base Service

Thank you for your interest in contributing to RAG Base Service! This document provides guidelines and instructions for contributing.

## 🤝 How to Contribute

### Reporting Issues

1. Check if the issue already exists in [GitHub Issues](https://github.com/your-repo/issues)
2. Use the issue template if available
3. Provide detailed information:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Logs if applicable

### Suggesting Enhancements

1. Open a GitHub Issue with the label "enhancement"
2. Describe the feature and its benefits
3. Provide use cases and examples
4. Consider implementation details

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes following our guidelines**
4. **Write/update tests**
5. **Run quality checks:**
   ```bash
   make check-all
   make test
   ```
6. **Commit with clear messages:**
   ```bash
   git commit -m "feat: add hybrid search support"
   ```
7. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```
8. **Open a Pull Request**

## 📝 Development Guidelines

### Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting (line length: 88)
- **Ruff** for linting
- **MyPy** for type checking

Run all checks:
```bash
make format
make lint
make type-check
```

### Code Standards

1. **Type Hints:** Use type hints for all functions and methods
   ```python
   async def process_document(file_path: str, tenant_id: UUID) -> Document:
       ...
   ```

2. **Docstrings:** Use Google-style docstrings
   ```python
   def embed_text(text: str) -> list[float]:
       """Embed a single text.

       Args:
           text: Text to embed

       Returns:
           Embedding vector

       Raises:
           EmbeddingError: If embedding fails
       """
   ```

3. **Error Handling:** Use custom exceptions from `app.core.exceptions`
   ```python
   from app.core.exceptions import DocumentProcessingError

   if not file_exists(path):
       raise DocumentProcessingError("File not found", {"path": path})
   ```

4. **Logging:** Use structured logging
   ```python
   from app.core.logging import get_logger

   logger = get_logger(__name__)
   logger.info("document_processed", document_id=doc_id, size=file_size)
   ```

5. **Async/Await:** Use async for I/O operations
   ```python
   async def fetch_data() -> dict:
       async with httpx.AsyncClient() as client:
           response = await client.get(url)
           return response.json()
   ```

### Testing

1. **Write tests for new features**
   ```python
   import pytest

   @pytest.mark.asyncio
   async def test_document_upload():
       # Arrange
       file_path = "test.pdf"

       # Act
       result = await upload_document(file_path)

       # Assert
       assert result.status == "completed"
   ```

2. **Test coverage:** Aim for >80% coverage
   ```bash
   make test-cov
   ```

3. **Test categories:**
   - Unit tests: `tests/unit/`
   - Integration tests: `tests/integration/`
   - E2E tests: `tests/e2e/`

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Build/tooling changes

Examples:
```
feat: add hybrid search retrieval
fix: handle timeout errors in LLM calls
docs: update API documentation for query endpoint
refactor: extract embedding logic to service
test: add unit tests for cache service
```

### Architecture Patterns

Follow the established architecture:

```
app/
├── api/              # API layer (endpoints, middleware)
├── core/             # Core utilities (config, logging, security)
├── domain/           # Business logic (entities, services, interfaces)
├── infrastructure/   # External services (database, cache, vector store)
├── rag/              # RAG pipeline components
├── adapters/         # External service adapters
└── schemas/          # Pydantic validation schemas
```

**Key principles:**
1. **Separation of Concerns:** Keep layers independent
2. **Dependency Inversion:** Depend on abstractions, not implementations
3. **Interface-based Design:** Use abstract interfaces for flexibility
4. **Repository Pattern:** Abstract data access
5. **Service Layer:** Business logic in services

### Adding New Components

#### New LLM Provider

1. Create adapter in `app/adapters/llm/`:
   ```python
   class MyLLMAdapter(BaseLLMAdapter):
       async def generate(self, ...):
           ...
   ```

2. Update factory in `llm_factory.py`
3. Add configuration to `config.py`
4. Write tests

#### New Endpoint

1. Create router in `app/api/v1/endpoints/`:
   ```python
   router = APIRouter()

   @router.post("/", response_model=ResponseSchema)
   async def create_resource(data: RequestSchema):
       ...
   ```

2. Include in `app/api/v1/router.py`
3. Add schemas to `app/schemas/`
4. Write tests

#### New Service

1. Create in `app/domain/services/`:
   ```python
   class MyService:
       def __init__(self, repo: Repository):
           self.repo = repo

       async def do_something(self):
           ...
   ```

2. Add dependencies
3. Use in endpoints
4. Write tests

## 🔄 Development Workflow

### Setup

```bash
# Clone and setup
git clone <your-fork>
cd rag-docs

# Install dependencies
make install-dev

# Start services
make dev-up

# Initialize database
make init-db
```

### Development Cycle

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and test
make test
make lint
make format

# Commit
git add .
git commit -m "feat: add my feature"

# Push and create PR
git push origin feature/my-feature
```

### Before Submitting PR

Checklist:
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] No merge conflicts
- [ ] PR description is clear

## 📚 Resources

- **Architecture Overview:** See `IMPLEMENTATION_STATUS.md`
- **API Documentation:** http://localhost:8000/api/v1/docs (when running)
- **Code Examples:** Check existing implementations (e.g., `openai_adapter.py`)

## 🐛 Debugging

### Run in Debug Mode

```bash
# Set DEBUG=True in .env
DEBUG=True
LOG_LEVEL=DEBUG

# View logs
make dev-logs-api
```

### Access Container

```bash
make shell
# or
docker exec -it ragbase-api-dev bash
```

### Database Issues

```bash
# Access PostgreSQL
make db-shell

# Check migrations
docker exec -it ragbase-api-dev poetry run alembic current
```

## 💡 Tips

1. **Follow existing patterns** - Check similar implementations
2. **Keep PRs focused** - One feature/fix per PR
3. **Write clear code** - Prioritize readability
4. **Test thoroughly** - Consider edge cases
5. **Ask questions** - Use GitHub Discussions

## 📧 Contact

- **Issues:** [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-repo/discussions)
- **Email:** dev@example.com

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to RAG Base Service! 🚀**
