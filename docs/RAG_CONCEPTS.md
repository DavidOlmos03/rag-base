# Conceptos Clave de RAG (Retrieval-Augmented Generation)

Esta guía explica los conceptos fundamentales que debes entender para trabajar con el sistema RAG Base.

---

## 📄 Chunking (Fragmentación de Documentos)

### ¿Qué es?

El **chunking** es el proceso de dividir documentos largos en fragmentos (chunks) más pequeños y manejables. Esto es esencial porque:

- Los modelos de embeddings tienen límites de longitud de entrada
- Los LLMs tienen límites de contexto
- Fragmentos más pequeños permiten búsquedas más precisas

### ¿Cómo funciona en este proyecto?

Ubicación: `app/rag/ingestion/chunker.py`

**Configuración actual:**
- **Tamaño del chunk**: 500 caracteres (configurable en `.env` como `DEFAULT_CHUNK_SIZE`)
- **Overlap**: 50 caracteres (configurable como `DEFAULT_CHUNK_OVERLAP`)

### Parámetros importantes

```python
DEFAULT_CHUNK_SIZE=500        # Tamaño de cada fragmento
DEFAULT_CHUNK_OVERLAP=50      # Superposición entre fragmentos
```

#### ¿Por qué overlap?

El overlap (superposición) asegura que información importante en los límites entre chunks no se pierda:

```
Chunk 1: [0-500 caracteres]
                    ↓ Overlap (50 chars)
Chunk 2:        [450-950 caracteres]
                    ↓ Overlap (50 chars)
Chunk 3:            [900-1400 caracteres]
```

### Recomendaciones de configuración

| Tipo de Documento | Chunk Size | Overlap | Razón |
|-------------------|------------|---------|-------|
| Documentos técnicos | 400-600 | 50-100 | Balance entre contexto y precisión |
| Artículos/Blogs | 600-800 | 100-150 | Párrafos completos |
| Código fuente | 200-400 | 30-50 | Funciones/bloques completos |
| FAQs | 100-200 | 20-30 | Preguntas/respuestas individuales |

### Metadata de chunks

Cada chunk incluye metadata útil:

```python
{
    "content": "Texto del fragmento...",
    "chunk_index": 0,
    "document_id": "uuid-del-documento",
    "filename": "documento.pdf",
    "file_type": "pdf",
    "metadata": {...}  # Metadata adicional
}
```

---

## 🧠 Embeddings (Representaciones Vectoriales)

### ¿Qué son?

Los **embeddings** son representaciones numéricas (vectores) de texto que capturan su significado semántico. Textos con significados similares tienen vectores similares.

```
"¿Cómo funciona el motor?"     → [0.2, 0.8, 0.1, ..., 0.5]  (768 dimensiones)
"¿Cuál es el funcionamiento?"  → [0.25, 0.75, 0.15, ..., 0.48]  (similar)
"El gato está durmiendo"       → [0.9, 0.1, 0.7, ..., 0.2]  (diferente)
```

### Modelo utilizado: BAAI/bge-m3

**Características:**
- **Dimensiones**: 1024 (más dimensiones = mayor precisión)
- **Multilingüe**: Soporta español, inglés y 100+ idiomas
- **Max length**: 8192 tokens (configurable a 512 en este proyecto)
- **Tipo**: Dense embeddings

**Configuración:**

```bash
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cpu              # o 'cuda' para GPU
EMBEDDING_BATCH_SIZE=32           # Textos procesados por lote
EMBEDDING_MAX_LENGTH=512          # Longitud máxima de entrada
EMBEDDING_CACHE_TTL=2592000       # Cache: 30 días
```

### Proceso de generación

```
1. Texto original → "¿Cuál es la política de reembolso?"
2. Tokenización → [2534, 8901, 3421, ...]
3. Modelo BAAI/bge-m3 → Procesamiento
4. Vector de embeddings → [0.234, -0.567, 0.891, ..., 0.123] (1024 dims)
5. Almacenamiento en Qdrant
```

