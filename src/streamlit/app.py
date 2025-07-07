import streamlit as st
# from st_copy import copy_button
import time
import os, sys
import json
from dataclasses import dataclass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.streamlit.helper import (
  close_dialog,
  collapse_list_to_points,
  convert_conversation_to_text,
  convert_conversation_to_pdf_file,
  create_message_format,
  get_starter_message,
  get_profile_prompt,
  get_response,
  get_button_help_and_label
)

from src.db.postgres import PostgresDB
from src.db.postgres_queries import (
  add_conversation,
  update_conversation,
  delete_conversation,
  add_message,
  get_conversation_history,
  get_top_k_conversations,
  get_all_conversations,
  get_most_recent_conversation
)
from src.db.chromadb import ChromaDB

from src.utils.utils import (
  collect_text_stream, 
  convert_text_to_stream,
  parse_json
)

# --- Set up various databases ---
@st.cache_resource
def init_db():
  # set up postgres
  postgresdb = PostgresDB()
  postgresdb.setup()
  
  # set up chroma
  chromadb = ChromaDB()
  chromadb.setup()
  
  return postgresdb, chromadb

postgresdb, chromadb = init_db()

# --- Initialise objects --- #
@dataclass
class initObjects:
  profile_mapping: dict
  profiles: list
  file_type_mapping: dict
  file_types: list
  DEFAULT_PROFILE: str

@st.cache_resource
def init_objects() -> initObjects:
  profile_mapping = parse_json('src/streamlit/profile_mapping.json')
  profiles = profile_mapping.keys()

  file_type_mapping = parse_json('src/streamlit/file_mapping.json')
  file_types = file_type_mapping.keys()

  DEFAULT_PROFILE = "General"
  
  return initObjects(
    profile_mapping=profile_mapping,
    profiles=profiles,
    file_type_mapping=file_type_mapping,
    file_types=file_types,
    DEFAULT_PROFILE=DEFAULT_PROFILE
  )

objects = init_objects()

# --- Initialise session_state objects --- #
if "current_conversation_id" not in st.session_state and "current_profile" not in st.session_state:
  most_recent_conversation = get_most_recent_conversation(db=postgresdb)
  if most_recent_conversation:
    st.session_state.current_conversation_id = most_recent_conversation[0].id
    st.session_state.current_profile = most_recent_conversation[0].profile
  else:
    st.session_state.current_conversation_id = add_conversation(db=postgresdb, profile=objects.DEFAULT_PROFILE, title="")
    st.session_state.current_profile = objects.DEFAULT_PROFILE
  
# initialise message history
if "messages" not in st.session_state:
  if st.session_state.current_conversation_id:
    st.session_state.messages = get_conversation_history(
      db=postgresdb, conversation_id=st.session_state.current_conversation_id
    )
  else:
    st.session_state.messages = []
  
def add_and_change_conversation_session(profile: str = objects.DEFAULT_PROFILE):
  st.session_state.messages = [] # reset session_state messages
  st.session_state.current_profile = profile
  st.session_state.current_conversation_id = add_conversation(
    db=postgresdb, profile=profile, title=""
  )  # add a conversation

# --- Sidebar with profile selection ---
@st.dialog(title="Choose your profile", width="large")
def choose_profile():
  left, right = st.columns(2)
  column_mapping = {
    "left": left,
    "right": right
  }
  
  for profile in objects.profiles:
    column = column_mapping[objects.profile_mapping[profile]["column"]]
    help_msg = objects.profile_mapping[profile]["help"]
    icon = objects.profile_mapping[profile]["icon"]
    
    if column.button(profile, icon=icon, help=help_msg, use_container_width=True):
      add_and_change_conversation_session(profile=profile)
      close_dialog()
      st.rerun()
      
@st.dialog(title="Choose your desired file type", width="large")
def choose_file_type():
  text_content = convert_conversation_to_text(st.session_state.messages)
  pdf_file_dir = convert_conversation_to_pdf_file(st.session_state.messages)
  
  with open(pdf_file_dir, "rb") as pdf_file:
    pdf_content = pdf_file.read()
    pdf_file.close()
    
  left, middle, right = st.columns(3)
  
  column_mapping = {
    "left": left,
    "middle": middle,
    "right": right
  }
  content_mapping = {
    "text_content": text_content,
    "pdf_content": pdf_content
  }
  
  for file_type in objects.file_types:
    file_mapping = objects.file_type_mapping[file_type]
    column = column_mapping[file_mapping["column"]]
    mime_type = file_mapping["mime"]
    content = content_mapping[file_mapping["content"]]
    
    column.download_button(
      label=file_type,
      data=content,
      file_name=f"chat_history_{int(time.time())}{file_type}",
      mime=mime_type,
      use_container_width=True
    )

