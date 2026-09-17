# Phase C: CLI Chat Interface

Command-line interface for the Vedic knowledge assistant. Interactive chatbot powered by the RAG pipeline from Phase B.

## Quick Start

```bash
# Make executable (optional)
chmod +x vedic_chat.py

# Ask a single question
python vedic_chat.py ask "What is Dharma?"

# Start interactive chat
python vedic_chat.py chat

# Search for verses
python vedic_chat.py search "Yoga"

# Explore a verse
python vedic_chat.py explore BG-2.47

# View history
python vedic_chat.py history --list

# Show stats
python vedic_chat.py stats
```

## Commands

### `ask` - Single Question

Ask a one-off question and get an answer with citations.

```bash
python vedic_chat.py ask "What does Krishna teach about duty?"
```

**Output:**
```
════════════════════════════════════════════════════════════
  Vedic Assistant Response
════════════════════════════════════════════════════════════

🙏 Question: What does Krishna teach about duty?

📜 Answer:
────────────────────────────────────────────────────────────
Krishna emphasizes the importance of fulfilling one's 
prescribed duty (dharma) as the path to spiritual liberation...
────────────────────────────────────────────────────────────

📖 Retrieved Verses (3):
  [BG 3.35]
  It is far better to discharge one's prescribed duty...

💡 Related Concepts (2):
  Dharma
  Duty in action

📝 Session: 550e8400-e29b-41d4-a716-446655440000
```

### `chat` - Interactive Mode

Start an interactive conversation with session memory.

```bash
python vedic_chat.py chat
```

**Features:**
- Multi-turn conversations
- Automatic session ID creation
- Commands while chatting:
  - `quit` — Exit session
  - `history` — Show conversation
  - `clear` — Clear screen

**Example:**
```
📝 Session ID: a1b2c3d4-e5f6-47g8-h9i0-j1k2l3m4n5o6
Type 'quit' to exit, 'history' to see conversation

🙏 You: What is Bhakti?
⏳ Thinking...

🤖 Assistant:
Bhakti is the path of devotion...

📖 Sources: BG-12.6, BG-2.39

🙏 You: How does it relate to Yoga?
⏳ Thinking...

🤖 Assistant:
Bhakti Yoga is considered the highest form of Yoga...

📖 Sources: BG-6.47, BG-18.55

🙏 You: history
```

### `search` - Knowledge Search

Search for verses and concepts in multiple ways.

```bash
# Semantic search
python vedic_chat.py search "Purpose of life"

# By concept
python vedic_chat.py search --concept Dharma

# By chapter
python vedic_chat.py search --chapter 2

# With limit
python vedic_chat.py search "Yoga" --limit 20
```

**Output:**
```
════════════════════════════════════════════════════════════
  Vedic Knowledge Search
════════════════════════════════════════════════════════════

🔍 Query: Purpose of life

Found 10 verses:

1. [BG-2.47] You have a right to perform your prescribed duty...
   ↳ Match: 85%

2. [BG-3.35] It is far better to discharge one's prescribed duty...
   ↳ Match: 82%
```

### `explore` - Verse Exploration

Deep dive into a verse and discover related content.

```bash
python vedic_chat.py explore BG-18.66 --depth 2
```

**Output:**
```
════════════════════════════════════════════════════════════
  Exploring BG-18.66
════════════════════════════════════════════════════════════

📖 Verse:

[BG-18.66]
   Abandon all varieties of religion and just surrender unto Me...
   ⭐⭐⭐⭐⭐

🔗 Similar Verses:

1. [BG-9.34] Always think of Me...
   ↳ Match: 88%

2. [BG-7.17] Among all types of worship...
   ↳ Match: 85%

💡 Related Concepts:

Surrender
   The act of completely submitting to the divine...

Bhakti
   Devotion; loving service to the Supreme Lord...
```

### `history` - Conversation History

View and manage conversation history.

```bash
# List all conversations
python vedic_chat.py history --list

# Show specific session
python vedic_chat.py history --session a1b2c3d4-e5f6-47g8

# Resume session
python vedic_chat.py chat --session a1b2c3d4-e5f6-47g8
```

### `stats` - System Statistics

Display RAG system and database statistics.

```bash
python vedic_chat.py stats
```

**Output:**
```
════════════════════════════════════════════════════════════
  RAG System Statistics
════════════════════════════════════════════════════════════

📊 Vector Store:
  total_verses: 5
  indexed_verses: 5
  total_concepts: 3
  indexed_concepts: 3
  embedding_model: BAAI/bge-small-en-v1.5
  embedding_dimension: 384

💬 Conversations: 3
📝 Total Messages: 15
🤖 LLM Model: mistral
🔑 Using DeepSeek: False
```

## Architecture

