import ollama
import streamlit as st
# from st_copy import copy_button
import datetime
import time
import os, sys
import json
from dataclasses import dataclass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.streamlit.helper import (
  get_starter_message,
  convert_conversation_to_text,
  convert_conversation_to_pdf_file
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
from src.db.chromadb_queries import generate_relevant_chunks

from src.utils.utils import (
  get_prompt, 
  collect_text_stream, 
  convert_text_to_stream,
  parse_json
)
from src.utils.tavily_search import tavily_search

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
# @st.cache_data
# def init_session_state():
if "current_conversation_id" not in st.session_state and "current_profile" not in st.session_state:
  most_recent_conversation = get_most_recent_conversation(db=postgresdb)
  if most_recent_conversation:
    st.session_state.current_conversation_id = most_recent_conversation[0].id
    st.session_state.current_profile = most_recent_conversation[0].profile
  else:
    st.session_state.current_conversation_id = add_conversation(db=postgresdb, profile=objects.DEFAULT_PROFILE, title="")
    st.session_state.current_profile = objects.DEFAULT_PROFILE
  
# initialise message history
if st.session_state.current_conversation_id:
  st.session_state.messages = get_conversation_history(
    db=postgresdb, conversation_id=st.session_state.current_conversation_id
  )
elif messages not in st.session_state:
  st.session_state.messages = []

# init_session_state()

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
    helper_msg = objects.profile_mapping[profile]["help"]
    icon = objects.profile_mapping[profile]["icon"]
    
    if column.button(profile, icon=icon, help=helper_msg, use_container_width=True):
      st.session_state.current_profile = profile
      st.session_state.current_conversation_id = add_conversation(
        db=postgresdb, profile=profile, title=""
      )  # add a conversation
      st.session_state.messages = [] # reset session_state messages
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

def format_button_label(conversation):
  conversation_id = conversation.id
  profile = conversation.profile
  title = conversation.title
  icon = objects.profile_mapping[profile]["icon"]
  
  label = f"""
  **{title}**
  :small[{icon} *{profile}* -- *{conversation_id}*]
  """
  
  return label
 
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
    left, right = st.columns([0.9, 0.1], vertical_alignment="center")
    with left:
      st.button(
        label=format_button_label(conversation),
        on_click=change_conversation,
        args=[conversation],
        use_container_width=True
      )
    with right:
      if st.button(label="", icon="❌", key=f"del_{conversation.id}", type="tertiary"):
        delete_conversation(postgresdb, conversation.id)
        latest_conversation = get_most_recent_conversation(postgresdb)
        change_conversation(latest_conversation[0])
        st.rerun()

# --- Header ---
# st.header(f"💬 Chat - {st.session_state.current_profile}")

# --- Profile Response Logic ---
def get_profile_prompt(profile:str, query: str):
  formatted_profile = profile.lower()
  prompt = get_prompt(formatted_profile)
  
  current_datetime = datetime.datetime.utcnow()
  
  collections_mapping = {
    "shopee": "shopee"
  }
  
  collection = collections_mapping.get(formatted_profile, "")
  if collection:
    chunks, metadata = generate_relevant_chunks(
      db=chromadb, query=query, collection_name=collection
    )
    context = "\n".join(chunks)
    prompt = prompt.format(context=context, current_datetime=current_datetime)
  else:
    prompt = prompt.format(current_datetime=current_datetime)
    metadata = []
  
  return prompt, metadata

def get_response(profile: str, query: str) -> str:
  system_message, metadata = get_profile_prompt(profile, query)
  
  system_message_formatted = {
    "role": "system",
    "content": system_message,
  }
  
  user_message_formatted = {
    "role": "user",
    "content": query,
  }

  messages = [
    system_message_formatted,
    *st.session_state.messages,
    user_message_formatted
  ]

  model_name = 'mistral:latest'
  # start_time = time.time()
  
  tools_mapping = {
    "General": [tavily_search]
  }
  
  tools = tools_mapping.get(profile, [])
  
  print('generating message...')
 
  # for tools, you need to update ollama for streaming - pip install -U ollama
  stream = ollama.chat(
    model=model_name, 
    messages=messages,
    stream=True,
    tools=tools,
  )
  
  for chunk in stream:
    chunk_content = chunk.message.content
    # if chunk.message.tool_calls:
    #   tool_content = chunk.message.tool_calls
    #   print(tool_content)
    yield chunk_content

  # time_taken = time.time() - start_time
  # print(time_taken)
  # yield f"\n\n :gray-badge[:small[*:timer_clock: Time taken  &mdash; {time_taken: .2f} seconds*]]"

# --- Display Chat History ---
for message in st.session_state.messages:
  message_role = message["role"]
  message_content = message["content"]
  message_help = message.get("help", "")
  st.chat_message(message_role).markdown(message_content, help=message_help)

# --- Starter Message ---
curr_profile = st.session_state.get("current_profile", objects.DEFAULT_PROFILE)
starter_msg = get_starter_message(curr_profile)
starter_msg_role = starter_msg["role"]
starter_msg_content = starter_msg["content"]
starter_msg_help = starter_msg.get("help", "")
starter_msg_content_stream = convert_text_to_stream(starter_msg_content)

if len(st.session_state.messages) == 0:
  with st.chat_message(starter_msg_role):
    st.write_stream(starter_msg_content_stream)
    st.markdown(body="", help=starter_msg_help)
    
  st.session_state.messages.append(starter_msg)
  
  add_message(
    db=postgresdb,
    conversation_id=st.session_state.current_conversation_id,
    sender=starter_msg_role,
    content=starter_msg_content,
    helper=starter_msg_help
  ) # add message to database
  
# --- User Input ---
user_input = st.chat_input("Type your message here...")

# --- On New Message ---
if user_input:
  # to write user_input first
  st.chat_message("user").write(user_input)
  user_message = {
    "role": "user",
    "content": user_input,
  }
  st.session_state.messages.append(user_message)
  
  add_message(
    db=postgresdb,
    conversation_id=st.session_state.current_conversation_id,
    sender="user",
    content=user_input
  ) # add message to database
 
  # get response
  with st.spinner("Generating response...", show_time=True):
    response_stream = get_response(st.session_state.get("current_profile", objects.DEFAULT_PROFILE), user_input)
    ai_message_box = st.chat_message("assistant").empty()
    
    collected_chunks = ""
    
    for chunk in response_stream:
      collected_chunks += chunk
      ai_message_box.markdown(collected_chunks)
    
  assistant_message = {
    "role": "assistant",
    "content": collected_chunks,
  }
  st.session_state.messages.append(assistant_message)
  
  add_message(
    db=postgresdb,
    conversation_id=st.session_state.current_conversation_id,
    sender="assistant",
    content=collected_chunks
  ) # add message to database

  
# def fetch_pdf_file_contents():
#   pdf_file = convert_conversation_for_download(st.session_state.messages)

#   with open(pdf_file, "rb") as pdf_file:
#     pdf_bytes = pdf_file.read()

# st.download_button(
#   label="Download PDF",
#   data=pdf_bytes,
#   file_name=f"conversation_history_{time.time()}",
#   mime='application/octet-stream',
#   icon=":material/download:"
# )