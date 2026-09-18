"""
LLM Interface
Handles DeepSeek API (primary) and Ollama (fallback)
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from anthropic import Anthropic as AnthropicClient
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class LLMInterface:
    """Unified LLM interface for DeepSeek and Ollama"""

    def __init__(self, use_deepseek: bool = True):
        self.use_deepseek = use_deepseek and self._check_deepseek_key()
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = None

        if self.use_deepseek:
            logger.info("Using DeepSeek API (primary)")
            self.model = "deepseek-chat"
        else:
            logger.info("Using Ollama (fallback)")
            self.model = os.getenv("OLLAMA_MODEL", "mistral")

        self.max_tokens = 2048
        self.context_window = 32000  # DeepSeek limit

    def _check_deepseek_key(self) -> bool:
        """Check if DeepSeek API key is available"""
        key = os.getenv("DEEPSEEK_API_KEY")
        if key:
            logger.info("✓ DeepSeek API key found")
            return True
        logger.warning("DeepSeek API key not found. Set DEEPSEEK_API_KEY env var.")
        return False

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 chars)"""
        return len(text) // 4

    def call_deepseek(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """Call DeepSeek API"""
        import httpx

        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.deepseek_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": self.max_tokens,
        }

        try:
            with httpx.Client(timeout=60) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()

                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"Unexpected response: {result}")
                    return ""

        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            raise

    def call_ollama(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """Call Ollama locally"""
        import json
        import requests

        url = f"{self.ollama_base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()

            if "message" in result:
                return result["message"]["content"]
            else:
                logger.error(f"Unexpected response: {result}")
                return ""

        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Ollama at {self.ollama_base_url}")
            logger.error("Make sure Ollama is running: ollama serve")
            raise
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise

    def generate(
        self,
        system_prompt: str,
        user_query: str,
        context: str = "",
        temperature: float = 0.7,
    ) -> str:
        """Generate response with optional context"""

        # Build message history
        messages = []

        # System message
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt,
            })

        # Add context if provided
        if context:
            context_msg = f"Reference context:\n\n{context}\n\n---"
            messages.append({
                "role": "user",
                "content": context_msg,
            })

        # User query
        messages.append({
            "role": "user",
            "content": user_query,
        })

        # Call appropriate model
        if self.use_deepseek:
            try:
                return self.call_deepseek(messages, temperature=temperature)
            except Exception as e:
                logger.warning(f"DeepSeek failed, trying Ollama: {e}")
                self.use_deepseek = False
                try:
                    return self.call_ollama(messages, temperature=temperature)
                except Exception as e2:
                    logger.warning(f"Ollama failed, using demo response: {e2}")
                    return self._get_demo_response(user_query)
        else:
            try:
                return self.call_ollama(messages, temperature=temperature)
            except Exception as e:
                logger.warning(f"Ollama unavailable, using demo response: {e}")
                return self._get_demo_response(user_query)

    def chat(self, message: str, conversation_history: List[Dict] = None) -> str:
        """Chat with context history"""
        if conversation_history is None:
            conversation_history = []

        system_prompt = """You are a Vedic philosophy assistant knowledgeable about the Bhagavad Gita.
Provide accurate, thoughtful responses based on Vedic teachings.
Always cite specific verses when relevant."""

        # Prepare messages
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": message})

        if self.use_deepseek:
            try:
                return self.call_deepseek(messages)
            except Exception as e:
                logger.warning(f"DeepSeek failed, trying Ollama: {e}")
                self.use_deepseek = False
                try:
                    return self.call_ollama(messages)
                except:
                    return self._get_demo_response(message)
        else:
            try:
                return self.call_ollama(messages)
            except:
                return self._get_demo_response(message)

    def _get_demo_response(self, query: str) -> str:
        """Get demo response for testing"""
        from .demo_responses import get_demo_response
        return get_demo_response(query)


class RAGPromptBuilder:
    """Build prompts for RAG-enhanced responses"""

    SYSTEM_PROMPT = """You are a knowledgeable guide to Vedic philosophy and the Bhagavad Gita.

IMPORTANT INSTRUCTIONS:
1. Answer questions based on the provided Vedic knowledge context
2. Always cite specific verses (e.g., BG 2.47) when referencing teachings
3. If asked about a topic not in the provided context, say so clearly
4. Provide balanced, philosophical explanations
5. Maintain respectful, educational tone

CONTEXT RULES:
- Use [BG X.Y] format for verse references
- If multiple verses are relevant, cite the most appropriate one
- Explain what verses mean in modern terms when helpful
- Connect concepts to practical spiritual practice when relevant
"""

    @staticmethod
    def build_rag_prompt(
        query: str,
        verses: List[Dict],
        concepts: List[Dict],
    ) -> Tuple[str, str]:
        """Build system and user prompts for RAG query"""

        # Build context from retrieved verses and concepts
        context = "RETRIEVED KNOWLEDGE:\n\n"

        if verses:
            context += "VERSES:\n"
            for verse in verses[:5]:  # Limit to top 5
                context += f"\n[{verse.get('id', 'BG')}] {verse.get('translation', '')}\n"
            context += "\n"

        if concepts:
            context += "CONCEPTS:\n"
            for concept in concepts[:3]:  # Limit to top 3
                context += f"\n{concept.get('name', '')}: {concept.get('definition', '')}\n"
            context += "\n"

        user_prompt = f"{context}\nQUESTION: {query}"

        return RAGPromptBuilder.SYSTEM_PROMPT, user_prompt


if __name__ == "__main__":
    # Test LLM interface
    print("\n=== Testing LLM Interface ===\n")

    llm = LLMInterface(use_deepseek=False)  # Use Ollama for testing

    system_prompt = "You are a helpful assistant about Vedic philosophy."
    query = "What is the significance of the Bhagavad Gita?"

    print(f"Model: {llm.model}")
    print(f"Using DeepSeek: {llm.use_deepseek}\n")

    try:
        response = llm.generate(system_prompt, query)
        print(f"Response:\n{response}")
    except Exception as e:
        print(f"Error: {e}")
        print("Note: Make sure Ollama is running or DEEPSEEK_API_KEY is set")
