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
  
  messages = relationship("ConversationMessage", back_populates="conversation")

# define conversation_messages table - stores all the messages from each conversation
class ConversationMessage(Base):
  __tablename__ = 'conversation_messages'

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=False)
  sender = Column(String(50), nullable=False)
  content = Column(Text, nullable=False)
  created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
  
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

  def add_conversation(self, profile, title):
    conversation_id = uuid.uuid4() # define conversation_id
    
    with self.session() as session_local:
      # table entry
      msg = Conversation(
        id=conversation_id,
        profile=profile,
        title=title
      )
      # add entry and commit
      session_local.add(msg)
      session_local.commit()
    # return the conversation_id for usage
    return conversation_id

  def update_conversation(self, conversation_id, **kwargs):
    with self.session() as session_local:
      # retrieve conversation based on conversation_id
      conversation = session.query(Conversation).filter_by(id=conversation_id).first()
      
      # check conversation
      if not conversation:
        raise ValueError(f"Conversation with ID {conversation_id} does not exist.")
      
      # update the columns accordingly
      for key, value in kwargs.items():
        conversation.key = value
      
      session_local.commit()
        
  def add_message(self, conversation_id, sender, content):
    add_update_datetime = datetime.datetime.utcnow() # define the current datetime to use for adding and updating
    
    with self.session() as session_local:
      # retrieve conversation based on conversation_id
      conversation = session_local.query(Conversation).filter_by(id=conversation_id).first()
      
      # check conversation
      if not conversation:
        raise ValueError(f"Conversation with ID {conversation_id} does not exist.")
      
      # updated conversation's updated_at datetime
      conversation.updated_at = add_update_datetime
      
      # table entry for conversation_message
      msg = ConversationMessage(
        conversation_id=conversation_id,
        sender=sender,
        content=content,
        created_at=add_update_datetime
      )
      # add entry and commit both changes
      session_local.add(msg)
      session_local.commit()
  
  def get_conversation_history(self, conversation_id):
    with self.session() as session_local:
      conversation_history = session_local.query(ConversationMessage)\
                          .order_by(ConversationMessage.created_at.asc())\
                          .filter_by(conversation_id=conversation_id)\
                          .all()
                          
    cleaned_conversation_history = [
      {
        "role": message.sender,
        "content": message.content
      }
      for message in conversation_history
    ]
    return cleaned_conversation_history
  
  def get_top_k_conversations(self, k=5):
    with self.session() as session_local:
      return session_local.query(Conversation)\
                          .order_by(Conversation.updated_at.desc())\
                          .limit(k)\
                          .all()
                          
  def get_most_recent_conversation(self):
    return self.get_top_k_conversations(k=1)