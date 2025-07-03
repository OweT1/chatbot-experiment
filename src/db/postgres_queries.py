import uuid
import datetime
from src.db.postgres import Conversation, ConversationMessage

def add_conversation(db, profile, title):
  conversation_id = uuid.uuid4() # define conversation_id
  
  with db.session() as session_local:
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

def update_conversation(db, conversation_id, **kwargs):
  with db.session() as session_local:
    # retrieve conversation based on conversation_id
    conversation = session_local.query(Conversation).filter_by(id=conversation_id).first()
    
    # check conversation
    if not conversation:
      raise ValueError(f"Conversation with ID {conversation_id} does not exist.")
    
    # update the columns accordingly
    for key, value in kwargs.items():
      conversation.key = value
    
    session_local.commit()

def delete_conversation(db, conversation_id):
  with db.session() as session_local:
    # retrieve conversation based on the conversation_id
    conversation = session_local.query(Conversation).filter_by(id=conversation_id).first()
    
    session_local.delete(conversation)
    session_local.commit()

def add_message(db, conversation_id, sender, content, helper=""):
  add_update_datetime = datetime.datetime.utcnow() # define the current datetime to use for adding and updating
  
  with db.session() as session_local:
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
      created_at=add_update_datetime,
      helper=helper,
    )
    # add entry and commit both changes
    session_local.add(msg)
    session_local.commit()

def get_conversation_history(db, conversation_id) -> list[dict[str, str]]:
  with db.session() as session_local:
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

def get_top_k_conversations(db, k=5):
  with db.session() as session_local:
    return session_local.query(Conversation)\
                        .order_by(Conversation.updated_at.desc())\
                        .limit(k)\
                        .all()

def get_all_conversations(db):
  with db.session() as session_local:
    return session_local.query(Conversation)\
                        .order_by(Conversation.updated_at.desc())\
                        .all()
                        
def get_most_recent_conversation(db):
  return get_top_k_conversations(db=db, k=1)