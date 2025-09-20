# database.py - Updated for psycopg2
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, Integer
from datetime import datetime
from typing import List, Optional

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Convert to async psycopg2 format if needed
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# Create engine
engine = None
async_session_maker = None

if DATABASE_URL:
    # Use regular SQLAlchemy (not async) for psycopg2-binary
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Simple cache
class SimpleCache:
    def __init__(self):
        self.data = {}
    
    async def setex(self, key, seconds, value):
        self.data[key] = value
    
    async def get(self, key):
        return self.data.get(key)
    
    async def exists(self, key):
        return key in self.data
    
    async def delete(self, key):
        self.data.pop(key, None)

_cache = SimpleCache()

async def get_redis():
    return _cache

# Database dependency (sync version for psycopg2)
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Models (same as before)
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    connected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Group(Base):
    __tablename__ = "groups"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    creator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class GroupMember(Base):
    __tablename__ = "group_members"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[str] = mapped_column(String(36), ForeignKey("groups.id"))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Message(Base):
    __tablename__ = "messages"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    sender_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    message_type: Mapped[str] = mapped_column(String(10), default="text")
    group_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("groups.id"))
    private_chat_id: Mapped[Optional[str]] = mapped_column(String(100))

# Create tables (sync version)
def create_tables():
    if engine:
        Base.metadata.create_all(bind=engine)