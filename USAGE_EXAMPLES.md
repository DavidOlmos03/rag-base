# RAG Base Service - Usage Examples

Complete examples of using the RAG Base Service API.

---

## 📋 Table of Contents

- [Setup](#setup)
- [Authentication](#authentication)
- [LLM Configuration](#llm-configuration)
- [Document Management](#document-management)
- [RAG Queries](#rag-queries)
- [Python Client Example](#python-client-example)
- [cURL Examples](#curl-examples)

---

## Setup

Start the service:

```bash
make quickstart
```

The API will be available at: `http://localhost:8000`

---

## Authentication

### Register a New User

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "SecurePassword123!"
  }'
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "John Doe",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Login

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePassword123!"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Save the access_token for subsequent requests:**
```bash
export TOKEN="your_access_token_here"
```

### Refresh Token

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '"your_refresh_token_here"'
```

---

## LLM Configuration

### List Available Providers

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/llm/providers" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "openai": {
    "name": "OpenAI",
    "display_name": "OpenAI",
    "models": ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
    "requires_api_key": true,
    "supports_streaming": true
  },
  "ollama": {
    "name": "Ollama (Local)",
    "display_name": "Ollama (Local)",
    "models": ["llama3", "mistral", "mixtral", "phi3", "gemma"],
    "requires_api_key": false,
    "supports_streaming": true
  }
}
```

### Configure OpenAI

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/llm/config" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "api_key": "sk-your-openai-api-key",
    "temperature": 0.7,
    "max_tokens": 2000
  }'
```

### Configure Ollama (Local)

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/llm/config" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "ollama",
    "model": "llama3",
    "temperature": 0.7,
    "max_tokens": 2000
  }'
```

### Test LLM Connection

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/llm/test" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "ollama",
    "model": "llama3"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully connected to ollama",
  "latency_ms": 45.3
}
```

### Get Active Configuration

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/llm/config" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Document Management

### Upload a Document

**PDF:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/document.pdf"
```

**DOCX:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/document.docx"
```

**TXT:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/document.txt"
```

**Response:**
```json
{
  "document_id": "456e7890-e89b-12d3-a456-426614174001",
  "filename": "document.pdf",
  "status": "processing",
  "message": "Document uploaded and processing started"
}
```

### List Documents

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/documents?limit=10&offset=0" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
[
  {
    "id": "456e7890-e89b-12d3-a456-426614174001",
    "filename": "document.pdf",
    "file_type": "pdf",
    "file_size": 1048576,
    "status": "completed",
    "num_chunks": 25,
    "error_message": null,
    "created_at": "2024-01-15T10:35:00Z",
    "updated_at": "2024-01-15T10:35:30Z"
  }
]
```

### Get Document Details

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/documents/456e7890-e89b-12d3-a456-426614174001" \
  -H "Authorization: Bearer $TOKEN"
```

### Delete Document

**Request:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/documents/456e7890-e89b-12d3-a456-426614174001" \
  -H "Authorization: Bearer $TOKEN"
```

---

## RAG Queries

### Execute a Query

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main topics discussed in the document?",
    "top_k": 5,
    "score_threshold": 0.7,
    "temperature": 0.7,
    "max_tokens": 500,
    "use_hybrid_search": false
  }'
```

**Response:**
```json
{
  "query_id": "789e0123-e89b-12d3-a456-426614174002",
  "query": "What are the main topics discussed in the document?",
  "answer": "Based on the document, the main topics discussed are:\n\n1. Introduction to machine learning\n2. Supervised vs unsupervised learning\n3. Neural networks and deep learning\n4. Practical applications in industry\n\nThe document provides comprehensive coverage of fundamental ML concepts...",
  "contexts": [
    {
      "content": "Machine learning is a subset of artificial intelligence...",
      "score": 0.92,
      "document_id": "456e7890-e89b-12d3-a456-426614174001",
      "chunk_id": "456e7890-e89b-12d3-a456-426614174001_5",
      "metadata": {
        "filename": "ml_guide.pdf",
        "chunk_index": 5
      }
    }
  ],
  "model_used": "llama3",
  "tokens_used": 345,
  "processing_time": 2.5,
  "created_at": "2024-01-15T10:40:00Z"
}
```

### Streaming Query

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/query/stream" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain the concept of neural networks",
    "top_k": 5
  }'
```

This will stream the response in real-time.

### Get Query History

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/query/history?limit=20&offset=0" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "total": 150,
  "items": [
    {
      "id": "789e0123-e89b-12d3-a456-426614174002",
      "query": "What are the main topics?",
      "answer": "The main topics are...",
      "model_used": "llama3",
      "tokens_used": 345,
      "processing_time": 2.5,
      "created_at": "2024-01-15T10:40:00Z"
    }
  ],
  "page": 1,
  "page_size": 20
}
```

---

## Python Client Example

```python
import requests
from typing import Optional

class RAGClient:
    """Python client for RAG Base Service"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token: Optional[str] = None

    def register(self, name: str, email: str, password: str):
        """Register a new user"""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/register",
            json={"name": name, "email": email, "password": password}
        )
        response.raise_for_status()
        return response.json()

    def login(self, email: str, password: str):
        """Login and store token"""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        return data

    def _headers(self):
        """Get headers with authorization"""
        if not self.token:
            raise ValueError("Not authenticated. Call login() first.")
        return {"Authorization": f"Bearer {self.token}"}

    def configure_llm(self, provider: str, model: str, **kwargs):
        """Configure LLM provider"""
        data = {"provider": provider, "model": model, **kwargs}
        response = requests.post(
            f"{self.base_url}/api/v1/llm/config",
            headers=self._headers(),
            json=data
        )
        response.raise_for_status()
        return response.json()

    def upload_document(self, file_path: str):
        """Upload a document"""
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(
                f"{self.base_url}/api/v1/documents/upload",
                headers=self._headers(),
                files=files
            )
            response.raise_for_status()
            return response.json()

    def list_documents(self, limit: int = 100, offset: int = 0):
        """List documents"""
        response = requests.get(
            f"{self.base_url}/api/v1/documents",
            headers=self._headers(),
            params={"limit": limit, "offset": offset}
        )
        response.raise_for_status()
        return response.json()

    def query(self, query: str, top_k: int = 5, **kwargs):
        """Execute a RAG query"""
        data = {"query": query, "top_k": top_k, **kwargs}
        response = requests.post(
            f"{self.base_url}/api/v1/query",
            headers=self._headers(),
            json=data
        )
        response.raise_for_status()
        return response.json()

    def query_stream(self, query: str, top_k: int = 5, **kwargs):
        """Execute a streaming RAG query"""
        data = {"query": query, "top_k": top_k, **kwargs}
        response = requests.post(
            f"{self.base_url}/api/v1/query/stream",
            headers=self._headers(),
            json=data,
            stream=True
        )
        response.raise_for_status()

        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                yield chunk


# Usage Example
if __name__ == "__main__":
    # Initialize client
    client = RAGClient()

    # Register and login
    client.register("John Doe", "john@example.com", "password123")
    client.login("john@example.com", "password123")

    # Configure Ollama
    client.configure_llm(provider="ollama", model="llama3", temperature=0.7)

    # Upload document
    result = client.upload_document("/path/to/document.pdf")
    print(f"Document uploaded: {result['document_id']}")

    # Wait for processing (check status)
    import time
    time.sleep(5)

    # Query the document
    response = client.query(
        query="What is this document about?",
        top_k=5,
        temperature=0.7
    )

    print(f"\nQuestion: {response['query']}")
    print(f"\nAnswer: {response['answer']}")
    print(f"\nSources used: {len(response['contexts'])}")
    print(f"Tokens used: {response['tokens_used']}")
    print(f"Processing time: {response['processing_time']}s")

    # Streaming example
    print("\n\nStreaming query:")
    for chunk in client.query_stream("Explain the key concepts"):
        print(chunk, end="", flush=True)
```

---

## cURL Examples

### Complete Workflow

```bash
#!/bin/bash

# Set base URL
BASE_URL="http://localhost:8000/api/v1"

# 1. Register
echo "Registering user..."
curl -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "test123"
  }'

# 2. Login
echo -e "\n\nLogging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "Token: $TOKEN"

# 3. Configure LLM
echo -e "\n\nConfiguring LLM..."
curl -X POST "$BASE_URL/llm/config" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "ollama",
    "model": "llama3",
    "temperature": 0.7
  }'

# 4. Upload document
echo -e "\n\nUploading document..."
curl -X POST "$BASE_URL/documents/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"

# Wait for processing
echo -e "\n\nWaiting for processing..."
sleep 5

# 5. Query
echo -e "\n\nQuerying document..."
curl -X POST "$BASE_URL/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is this document about?",
    "top_k": 5
  }'
```

---

## Health Checks

### Check API Health

```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

**Response:**
```json
{
  "status": "healthy",
  "service": "RAG Base Service",
  "version": "0.1.0"
}
```

### Check System Status

```bash
curl -X GET "http://localhost:8000/api/v1/status"
```

**Response:**
```json
{
  "status": "operational",
  "version": "0.1.0",
  "components": {
    "api": "operational",
    "database": "operational",
    "vector_store": "operational",
    "cache": "operational"
  }
}
```

---

## Tips and Best Practices

### 1. Token Management

```bash
# Store token in environment variable
export RAG_TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass"}' \
  | jq -r '.access_token')

# Use in requests
curl -H "Authorization: Bearer $RAG_TOKEN" ...
```

### 2. Batch Document Upload

```bash
# Upload multiple documents
for file in documents/*.pdf; do
  echo "Uploading $file..."
  curl -X POST "http://localhost:8000/api/v1/documents/upload" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@$file"
  sleep 2
done
```

### 3. Query Multiple Questions

```python
questions = [
    "What is the main topic?",
    "Who are the authors?",
    "What are the key findings?"
]

for question in questions:
    response = client.query(question)
    print(f"Q: {question}")
    print(f"A: {response['answer']}\n")
```

---

## Troubleshooting

### Authentication Issues

```bash
# Check if token is valid
curl -X GET "http://localhost:8000/api/v1/llm/config" \
  -H "Authorization: Bearer $TOKEN" \
  -v
```

### Document Processing Issues

```bash
# Check document status
DOC_ID="your-document-id"
curl -X GET "http://localhost:8000/api/v1/documents/$DOC_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### LLM Connection Issues

```bash
# Test LLM connection before using
curl -X POST "http://localhost:8000/api/v1/llm/test" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "ollama",
    "model": "llama3"
  }'
```

---

**Happy querying! 🚀**