### Cache de embeddings

**Ubicación**: Redis

El sistema cachea embeddings para:
- **Mejorar rendimiento**: Evita recalcular el mismo texto
- **Reducir costos**: Menos procesamiento
- **TTL**: 30 días por defecto

```python
# La misma pregunta en diferentes queries usa el embedding cacheado
Query 1: "¿Cuál es el precio?" → Calcula embedding → Guarda en cache
Query 2: "¿Cuál es el precio?" → Usa embedding del cache (instantáneo)
```

---

## 🔍 Similarity Search (Búsqueda por Similitud)

### ¿Cómo funciona?

La búsqueda por similitud compara el embedding de tu query con los embeddings de todos los chunks almacenados:

```
Query: "¿Cómo instalar la aplicación?"
  ↓ Generar embedding
[0.3, 0.7, 0.2, ..., 0.5]
  ↓ Comparar con chunks en Qdrant

Chunk 1: "Instalación paso a paso..." → Similitud: 0.92 ✅
Chunk 2: "Proceso de instalación..."  → Similitud: 0.88 ✅
Chunk 3: "Política de privacidad..."  → Similitud: 0.23 ❌
Chunk 4: "Contacto y soporte..."      → Similitud: 0.15 ❌
```

### Métrica de distancia: Cosine Similarity

Este proyecto usa **similitud coseno** (cosine similarity), que mide el ángulo entre vectores:

```
Score = cos(θ) = (A · B) / (||A|| ||B||)

Rango: -1 a 1
- 1.0  = Idénticos
- 0.7  = Muy similares (threshold por defecto)
- 0.5  = Moderadamente similares
- 0.0  = No relacionados
- -1.0 = Opuestos
```

**Ventajas de cosine**:
- Insensible a la magnitud del vector
- Ideal para similitud semántica
- Rango normalizado [0, 1] cuando se usa con vectores positivos

### Score Threshold (Umbral de Similitud)

El **score_threshold** filtra resultados poco relevantes:

```python
# En el endpoint query
{
    "query": "¿Cómo resetear mi contraseña?",
    "score_threshold": 0.7  # Solo chunks con ≥70% similitud
}
```

#### Recomendaciones de threshold

| Threshold | Uso | Resultado |
|-----------|-----|-----------|
| **0.9 - 1.0** | Búsquedas exactas | Muy pocos resultados, alta precisión |
| **0.7 - 0.9** | **Uso general** ✅ | Balance entre precisión y recall |
| **0.5 - 0.7** | Búsquedas amplias | Más resultados, menor precisión |
| **< 0.5** | Exploración | Muchos resultados irrelevantes ⚠️ |

**Ejemplo práctico:**

```python
# Threshold = 0.9 (Estricto)
Query: "política de reembolso"
Resultados: 2 chunks (muy relevantes)

# Threshold = 0.7 (Balanceado) ✅
Query: "política de reembolso"
Resultados: 5 chunks (relevantes)

# Threshold = 0.5 (Permisivo)
Query: "política de reembolso"
Resultados: 15 chunks (incluye información tangencial)
```

### Top K (Número de resultados)

Controla cuántos chunks recuperar:

```python
{
    "top_k": 5,              # Recuperar los 5 chunks más similares
    "score_threshold": 0.7   # Que tengan ≥ 0.7 de similitud
}
```

**Configuración recomendada:**

| Escenario | top_k | score_threshold |
|-----------|-------|-----------------|
| Respuestas precisas | 3-5 | 0.8-0.9 |
| **Uso general** ✅ | 5-7 | 0.7-0.8 |
| Respuestas detalladas | 10-15 | 0.6-0.7 |
| Exploración | 15-20 | 0.5-0.6 |

---

## 🗄️ Vector Store (Qdrant)

### ¿Qué es?

