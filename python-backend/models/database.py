from sqlalchemy import create_engine, Column, String, Integer, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
import uuid
from pathlib import Path

# Get the directory where this file lives (python-backend/)
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "novel_writer.db"

# Use absolute path for SQLite database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    genre = Column(String, nullable=False)
    target_word_count = Column(Integer, nullable=False)
    created_at = Column(Integer, nullable=False)
    updated_at = Column(Integer, nullable=False)
    path = Column(String, nullable=False, unique=True)
    premise = Column(Text, nullable=True)
    themes = Column(Text, nullable=True)
    setting = Column(Text, nullable=True)
    key_characters = Column(Text, nullable=True)

    # Literary agent pipeline control
    enable_literary_agents = Column(Boolean, default=True)
    agent_intervention_level = Column(String, default="moderate")  # 'light', 'moderate', 'intensive'
    auto_apply_suggestions = Column(Boolean, default=False)

    messages = relationship("Message", back_populates="project", cascade="all, delete-orphan")
    agent_analyses = relationship("AgentAnalysis", back_populates="project", cascade="all, delete-orphan")
    content_versions = relationship("ContentVersion", back_populates="project", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    agent_type = Column(String, nullable=True)
    timestamp = Column(Integer, nullable=False)

    project = relationship("Project", back_populates="messages")


class AgentAnalysis(Base):
    """Stores individual agent analysis results for content."""
    __tablename__ = "agent_analyses"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    content_id = Column(String, nullable=True)  # Reference to specific content being analyzed
    content_type = Column(String, nullable=False)  # 'outline', 'chapter', 'scene', etc.
    agent_type = Column(String, nullable=False)  # Which agent performed analysis
    analysis_result = Column(Text, nullable=False)  # JSON string with agent's findings
    timestamp = Column(Integer, nullable=False)

    project = relationship("Project", back_populates="agent_analyses")


class ContentVersion(Base):
    """Stores versions of content with their agent analysis references."""
    __tablename__ = "content_versions"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    content_type = Column(String, nullable=False)  # 'outline', 'chapter', 'scene', etc.
    original_content = Column(Text, nullable=False)
    enhanced_content = Column(Text, nullable=True)
    agent_analyses_id = Column(String, nullable=True)  # Link to analysis that produced this
    timestamp = Column(Integer, nullable=False)

    project = relationship("Project", back_populates="content_versions")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
