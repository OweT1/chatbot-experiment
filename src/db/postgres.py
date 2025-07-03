from sqlalchemy import create_engine, Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID
from dotenv import load_dotenv
import os
import uuid
import datetime

# GETTING OF .ENV VARIABLES
load_dotenv()

# define base
Base = declarative_base()

# define conversations table - stores all the unique conversations
class Conversation(Base):
  __tablename__ = 'conversations'
  
  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  profile = Column(String(50), nullable=False)
  title = Column(Text)
  created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
  updated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
  
  messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete")

# define conversation_messages table - stores all the messages from each conversation
class ConversationMessage(Base):
  __tablename__ = 'conversation_messages'

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=False)
  sender = Column(String(50), nullable=False)
  content = Column(Text, nullable=False)
  created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
  helper = Column(Text)
  
  conversation = relationship("Conversation", back_populates="messages")

class PostgresDB:
  def __init__(self):
    self.username = os.environ.get("POSTGRES_USERNAME")
    self.password = os.environ.get("POSTGRES_PASSWORD")
    self.database_name = os.environ.get("POSTGRES_DATABASE_NAME")
    self.database_url = f"postgresql+psycopg2://{self.username}:{self.password}@localhost:5432/{self.database_name}"
    
    self.engine = create_engine(self.database_url)
    self.session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
  def setup(self):
    Base.metadata.create_all(self.engine)
    print('postgresdb successfully set-up!') 