Qdrant es una base de datos especializada en almacenar y buscar vectores de alta dimensionalidad de manera eficiente.

### Estructura de datos

```python
Collection: "tenant_517d45e0-f975-4bb9-84fb-232c33f6e6dd"
├── Vector 1 (UUID: abc123)
│   ├── vector: [0.2, 0.8, ..., 0.5]  # 1024 dimensiones
│   └── payload: {
│       "content": "Texto del chunk...",
│       "document_id": "doc-uuid",
│       "chunk_index": 0,
│       "tenant_id": "tenant-uuid",
│       "metadata": {...}
│   }
├── Vector 2 (UUID: def456)
│   └── ...
```

### Collections por tenant

Cada tenant tiene su propia collection aislada:

```
tenant_517d45e0-f975-4bb9-84fb-232c33f6e6dd  (Usuario 1)
tenant_8a2f3b1c-4d5e-6f7g-8h9i-0j1k2l3m4n5o  (Usuario 2)
```

**Ventajas:**
- **Aislamiento**: Un usuario no puede acceder a datos de otro
- **Escalabilidad**: Collections independientes
- **Rendimiento**: Búsquedas solo en datos del usuario

### Configuración

```bash
QDRANT_URL=http://qdrant:6333
QDRANT_TIMEOUT=30              # Timeout de operaciones
QDRANT_PREFER_GRPC=False       # Usar HTTP en lugar de gRPC
```

---

## 🔄 RAG Pipeline (Flujo Completo)

### Proceso de Indexación (Upload Document)

```
1. Upload
   ↓
   📄 documento.pdf (50 páginas)

2. Parsing (DocumentLoader)
   ↓
   📝 Texto extraído (25,000 caracteres)

3. Chunking (TextChunker)
   ↓
   📋 50 chunks × 500 chars cada uno

4. Embedding (BAAI/bge-m3)
   ↓
   🧠 50 vectores × 1024 dimensiones

5. Storage (Qdrant)
   ↓
   🗄️ Collection: tenant_xxx
       └── 50 vectors con metadata
```

### Proceso de Query

```
1. Usuario hace pregunta
   ↓
   "¿Cómo resetear la contraseña?"

2. Generar embedding de la query
   ↓
   🧠 [0.3, 0.7, 0.2, ..., 0.5]

3. Similarity Search en Qdrant
   ↓
   🔍 Buscar top_k=5 chunks más similares
       con score >= 0.7

4. Recuperar contextos
   ↓
   📋 5 chunks relevantes:
       - Chunk 23: score=0.92
       - Chunk 45: score=0.88
       - Chunk 12: score=0.85
       - Chunk 67: score=0.78
       - Chunk 34: score=0.72

5. Construir prompt para LLM
   ↓
   📝 Contexto + Pregunta

6. LLM genera respuesta
   ↓
   🤖 Ollama (phi3:mini)

7. Respuesta final
   ↓
   ✅ "Para resetear tu contraseña..."
```

---

## ⚙️ Parámetros de Query Explicados

### Tabla completa de parámetros

| Parámetro | Tipo | Rango | Default | Descripción |
|-----------|------|-------|---------|-------------|
| `query` | string | 1-1000 | - | **Requerido**: Tu pregunta |
| `top_k` | int | 1-20 | 5 | Número de chunks a recuperar |
| `score_threshold` | float | 0.0-1.0 | 0.7 | Umbral mínimo de similitud |
| `temperature` | float | 0.0-2.0 | 0.7 | Creatividad del LLM |
| `max_tokens` | int | 1-4000 | None | Límite de tokens en respuesta |
| `use_hybrid_search` | bool | true/false | false | Combinar búsqueda vectorial + keyword |

### Temperature (Creatividad del LLM)

Controla la aleatoriedad en las respuestas del LLM:

