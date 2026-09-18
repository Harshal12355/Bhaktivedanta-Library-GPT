"""
Database Models for RAG System
SQLAlchemy models for verses, concepts, embeddings, and conversations
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Boolean, JSON, Index, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json

Base = declarative_base()


class Verse(Base):
    """Bhagavad Gita verse with embeddings"""
    __tablename__ = "verses"

    id = Column(String(20), primary_key=True)  # e.g., "BG-1.1"
    chapter = Column(Integer, nullable=False)
    verse_number = Column(Integer, nullable=False)

    # Content
    devanagari = Column(Text, nullable=True)
    transliteration = Column(Text, nullable=True)
    translation = Column(Text, nullable=True)
    purport = Column(Text, nullable=True)

    # Embedding
    embedding = Column(Text, nullable=True)  # JSON-serialized vector
    embedding_model = Column(String(100), default="BAAI/bge-small-en-v1.5")

    # Metadata
    themes = Column(JSON, default=[])  # List of concept names
    source_text = Column(String(100), default="Bhagavad-Gita")
    copyright = Column(String(200), default="© ISKCON (Prabhupada)")
    verified = Column(Boolean, default=True)
    confidence = Column(Float, default=0.95)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_chapter_verse", "chapter", "verse_number"),
        Index("idx_themes", "themes"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "chapter": self.chapter,
            "verse_number": self.verse_number,
            "translation": self.translation,
            "themes": self.themes,
            "source_text": self.source_text,
        }


class Concept(Base):
    """Vedic concept with embedding"""
    __tablename__ = "concepts"

    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    definition = Column(Text, nullable=False)
    description = Column(Text, nullable=True)

    # Embedding
    embedding = Column(Text, nullable=True)  # JSON-serialized vector
    embedding_model = Column(String(100), default="BAAI/bge-small-en-v1.5")

    # Relations
    synonyms = Column(JSON, default=[])
    related_concepts = Column(JSON, default=[])
    related_verses = Column(JSON, default=[])  # List of verse IDs

    # Metadata
    source_url = Column(String(500), nullable=True)
    confidence = Column(Float, default=0.9)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_concept_name", "name"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "definition": self.definition,
            "synonyms": self.synonyms,
            "related_concepts": self.related_concepts,
        }


class Conversation(Base):
    """Conversation session"""
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True)  # UUID
    topic = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)

    # Extracted context
    extracted_concepts = Column(JSON, default=[])
    retrieved_verses = Column(JSON, default=[])

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_conversation_active", "is_active"),
    )


class ConversationMessage(Base):
    """Individual message in conversation"""
    __tablename__ = "conversation_messages"

    id = Column(String(36), primary_key=True)  # UUID
    conversation_id = Column(String(36), nullable=False)

    # Message content
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)

    # Retrieved context for this turn
    retrieved_verses = Column(JSON, default=[])  # List of verse IDs
    retrieved_concepts = Column(JSON, default=[])  # List of concept IDs

    # Metadata
    tokens_used = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EmbeddingCache(Base):
    """Cache for embeddings to avoid recomputation"""
    __tablename__ = "embedding_cache"

    text_hash = Column(String(64), primary_key=True)  # SHA256 hash
    text = Column(Text, nullable=False)
    embedding = Column(Text, nullable=False)  # JSON-serialized vector
    embedding_model = Column(String(100), default="BAAI/bge-small-en-v1.5")
    created_at = Column(DateTime, default=datetime.utcnow)


class DatabaseConfig:
    """Database configuration and session management"""

    def __init__(self, db_url: str = "sqlite:///vedic_rag.db"):
        self.db_url = db_url
        self.engine = None
        self.SessionLocal = None

    def init_db(self):
        """Initialize database engine and create tables"""
        self.engine = create_engine(
            self.db_url,
            echo=False,
            pool_pre_ping=True  # Verify connections are alive
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
        return self.engine

    def get_session(self):
        """Get a database session"""
        if not self.SessionLocal:
            self.init_db()
        return self.SessionLocal()

    def drop_all(self):
        """Drop all tables (for testing)"""
        if self.engine:
            Base.metadata.drop_all(self.engine)