def change_conversation(conversation):
  st.session_state.current_conversation_id = conversation.id
  st.session_state.current_profile = conversation.profile
  
def delete_conversation_sidebar(conversation):
  delete_conversation(postgresdb, conversation.id)
  latest_conversation = get_most_recent_conversation(postgresdb)
  if latest_conversation:
    change_conversation(latest_conversation[0])
  else:
    add_and_change_conversation_session()
 
with st.sidebar:
  # Add chat button
  st.button(
    label="Add new Chat",
    on_click=choose_profile,
    icon=":material/open_in_new:",
    use_container_width=True
  )
  
  # --- Download Button ---
  st.button(
    label="Download Current Conversation",
    on_click=choose_file_type,
    icon=":material/download:",
    use_container_width=True
  )
      
  # Previous conversations
  st.header("Conversation History")
  past_conversations = get_all_conversations(db=postgresdb)
  # last_5_conversations = postgresdb.get_top_k_conversations(k=5)
  
  for conversation in past_conversations:
    left, right = st.columns([1, 0.1], vertical_alignment="center")
    with left:
      profile_mapping = objects.profile_mapping
      help_msg, label = get_button_help_and_label(conversation, profile_mapping)
      st.button(
        label=label,
        use_container_width=True,
        help=help_msg,
        on_click=change_conversation,
        args=[conversation],
      )
    with right:
      st.button(
        label="",
        icon="❌",
        key=f"del_{conversation.id}",
        type="tertiary", 
        help="Delete Conversation",
        on_click=delete_conversation_sidebar,
        args=[conversation],
      )

# --- Display Chat History ---
for hist_message in st.session_state.messages:
  hist_message_role = hist_message["role"]
  hist_message_content = hist_message["content"]
  hist_message_help = hist_message["help"]

  st.chat_message(hist_message_role).markdown(hist_message_content, help=hist_message_help)

# --- Starter Message ---
curr_profile = st.session_state.get("current_profile", objects.DEFAULT_PROFILE)
starter_msg = get_starter_message(curr_profile)
starter_msg_role = starter_msg["role"]
starter_msg_content = starter_msg["content"]
starter_msg_help = starter_msg["help"]
starter_msg_content_stream = convert_text_to_stream(starter_msg_content)

if len(st.session_state.messages) == 0:
  starter_message_box = st.chat_message("assistant").empty()
    
  starter_collected_chunks = ""

  for chunk in starter_msg_content_stream :
    starter_collected_chunks += chunk
    starter_message_box.markdown(starter_collected_chunks, help=starter_msg_help)
    
  st.session_state.messages.append(starter_msg)
  
  add_message(
    db=postgresdb,
    conversation_id=st.session_state.current_conversation_id,
    sender=starter_msg_role,
    content=starter_msg_content,
    help=starter_msg_help
  ) # add message to database
  
# --- User Input ---
user_input = st.chat_input("Type your message here...")

# --- On New Message ---
if user_input:
  # to write user_input first
  st.chat_message("user").write(user_input)
  user_message = create_message_format(role="user", content=user_input)
  st.session_state.messages.append(user_message)
  
  add_message(
    db=postgresdb,
    conversation_id=st.session_state.current_conversation_id,
    sender="user",
    content=user_input,
  ) # add message to database
 
  # get response
  with st.spinner("Generating response...", show_time=True):
    curr_profile = st.session_state.get("current_profile", objects.DEFAULT_PROFILE)
    system_message = get_profile_prompt(profile=curr_profile, query=user_input)
    
    if curr_profile == "shopee":
      chunks, metadata = generate_relevant_chunks(
        db=db, query=query, collection_name="shopee"
      )
      collated_metadata = list(set([f"{item['document_name']}: {item['document_link']}" for item in metadata]))
      message_help = collapse_list_to_points(top_msg="List of Referenced Documents", list_of_items=collated_metadata)
    else:
      chunks = []
      message_help = ""
      
    response_stream = get_response(
      profile=curr_profile,
      query=user_input,
      message_history=st.session_state.messages,
      chunks=chunks
    )
    
    ai_message_box = st.chat_message("assistant").empty()
    
    collected_chunks = ""
    
    for chunk in response_stream:
      collected_chunks += chunk
      ai_message_box.markdown(collected_chunks, help=message_help)
    
  assistant_message = create_message_format(role="assistant", content=collected_chunks, help=message_help)
  st.session_state.messages.append(assistant_message)
  
  add_message(
    db=postgresdb,
    conversation_id=st.session_state.current_conversation_id,
    sender="assistant",
    content=collected_chunks,
    help=message_help
  ) # add message to database