```python
temperature = 0.0   # Determinista, siempre la misma respuesta
              ↓
temperature = 0.3   # Muy preciso, poco creativo
              ↓
temperature = 0.7   # ✅ Balanceado (recomendado)
              ↓
temperature = 1.0   # Creativo, variado
              ↓
temperature = 2.0   # Muy aleatorio, puede divagar
```

**Uso recomendado:**

| Caso de uso | Temperature |
|-------------|-------------|
| FAQ / Soporte técnico | 0.3 - 0.5 |
| **Uso general** ✅ | 0.7 - 0.9 |
| Brainstorming / Creatividad | 1.0 - 1.5 |
| Experimentación | 1.5 - 2.0 |

### Max Tokens

Limita la longitud de la respuesta:

```python
max_tokens = 50    # Respuesta muy breve
max_tokens = 200   # Respuesta concisa ✅
max_tokens = 400   # Respuesta detallada
max_tokens = 1000  # Respuesta muy extensa
```

**Nota**: 1 token ≈ 0.75 palabras en inglés, ≈ 0.5 palabras en español

---

## 🔀 Hybrid Search (Búsqueda Híbrida)

### ¿Qué es?

Combina dos tipos de búsqueda:

1. **Búsqueda vectorial (semántica)**: Por significado
2. **Búsqueda por keywords (léxica)**: Por palabras exactas

### ¿Cuándo usarla?

```python
# Búsqueda vectorial (use_hybrid_search=false) ✅
Query: "¿Cómo funciona el motor?"
Encuentra: "proceso de funcionamiento del motor", "operación del sistema"

# Búsqueda híbrida (use_hybrid_search=true)
Query: "error CODE_123"
Encuentra: Documentos con el código exacto "CODE_123" + contexto semántico
```

**Usa hybrid search cuando:**
- Buscas códigos de error específicos
- Necesitas nombres propios exactos
- Quieres combinar precisión léxica con comprensión semántica

---

## 💾 Caching y Optimización

### Cache de Embeddings (Redis)

**Ubicación**: `app/infrastructure/cache/cache_service.py`

```python
# Cache key format
embedding_cache:{hash_del_texto} → vector_embedding

# TTL (Time To Live)
EMBEDDING_CACHE_TTL=2592000  # 30 días
```

**Beneficios:**
- **Performance**: Embeddings instantáneos para textos repetidos
- **Costo**: No re-procesar el mismo texto
- **Escalabilidad**: Menos carga en el modelo

### Cache de Queries

```python
QUERY_CACHE_TTL=3600        # 1 hora
RESPONSE_CACHE_TTL=1800     # 30 minutos
```

**Funcionamiento:**

```
Query 1 (11:00): "¿Cuál es el precio?"
  ↓ Procesa completo
  ↓ Guarda en cache (1 hora)

Query 2 (11:15): "¿Cuál es el precio?"
  ↓ Usa cache (instantáneo) ✅

Query 3 (12:30): "¿Cuál es el precio?"
  ↓ Cache expirado, procesa nuevamente
```

---

## 📊 Métricas y Observabilidad

### Campos registrados en queries

Cada query guarda:

```python
{
    "query_text": "¿Cómo resetear?",
    "answer_text": "Para resetear...",
    "model_used": "phi3:mini",
    "tokens_used": 234,
    "processing_time": 2.5,  # segundos
    "num_contexts": 5,
    "created_at": "2025-12-31T10:30:00"
}
```

### Endpoint de historial

```bash
GET /api/v1/query/history?limit=50&offset=0
```

Útil para:
- Analizar patrones de uso
- Mejorar respuestas frecuentes
- Optimizar configuración (top_k, threshold)

---

## 🎯 Best Practices

### 1. Configuración de Chunking

```python
# ✅ BIEN
DEFAULT_CHUNK_SIZE=500
DEFAULT_CHUNK_OVERLAP=50

# ❌ MAL - Chunks muy grandes
DEFAULT_CHUNK_SIZE=2000  # Pierde precisión en búsqueda

# ❌ MAL - Sin overlap
DEFAULT_CHUNK_OVERLAP=0  # Pierde contexto en límites
```

