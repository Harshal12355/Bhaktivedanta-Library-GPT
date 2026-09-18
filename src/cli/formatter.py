"""
Output Formatter
Rich formatting for CLI output with citations and metadata
"""

from typing import List, Dict, Optional
import textwrap


def print_header(title: str, level: int = 1):
    """Print formatted header"""
    if level == 1:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
    elif level == 2:
        print(f"\n{title}")
        print(f"{'-'*len(title)}\n")


def print_success(message: str):
    """Print success message"""
    print(f"✓ {message}")


def print_error(message: str):
    """Print error message"""
    print(f"✗ {message}")


def print_info(message: str):
    """Print info message"""
    print(f"ℹ {message}")


def print_verse(verse: Dict):
    """Print formatted verse with metadata"""
    ref = verse.get("id", verse.get("reference", "Unknown"))
    translation = verse.get("translation", "")
    score = verse.get("score", 0)
    themes = verse.get("themes", [])

    print(f"\n📖 [{ref}]")
    print(f"   {translation}")

    if score > 0:
        print(f"   Relevance: {'⭐' * int(score * 5)}")

    if themes:
        print(f"   Topics: {', '.join(themes)}")


def print_verses(verses: List[Dict]):
    """Print multiple verses"""
    if not verses:
        print_error("No verses found")
        return

    print(f"\nFound {len(verses)} verses:\n")

    for i, verse in enumerate(verses, 1):
        ref = verse.get("id", verse.get("reference", "Unknown"))
        translation = verse.get("translation", "")[:100]
        score = verse.get("score", 0)

        print(f"{i}. [{ref}] {translation}...")
        if score > 0:
            print(f"   ↳ Match: {score:.2%}")


def print_concept(concept: Dict):
    """Print formatted concept"""
    name = concept.get("name", "Unknown")
    definition = concept.get("definition", "")
    score = concept.get("score", 0)

    print(f"\n💡 {name}")
    print(f"   {definition}")

    if score > 0:
        print(f"   Relevance: {'⭐' * int(score * 5)}")


def print_concepts(concepts: List[Dict]):
    """Print multiple concepts"""
    if not concepts:
        return

    print(f"\nRelated Concepts:\n")

    for i, concept in enumerate(concepts, 1):
        name = concept.get("name", "Unknown")
        definition = concept.get("definition", "")[:80]
        score = concept.get("score", 0)

        print(f"{i}. {name}")
        print(f"   {definition}")
        if score > 0:
            print(f"   ↳ Match: {score:.2%}")


def print_response(
    query: str,
    response: str,
    verses: List[Dict] = None,
    concepts: List[Dict] = None,
    session_id: str = None,
):
    """Print full response with context"""

    print_header("Vedic Assistant Response")

    print(f"🙏 Question: {query}\n")

    # Print response
    print("📜 Answer:")
    print("-" * 60)
    wrapped = textwrap.fill(response, width=60)
    print(wrapped)
    print("-" * 60)

    # Print retrieved verses
    if verses:
        print(f"\n📖 Retrieved Verses ({len(verses)}):")
        for verse in verses:
            ref = verse.get("id", "Unknown")
            translation = verse.get("translation", "")[:80]
            print(f"\n  [{ref}]")
            print(f"  {translation}...")
            if verse.get("themes"):
                print(f"  Topics: {', '.join(verse['themes'])}")

    # Print concepts
    if concepts:
        print(f"\n💡 Related Concepts ({len(concepts)}):")
        for concept in concepts:
            name = concept.get("name", "Unknown")
            definition = concept.get("definition", "")[:60]
            print(f"\n  {name}")
            print(f"  {definition}...")

    # Print session info
    if session_id:
        print(f"\n📝 Session: {session_id}")


def print_conversation(messages: List[Dict]):
    """Print conversation history"""
    print_header("Conversation History")

    for i, msg in enumerate(messages, 1):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")

        if role == "user":
            print(f"\n{i}. 👤 You ({timestamp[:10]}):")
            print(f"   {content}")
        else:
            print(f"\n{i}. 🤖 Assistant ({timestamp[:10]}):")
            # Truncate long responses
            if len(content) > 200:
                print(f"   {content[:200]}...")
            else:
                print(f"   {content}")


def format_table(rows: List[List[str]], headers: List[str] = None):
    """Format data as simple table"""
    if headers:
        print("  ".join(f"{h:<20}" for h in headers))
        print("-" * (22 * len(headers)))

    for row in rows:
        print("  ".join(f"{cell:<20}" for cell in row))
