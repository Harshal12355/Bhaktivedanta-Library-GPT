"""
RAG Engine
Main orchestrator for retrieval-augmented generation
"""

import json
import logging
import uuid
from typing import List, Dict, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEngine:
    """Main RAG engine combining retriever, vector store, and LLM"""

    def __init__(self, vector_store, retriever, llm_interface):
        self.vector_store = vector_store
        self.retriever = retriever
        self.llm = llm_interface
        self.conversations = {}  # In-memory conversation storage

    def query(
        self,
        question: str,
        session_id: Optional[str] = None,
        top_k_verses: int = 5,
        top_k_concepts: int = 3,
    ) -> Dict:
        """Process a query with RAG"""

        logger.info(f"Processing query: {question[:50]}...")

        # Create or get session
        if not session_id:
            session_id = str(uuid.uuid4())

        if session_id not in self.conversations:
            self.conversations[session_id] = {
                "id": session_id,
                "created_at": datetime.utcnow(),
                "messages": [],
            }

        conversation = self.conversations[session_id]

        # Step 1: Retrieve context
        retrieval_result = self.retriever.retrieve(
            question,
            top_k_verses=top_k_verses,
            top_k_concepts=top_k_concepts,
        )

        verses = retrieval_result["verses"]
        concepts = retrieval_result["concepts"]

        # Step 2: Build prompt with context
        system_prompt, user_prompt = self._build_prompt(question, verses, concepts)

        # Step 3: Generate response
        response = self.llm.generate(system_prompt, user_prompt)

        # Step 4: Store in conversation
        conversation["messages"].append({
            "role": "user",
            "content": question,
            "retrieved_verses": [v["id"] for v in verses],
            "retrieved_concepts": [c["id"] for c in concepts],
            "timestamp": datetime.utcnow().isoformat(),
        })

        conversation["messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat(),
        })

        return {
            "session_id": session_id,
            "question": question,
            "response": response,
            "retrieved_verses": verses,
            "retrieved_concepts": concepts,
            "conversation_length": len(conversation["messages"]),
        }

    def _build_prompt(
        self,
        question: str,
        verses: List[Dict],
        concepts: List[Dict],
    ) -> tuple:
        """Build system and user prompts with context"""

        system_prompt = """You are an expert guide to the Bhagavad Gita and Vedic philosophy.

INSTRUCTIONS:
1. Answer based on the provided Vedic knowledge context
2. Cite specific verses using [BG X.Y] format
3. Explain teachings in clear, accessible language
4. If a topic isn't in the context, acknowledge it
5. Connect teachings to practical spiritual understanding

RESPONSE FORMAT:
- Start with a direct answer to the question
- Support with verse citations
- Explain the deeper philosophical meaning
- Provide related concepts when relevant"""

        # Build context section
        context = "VEDIC KNOWLEDGE CONTEXT:\n\n"

        if verses:
            context += "RELEVANT VERSES:\n"
            for i, verse in enumerate(verses, 1):
                context += f"\n{i}. [{verse.get('id', 'BG')}] {verse.get('translation', '')}\n"
            context += "\n"

        if concepts:
            context += "RELATED CONCEPTS:\n"
            for i, concept in enumerate(concepts, 1):
                context += f"\n{i}. {concept.get('name', '')}: {concept.get('definition', '')}\n"
            context += "\n"

        user_prompt = f"{context}\nQUESTION: {question}"

        return system_prompt, user_prompt

    def chat_multi_turn(
        self,
        question: str,
        session_id: str,
    ) -> Dict:
        """Process a multi-turn conversation"""

        conversation = self.conversations.get(session_id)
        if not conversation:
            logger.warning(f"Session not found: {session_id}")
            return self.query(question, session_id=session_id)

        # Retrieve context for current query
        retrieval_result = self.retriever.retrieve(question)
        verses = retrieval_result["verses"]
        concepts = retrieval_result["concepts"]

        # Build messages with conversation history
        messages = self._build_conversation_messages(conversation, question)

        # Generate response
        response = self.llm.chat(question, conversation_history=messages[:-1])

        # Store in conversation
        conversation["messages"].append({
            "role": "user",
            "content": question,
            "retrieved_verses": [v["id"] for v in verses],
            "timestamp": datetime.utcnow().isoformat(),
        })

        conversation["messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat(),
        })

        return {
            "session_id": session_id,
            "question": question,
            "response": response,
            "retrieved_verses": verses,
            "conversation_turn": len([m for m in conversation["messages"] if m["role"] == "user"]),
        }

    def _build_conversation_messages(
        self,
        conversation: Dict,
        new_question: str,
    ) -> List[Dict]:
        """Build message list from conversation history"""

        messages = []

        # Include recent messages (limit to last 5 turns = 10 messages)
        recent_messages = conversation["messages"][-10:]

        for msg in recent_messages:
            messages.append({
                "role": msg["role"],
                "content": msg["content"],
            })

        return messages

    def get_conversation(self, session_id: str) -> Optional[Dict]:
        """Get conversation history"""
        return self.conversations.get(session_id)

    def list_conversations(self) -> List[Dict]:
        """List all conversations"""
        return [
            {
                "id": conv["id"],
                "created_at": conv["created_at"].isoformat(),
                "messages": len(conv["messages"]),
            }
            for conv in self.conversations.values()
        ]

    def stats(self) -> Dict:
        """Get RAG engine statistics"""
        vector_stats = self.vector_store.stats()

        return {
            "vector_store": vector_stats,
            "conversations": len(self.conversations),
            "total_messages": sum(len(c["messages"]) for c in self.conversations.values()),
            "llm_model": self.llm.model,
            "using_deepseek": self.llm.use_deepseek,
        }


if __name__ == "__main__":
    # Test would require full setup with all components
    print("RAG Engine module loaded")
