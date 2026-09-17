"""
CLI Commands
Individual command implementations
"""

from typing import Optional
import uuid

from .formatter import (
    print_header, print_response, print_verses, print_concepts,
    print_verse, print_concept, print_conversation, print_info,
    print_error, print_success
)


class AskCommand:
    """Ask a single question"""

    @staticmethod
    def ask_question(rag_engine, question: str, top_k: int = 5):
        """Process single question"""
        print_header("Vedic Assistant")
        print(f"🙏 Question: {question}\n")
        print("⏳ Thinking...\n")

        try:
            result = rag_engine.query(
                question,
                top_k_verses=top_k,
                top_k_concepts=3,
            )

            print_response(
                question,
                result["response"],
                result["retrieved_verses"],
                result["retrieved_concepts"],
                result["session_id"],
            )

            print_success(f"Session ID: {result['session_id']}")
            print_info(f"Continue with: vedic-chat chat --session {result['session_id']}")

        except Exception as e:
            print_error(f"Failed to process query: {e}")


class ChatCommand:
    """Interactive chat session"""

    @staticmethod
    def interactive_chat(rag_engine, session_id: Optional[str] = None):
        """Start interactive chat loop"""
        if not session_id:
            session_id = str(uuid.uuid4())

        print_header("Vedic Chat Session")
        print(f"📝 Session ID: {session_id}")
        print("Type 'quit' to exit, 'history' to see conversation\n")

        while True:
            try:
                user_input = input("🙏 You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() == "quit":
                    print_info("Namaste! 🙏")
                    break

                if user_input.lower() == "history":
                    history = rag_engine.get_conversation(session_id)
                    if history:
                        print_conversation(history["messages"])
                    else:
                        print_error("No conversation found")
                    continue

                if user_input.lower() == "clear":
                    print("\n" * 2)
                    continue

                # Process query
                print("⏳ Thinking...\n")
                result = rag_engine.chat_multi_turn(user_input, session_id)

                print(f"\n🤖 Assistant:\n{result['response']}\n")

                # Show retrieved verses briefly
                if result["retrieved_verses"]:
                    print(f"📖 Sources: {', '.join(v['id'] for v in result['retrieved_verses'][:3])}")

            except KeyboardInterrupt:
                print_info("\nSession paused")
                break
            except Exception as e:
                print_error(f"Error: {e}")


class SearchCommand:
    """Search for verses and concepts"""

    @staticmethod
    def search_knowledge(
        rag_engine,
        query: str,
        by_concept: Optional[str] = None,
        by_chapter: Optional[int] = None,
        limit: int = 10,
    ):
        """Search knowledge base"""
        print_header("Vedic Knowledge Search")

        try:
            if by_concept:
                # Search by concept
                print(f"🔍 Concept: {by_concept}\n")
                verses = rag_engine.retriever.retrieve_by_concept(by_concept)
                print_verses(verses[:limit])

            elif by_chapter:
                # Search by chapter
                print(f"📖 Chapter {by_chapter}\n")
                verses = rag_engine.retriever.retrieve_by_chapter(by_chapter)
                print_verses(verses[:limit])

            else:
                # Semantic search
                print(f"🔍 Query: {query}\n")
                result = rag_engine.retriever.retrieve(query, top_k_verses=limit)

                print_verses(result["verses"])
                print_concepts(result["concepts"])

        except Exception as e:
            print_error(f"Search failed: {e}")


class ExploreCommand:
    """Explore a verse in depth"""

    @staticmethod
    def explore_verse(rag_engine, verse_id: str, depth: int = 2):
        """Explore verse and related content"""
        print_header(f"Exploring {verse_id}")

        try:
            # Get verse details
            verse = rag_engine.vector_store.get_verse_by_id(verse_id)

            if not verse:
                print_error(f"Verse not found: {verse_id}")
                return

            # Print verse
            print("📖 Verse:")
            print_verse(verse)

            # Find similar verses
            print("\n\n🔗 Similar Verses:")
            similar = rag_engine.retriever.retrieve_similar_verses(verse_id, top_k=5)
            print_verses(similar)

            # Find related concepts
            if verse.get("themes"):
                print("\n\n💡 Related Concepts:")
                for theme in verse["themes"]:
                    concept = rag_engine.vector_store.get_concept_by_id(theme.lower())
                    if concept:
                        print_concept(concept)

        except Exception as e:
            print_error(f"Exploration failed: {e}")


class HistoryCommand:
    """View conversation history"""

    @staticmethod
    def show_history(
        rag_engine,
        session_id: Optional[str] = None,
        list_all: bool = False,
    ):
        """Show conversation history"""
        print_header("Conversation History")

        try:
            if list_all:
                # List all conversations
                conversations = rag_engine.list_conversations()

                if not conversations:
                    print_info("No conversations yet")
                    return

                print(f"📝 {len(conversations)} conversation(s):\n")

                for conv in conversations:
                    print(f"ID: {conv['id']}")
                    print(f"Created: {conv['created_at']}")
                    print(f"Messages: {conv['messages']}\n")

            else:
                # Show specific conversation
                if not session_id:
                    print_error("Provide --session ID or use --list to see all")
                    return

                history = rag_engine.get_conversation(session_id)

                if not history:
                    print_error(f"Session not found: {session_id}")
                    return

                print_conversation(history["messages"])

        except Exception as e:
            print_error(f"History lookup failed: {e}")


# Export command classes
ask = AskCommand()
chat = ChatCommand()
search = SearchCommand()
explore = ExploreCommand()
history = HistoryCommand()
