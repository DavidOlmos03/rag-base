# RAG Base as a Service (RAGaaS)
## Arquitectura Base Multipropósito con FastAPI, Open Source y Multi-LLM

---

## 🧠 Rol del sistema

Actúa como un **arquitecto senior de sistemas de IA**, especializado en:

- Retrieval-Augmented Generation (RAG)
- FastAPI y arquitecturas async
- Docker y despliegue en producción
- Sistemas multi-tenant y multi-modelo
- Enfoque **open-source first**, optimización de costos y escalabilidad futura

---

## 🎯 Objetivo general

Diseñar y construir un **RAG as a Service (RAGaaS)** implementado en **Python (FastAPI)** que funcione como un **núcleo reutilizable**, preparado para ser consumido y adaptado por múltiples proyectos independientes, tales como:

- Sistemas legales (abogados)
- Proyectos académicos / universitarios
- Plataformas de divulgación científica

Este proyecto debe **limitarse exclusivamente al RAG base**, sin incluir lógica específica de dominio.

---

## 🧩 Alcance del proyecto

El sistema debe:

- Implementar **solo el core del RAG**
- Ser **agnóstico al dominio**
- Ser **agnóstico al proveedor de LLM**
- Permitir extensión futura sin refactorización mayor

Cada proyecto consumidor podrá posteriormente:
- Definir prompts específicos
- Ajustar pipelines
- Elegir proveedor y modelo LLM
- Configurar políticas propias

---

## 🏗️ Stack tecnológico

### Backend
- Python 3.11+
- FastAPI (async-first)
- Pydantic v2
- Arquitectura modular

### Enfoque
- Open-source first
- Bajo costo operativo
- Evitar lock-in con proveedores

---

## 🧠 Arquitectura RAG Base

El RAG debe estar desacoplado del modelo y del proveedor.

### Pipeline recomendado

Document Loader
↓
Chunker
↓
Embedding Generator
↓
Vector Store (Qdrant)
↓
Retriever
↓
Context Builder
↓
Prompt Adapter
↓
LLM Client (OpenAI / Claude / DeepSeek / Ollama)


---

## 📂 Componentes del RAG Core

### 1. Ingesta de documentos
- PDF
- TXT
- DOCX
- Preparado para OCR en el futuro

### 2. Chunking
- Configurable:
  - Tamaño
  - Overlap
- Independiente del dominio

### 3. Embeddings
- **Open-source**
- Independientes del proveedor LLM

#### Modelos recomendados
- `bge-m3`
- `e5-large`

---

## 📦 Vector Database

### Requerimientos
- Open-source
- Self-hosted
- Soporte de metadatos
- Namespaces / collections

### Elección recomendada
- **Qdrant**

Uso de metadatos:
- `project_id`
- `document_id`
- `version`
- `source`

---

## 🤖 Soporte Multi-LLM (crítico)

El sistema debe permitir cambiar de proveedor **sin reindexar documentos**.

### Proveedores soportados

#### APIs externas
- OpenAI (ChatGPT)
- Anthropic (Claude)
- DeepSeek
- Otros compatibles

#### Modelos locales
- **Ollama**
- Selección explícita del modelo (ej: `llama3`, `mistral`)

---

## 🔌 Endpoint de configuración de LLM

Debe existir un endpoint para registrar y seleccionar dinámicamente el proveedor LLM.

### Capacidades requeridas
- Registrar API Key
- Registrar Base URL
- Seleccionar proveedor:
  - `openai`
  - `claude`
  - `deepseek`
  - `ollama`
- Seleccionar modelo
- Elegir entre:
  - API externa
  - Modelo local

⚠️ El core del RAG **no debe depender directamente del proveedor**, solo de un adapter.

---

## 🧩 Diseño por interfaces (recomendado)

Ejemplos de interfaces base:

- `LLMClient`
- `EmbeddingProvider`
- `VectorStore`
- `Retriever`

Esto garantiza:
- Bajo acoplamiento
- Fácil extensión
- Mantenibilidad

---

## 🐳 Dockerización (obligatoria)

El proyecto debe estar completamente dockerizado.

### Entornos

#### Desarrollo
- Hot reload
- Logs detallados
- Volúmenes montados

#### Producción
- Multi-stage build
- Imagen optimizada
- Variables de entorno
- Separación clara de servicios

### Archivos requeridos
- `Dockerfile.dev`
- `Dockerfile.prod`
- `docker-compose.dev.yml`
- `docker-compose.prod.yml`

### Servicios esperados
- API (FastAPI)
- Qdrant
- Ollama (opcional)

---

## 💰 Optimización de costos

- Uso prioritario de herramientas open-source
- Embeddings locales
- Ollama para:
  - Desarrollo
  - Pruebas
  - Casos de bajo presupuesto
- Escalado bajo demanda

---

## 📁 Estructura de proyecto sugerida

```text
rag_base/
├── app/
│   ├── main.py
│   ├── api/
│   ├── core/
│   ├── rag/
│   ├── adapters/
│   ├── embeddings/
│   ├── vectorstore/
│   └── models/
├── docker/
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── Dockerfile.dev
├── Dockerfile.prod
└── README.md