```
User Input
    ↓
┌─────────────────────────────────────────┐
│  CLI (Typer Framework)                  │
│  - ask, chat, search, explore, history  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  Formatter Module                       │
│  - Rich output formatting               │
│  - Citation display                     │
│  - Metadata rendering                   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  Command Modules                        │
│  - ask: Single query processing         │
│  - chat: Interactive loop               │
│  - search: Multi-mode search            │
│  - explore: Verse deep-dive             │
│  - history: Conversation tracking       │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  RAG Engine (Phase B)                   │
│  - Retrieval                            │
│  - LLM Generation                       │
│  - Session Management                   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  Data Layer                             │
│  - Vector Store (SQLite)                │
│  - Embeddings                           │
│  - Conversations                        │
└─────────────────────────────────────────┘
```

## File Structure

```
src/cli/
├── __init__.py          # Package marker
├── main.py              # CLI entry point (Typer app)
├── formatter.py         # Output formatting utilities
├── commands.py          # Command implementations
├── setup.py             # RAG initialization
└── requirements.txt     # CLI dependencies

vedic_chat.py            # Main executable
```

## Installation

```bash
# Install dependencies
pip install typer click

# Make script executable (optional)
chmod +x vedic_chat.py

# Add to PATH (optional)
sudo ln -s $(pwd)/vedic_chat.py /usr/local/bin/vedic-chat
```

## Usage Examples

### Example 1: Ask about Yoga

```bash
$ python vedic_chat.py ask "What is Yoga according to Krishna?"

════════════════════════════════════════════════════════════
  Vedic Assistant Response
════════════════════════════════════════════════════════════

🙏 Question: What is Yoga according to Krishna?

📜 Answer:
────────────────────────────────────────────────────────────
Yoga is the union of the individual soul with the Supreme.
Krishna teaches various paths of Yoga in the Gita...
────────────────────────────────────────────────────────────

📖 Retrieved Verses (3):
  [BG-2.48] Perform your duty...
  [BG-6.47] He who meditates...
  [BG-12.6] Those who control...

📝 Session: 8f7a9b1c-2d3e-4f5g-6h7i-8j9k0l1m2n3o
```

### Example 2: Multi-turn Chat

```bash
$ python vedic_chat.py chat

📝 Session ID: 5c7d9e1f-3g4h-5i6j-7k8l-9m0n1o2p3q4r
Type 'quit' to exit, 'history' to see conversation

🙏 You: What is the essence of the Bhagavad Gita?
⏳ Thinking...

🤖 Assistant:
The Bhagavad Gita is a 700-verse scripture teaching...

🙏 You: How should I apply these teachings in daily life?
⏳ Thinking...

🤖 Assistant:
Krishna offers practical guidance through the different paths...

🙏 You: quit
ℹ Namaste! 🙏
```

### Example 3: Search and Explore

```bash
$ python vedic_chat.py search "Reincarnation" --limit 5

Found 5 verses:
1. [BG-2.20] The soul is never born...
2. [BG-2.22] As a person sheds worn-out garments...
...

$ python vedic_chat.py explore BG-2.20

[BG-2.20]
   The soul is never born, nor does it ever die...
   
Similar Verses:
1. [BG-2.22] As a person sheds worn-out garments...
```

## Configuration

### Environment Variables

```bash
# Use DeepSeek API (optional)
export DEEPSEEK_API_KEY="your-key"

# Ollama configuration
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="mistral"
```

### Database

Default: SQLite at `vedic_rag.db`

Custom location:
```python
# In main.py, modify:
vector_store = VectorStore(db_url="sqlite:///path/to/custom.db")
```

## Features

✅ **Multiple Commands** — ask, chat, search, explore, history  
✅ **Interactive REPL** — Multi-turn conversations with memory  
✅ **Rich Output** — Formatted verses, concepts, citations  
✅ **Session Management** — Persistent conversation history  
✅ **Search Modes** — Semantic, by concept, by chapter  
✅ **Verse Exploration** — Related verses and concepts  
✅ **Statistics** — System and vector store info  

## Development

### Adding New Commands

1. Create method in `commands.py`:
```python
class NewCommand:
    @staticmethod
    def new_command(rag_engine, arg1: str):
        # Implementation
        pass
```

2. Add to `main.py`:
```python
@app.command()
def new_command(arg1: str = typer.Argument(...)):
    rag_engine = get_rag_engine()
    NewCommand.new_command(rag_engine, arg1)
```

### Extending Formatter

Add output functions to `formatter.py`:
```python
def print_custom(data: Dict):
    """Custom output format"""
    # Implementation
```

## Next Steps

**Future Enhancements:**
- Web interface (FastAPI + React)
- Slack bot integration
- Voice input/output
- PDF export of conversations
- Fine-tuned embedding model
- Real-time wiki linking
- Concept graph visualization

---

**Phase C Status**: ✅ Complete  
**CLI Interface**: ✅ Working  
**Commands**: ✅ All 6 implemented  
**Output Formatting**: ✅ Rich citations  
**Session Management**: ✅ Multi-turn support
