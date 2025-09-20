# database.py
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, Integer
from datetime import datetime
from typing import List, Optional

# Get database URL from environment (Render will provide this)
DATABASE_URL = os.getenv("DATABASE_URL")

# Convert postgresql:// to postgresql+asyncpg:// if needed
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create async engine
engine = None
async_session_maker = None

if DATABASE_URL:
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

# Simple in-memory cache instead of Redis (free tier)
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

# Global cache instance
_cache = SimpleCache()

async def get_redis():
    return _cache

# Database dependency
async def get_db():
    if not async_session_maker:
        raise Exception("Database not configured")
    
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# SQLAlchemy models
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    connected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    sent_messages: Mapped[List["Message"]] = relationship("Message", back_populates="sender")
    group_memberships: Mapped[List["GroupMember"]] = relationship("GroupMember", back_populates="user")
    created_groups: Mapped[List["Group"]] = relationship("Group", back_populates="creator")

class Group(Base):
    __tablename__ = "groups"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(10), nullable=False)  # public, private
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    creator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="created_groups")
    members: Mapped[List["GroupMember"]] = relationship("GroupMember", back_populates="group")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="group")

class GroupMember(Base):
    __tablename__ = "group_members"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[str] = mapped_column(String(36), ForeignKey("groups.id"))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="group_memberships")

class Message(Base):
    __tablename__ = "messages"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    sender_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    message_type: Mapped[str] = mapped_column(String(10), default="text")  # text, system
    
    # Either group_id or private_chat_id will be set, not both
    group_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("groups.id"))
    private_chat_id: Mapped[Optional[str]] = mapped_column(String(100))  # Format: chat_userid1_userid2
    
    # Relationships
    sender: Mapped["User"] = relationship("User", back_populates="sent_messages")
    group: Mapped[Optional["Group"]] = relationship("Group", back_populates="messages")

# Create all tables
async def create_tables():
    if engine:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)