### 2. Ajuste de Score Threshold

```python
# Si obtienes muy pocos resultados
score_threshold=0.7  → Reducir a 0.6

# Si obtienes resultados irrelevantes
score_threshold=0.7  → Aumentar a 0.8
```

### 3. Balance Top K vs Score Threshold

```python
# ✅ BIEN - Balance
top_k=5, score_threshold=0.7

# ⚠️ CUIDADO - Puede no devolver nada
top_k=20, score_threshold=0.95  # Muy estricto

# ⚠️ CUIDADO - Muchos irrelevantes
top_k=20, score_threshold=0.4   # Muy permisivo
```

### 4. Modelos de Embeddings

```python
# ✅ Producción - Multilingüe
EMBEDDING_MODEL=BAAI/bge-m3

# Alternativas:
# - BAAI/bge-large-en-v1.5 (solo inglés, mayor precisión)
# - sentence-transformers/all-MiniLM-L6-v2 (más rápido, menor precisión)
# - intfloat/multilingual-e5-large (excelente multilingüe)
```

---

## 🔧 Troubleshooting

### Problema: Respuestas no relevantes

**Solución:**
1. Aumentar `score_threshold` (0.7 → 0.8)
2. Revisar calidad de los chunks
3. Verificar que el documento fue indexado correctamente

### Problema: No encuentra información que sí existe

**Solución:**
1. Reducir `score_threshold` (0.7 → 0.6)
2. Aumentar `top_k` (5 → 10)
3. Usar `use_hybrid_search=true`

### Problema: Respuestas muy largas o cortas

**Solución:**
1. Ajustar `max_tokens` (100-500 para respuestas normales)
2. Modificar `temperature` para controlar creatividad

### Problema: Búsquedas lentas

**Solución:**
1. Verificar cache de Redis está funcionando
2. Reducir `top_k` si es muy alto
3. Verificar tamaño de la collection en Qdrant

---

## 📚 Referencias

### Archivos clave del proyecto

- `app/rag/ingestion/chunker.py` - Lógica de chunking
- `app/rag/embeddings/sentence_transformers_provider.py` - Generación de embeddings
- `app/rag/retrieval/vector_retriever.py` - Similarity search
- `app/rag/pipeline.py` - Pipeline completo de RAG
- `app/schemas/query.py` - Schemas de queries

### Variables de entorno importantes

```bash
# Chunking
DEFAULT_CHUNK_SIZE=500
DEFAULT_CHUNK_OVERLAP=50

# Embeddings
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cpu
EMBEDDING_BATCH_SIZE=32
EMBEDDING_MAX_LENGTH=512
EMBEDDING_CACHE_TTL=2592000

# RAG
DEFAULT_TOP_K=5
DEFAULT_RETRIEVAL_SCORE_THRESHOLD=0.7
CONTEXT_MAX_TOKENS=2000

# Cache
QUERY_CACHE_TTL=3600
RESPONSE_CACHE_TTL=1800
```

### Recursos externos

- [BAAI/bge-m3 Model Card](https://huggingface.co/BAAI/bge-m3)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Sentence Transformers](https://www.sbert.net/)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)

---

## 💡 Resumen Rápido

| Concepto | Qué hace | Parámetro clave | Valor recomendado |
|----------|----------|-----------------|-------------------|
| **Chunking** | Divide documentos | `CHUNK_SIZE` | 500 chars |
| **Embeddings** | Convierte texto a vectores | `EMBEDDING_MODEL` | BAAI/bge-m3 |
| **Similarity Search** | Encuentra chunks relevantes | `score_threshold` | 0.7 |
| **Top K** | Límite de resultados | `top_k` | 5 |
| **Temperature** | Creatividad del LLM | `temperature` | 0.7 |
| **Max Tokens** | Longitud de respuesta | `max_tokens` | 200-400 |
