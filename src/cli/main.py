"""
Vedic Chat CLI
Main entry point for the Vedic knowledge chatbot
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import typer
from typing import Optional
import uuid

from rag import VectorStore, Retriever, RAGEngine, LLMInterface
from .commands import AskCommand, ChatCommand, SearchCommand, ExploreCommand, HistoryCommand
from .formatter import print_header, print_success

app = typer.Typer(
    help="Vedic Knowledge Assistant - Chat with the Bhagavad Gita",
    no_args_is_help=True,
)


# Global RAG engine instance
_rag_engine = None


def get_rag_engine() -> RAGEngine:
    """Lazy load RAG engine"""
    global _rag_engine
    if _rag_engine is None:
        # Initialize vector store
        vector_store = VectorStore(
            db_url="sqlite:///vedic_rag.db",
            use_mock=True  # Use mock for demo
        )

        # Initialize retriever
        retriever = Retriever(vector_store, vector_store.embedder)

        # Initialize LLM (DeepSeek with Ollama fallback)
        llm = LLMInterface(use_deepseek=False)  # Use Ollama by default

        # Create RAG engine
        _rag_engine = RAGEngine(vector_store, retriever, llm)

    return _rag_engine


@app.command()
def ask(
    question: str = typer.Argument(..., help="Your question about Vedic philosophy"),
    top_k: int = typer.Option(5, "--top-k", help="Number of verses to retrieve"),
):
    """Ask a single question to the Vedic assistant"""
    rag_engine = get_rag_engine()
    AskCommand.ask_question(rag_engine, question, top_k)


@app.command()
def chat(
    session_id: Optional[str] = typer.Option(None, "--session", help="Resume existing conversation"),
):
    """Start an interactive chat session"""
    rag_engine = get_rag_engine()
    ChatCommand.interactive_chat(rag_engine, session_id)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    by_concept: Optional[str] = typer.Option(None, "--concept", help="Search by concept name"),
    by_chapter: Optional[int] = typer.Option(None, "--chapter", help="Get verses from chapter"),
    limit: int = typer.Option(10, "--limit", help="Number of results"),
):
    """Search for verses and concepts"""
    rag_engine = get_rag_engine()
    SearchCommand.search_knowledge(rag_engine, query, by_concept, by_chapter, limit)


@app.command()
def explore(
    verse_id: str = typer.Argument(..., help="Verse ID (e.g., BG-1.1)"),
    depth: int = typer.Option(2, "--depth", help="How deep to explore related verses"),
):
    """Explore a verse and related content"""
    rag_engine = get_rag_engine()
    ExploreCommand.explore_verse(rag_engine, verse_id, depth)


@app.command()
def history(
    session_id: Optional[str] = typer.Option(None, "--session", help="Specific session ID"),
    list_all: bool = typer.Option(False, "--list", help="List all conversations"),
):
    """View conversation history"""
    rag_engine = get_rag_engine()
    HistoryCommand.show_history(rag_engine, session_id, list_all)


@app.command()
def stats():
    """Show RAG system statistics"""
    rag_engine = get_rag_engine()

    print_header("RAG System Statistics")

    stats = rag_engine.stats()

    print("\n📊 Vector Store:")
    for key, value in stats["vector_store"].items():
        print(f"  {key}: {value}")

    print(f"\n💬 Conversations: {stats['conversations']}")
    print(f"📝 Total Messages: {stats['total_messages']}")
    print(f"🤖 LLM Model: {stats['llm_model']}")
    print(f"🔑 Using DeepSeek: {stats['using_deepseek']}")


@app.command()
def init():
    """Initialize RAG system with Phase 0 data"""
    print_header("Initializing RAG System")

    from .setup import setup_rag
    setup_rag()


def main():
    """Main entry point"""
    app()


if __name__ == "__main__":
    main()
