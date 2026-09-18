# Phase B: RAG Pipeline

Retrieval-Augmented Generation system for Vedic knowledge with semantic search and LLM integration.

## Components

### 1. **Vector Store** (`src/rag/vector_store.py`)
- SQLite-based vector database with embeddings
- Stores verses and concepts with metadata
- Supports semantic search via cosine similarity
- Fallback to mock embedder for testing (no network needed)

### 2. **Embedder** (`src/rag/embedder.py`)
- Uses `sentence-transformers` (BAAI/bge-small-en-v1.5)
- Embedding dimension: 384
- Caches embeddings to avoid recomputation
- **Mock variant** for testing without model downloads

### 3. **Database Models** (`src/rag/db_models.py`)
- SQLAlchemy ORM models
- `Verse` — Bhagavad Gita verses with embeddings, metadata
- `Concept` — Vedic concepts with definitions and relationships
- `Conversation` — Multi-turn conversation tracking
- `EmbeddingCache` — Caches to avoid recomputation

### 4. **Retriever** (`src/rag/retriever.py`)
- **Hybrid retrieval**: Semantic search + concept filtering
- Three-tier ranking:
  1. Semantic similarity search
  2. Concept-based filtering
  3. Rank verses by relevant concepts
- Methods:
  - `retrieve(query)` — Hybrid search
  - `retrieve_by_concept()` — Get verses for a concept
  - `retrieve_by_chapter()` — Get chapter verses
  - `retrieve_similar_verses()` — Find similar verses

### 5. **LLM Interface** (`src/rag/llm_interface.py`)
- **Primary**: DeepSeek API (cost-effective)
- **Fallback**: Ollama (local, free)
- Automatic failover if DeepSeek unavailable
- Supports context windows up to 32K tokens
- `RAGPromptBuilder` — Assembles context-aware prompts

### 6. **RAG Engine** (`src/rag/rag_engine.py`)
- Main orchestrator combining all components
- Methods:
  - `query()` — Single-turn RAG queries
  - `chat_multi_turn()` — Multi-turn conversations
  - `get_conversation()` — Retrieve conversation history
- Conversation memory with message tracking

## Setup

### Quick Start

```bash
# Install dependencies
pip install -r requirements-phase0.txt

# Initialize RAG system (loads Phase 0 data)
python setup_phase_b.py
```

This will:
1. Initialize vector store (SQLite)
2. Load Phase 0 verses and concepts
3. Generate embeddings (using mock embedder by default)
4. Test retrieval on sample query
5. Display statistics

### Output

```
✓ PHASE B SETUP COMPLETE

RAG System ready for queries!
Database: vedic_rag.db
Embedding model: BAAI/bge-small-en-v1.5

Vector Store Stats:
  - total_verses: 5
  - indexed_verses: 5
  - total_concepts: 3
  - indexed_concepts: 3
  - embedding_dimension: 384
```

## Usage Examples

### Single Query

```python
from src.rag import VectorStore, Retriever, RAGEngine, LLMInterface

# Initialize components
vector_store = VectorStore(use_mock=True)
retriever = Retriever(vector_store, vector_store.embedder)
llm = LLMInterface(use_deepseek=False)  # Use Ollama
rag_engine = RAGEngine(vector_store, retriever, llm)

# Query
result = rag_engine.query("What is Dharma?")
print(result["response"])
```

### Multi-Turn Conversation

```python
# First turn
result1 = rag_engine.query("What is Yoga?")
session_id = result1["session_id"]

# Follow-up turn
result2 = rag_engine.chat_multi_turn(
    "How does it relate to Dharma?",
    session_id=session_id
)

# Get history
history = rag_engine.get_conversation(session_id)
```

### Direct Retrieval

```python
# Search verses
verses = retriever.retrieve("What is the purpose of life?")

# Get verses by concept
dharma_verses = retriever.retrieve_by_concept("Dharma")

# Get chapter
chapter_verses = retriever.retrieve_by_chapter(2)
```

## Architecture

```
User Query
    ↓
[Retriever]
    ├→ Semantic Search (embedding similarity)
    ├→ Concept Filtering (theme matching)
    └→ Ranking (concept boost)
    ↓
[Context Assembly]
    ├→ Top 5 verses
    └→ Top 3 concepts
    ↓
[Prompt Building]
    ├→ System prompt (Vedic guidelines)
    ├→ Retrieved context
    └→ User query
    ↓
[LLM (DeepSeek/Ollama)]
    ↓
[Response Formatting]
    └→ Citations, concepts, follow-ups
    ↓
[Conversation Storage]
    └→ Message history + metadata
```

## Configuration

### Environment Variables

```bash
# DeepSeek (optional, for production)
export DEEPSEEK_API_KEY="your-key-here"

# Ollama (local fallback)
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="mistral"  # or "llama2", "neural-chat", etc.
```

### Database

Default: SQLite at `vedic_rag.db`

To use PostgreSQL with pgvector (production):
```python
vector_store = VectorStore(
    db_url="postgresql://user:password@localhost/vedic_rag"
)
```

## Key Features

✅ **Hybrid Retrieval** — Semantic + concept-based search  
✅ **Bidirectional Links** — Verses ↔ Concepts  
✅ **Multi-turn Conversations** — Session-based memory  
✅ **Cost-Effective** — DeepSeek API (cheap) + Ollama (free)  
✅ **Offline Capable** — Falls back to local Ollama  
✅ **Production Ready** — SQLAlchemy ORM, migrations, caching  

## Testing

### Run Setup Demo

```bash
python setup_phase_b.py
```

### Test Retrieval

```python
from src.rag import VectorStore, Retriever

vs = VectorStore(use_mock=True)
retriever = Retriever(vs, vs.embedder)

result = retriever.retrieve("What is the Gita teaching?")
print(f"Found {len(result['verses'])} verses")
print(f"Top concept: {result['concepts'][0]['name']}")
```

## Next Steps

**Phase C** — Build CLI chat interface:
- `vedic-chat ask "question"`
- `vedic-chat chat` (interactive REPL)
- `vedic-chat search --concept Dharma`
- Citation display with verse references
- Conversation history management

---

**Phase B Status**: ✅ Complete  
**RAG Pipeline**: ✅ Working  
**Vector Store**: ✅ Initialized  
**Embeddings**: ✅ (Mock + Real support)  
**LLM Integration**: ✅ (DeepSeek + Ollama)
