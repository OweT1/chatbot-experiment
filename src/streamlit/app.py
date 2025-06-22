import ollama
import streamlit as st
import time
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.chromadb import generate_relevant_chunks
from src.utils.utils import (
  get_prompt, 
  collect_text_stream, 
  convert_text_to_stream
)
from src.utils.tavily_search import tavily_search
from helper import convert_conversation_for_download

# --- Sidebar with profile selection ---
profiles = [
  "General",
  "Shopee"
]

with st.sidebar:
  # Add chat button
  st.button(
    label="Add new Chat",
    on_click=None,
    icon=":material/open_in_new:"
  )
  
  # Top header
  st.header("Chatbot")

  # Profiles
  _profile = st.selectbox("Profile", profiles)

  # Previous conversations
  st.header("Previous Conversations")
  last_5_conversations = ("xxx 1", "xxx 2", "xxx 3", "xxx 4", "xxx 5")
  for conversation in last_5_conversations:
    st.button(
      label=conversation,
      on_click=None,
      use_container_width=True
    )

# --- Header ---
st.header(f"💬 {_profile}")

# --- Session State for Chat History ---
if "messages" not in st.session_state:
  st.session_state.messages = {}
  for profile in profiles:
    st.session_state.messages[profile] = []

# --- Profile Response Logic ---
def get_profile_prompt(profile:str, query: str):
  formatted_profile = profile.lower()
  prompt = get_prompt(profile)
  
  collections_mapping = {
    "shopee": "shopee"
  }
  
  collection = collections_mapping.get(profile, "")
  if collection:
    chunks = generate_relevant_chunks(query, collection)
    context = "\n".join(chunks)
    prompt = prompt.format(context=context)
  
  return prompt

def get_response(profile: str, query: str) -> str:
  system_message = get_profile_prompt(profile, query)
  
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
    *st.session_state.messages[profile],
    user_message_formatted
  ]

  model_name = 'mistral:latest'
  start_time = time.time()
  
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
  
  time_taken = time.time() - start_time
  yield f"\n\n :gray-badge[:small[*:timer_clock: Time taken  &mdash; {time_taken: .2f} seconds*]]"

# --- Display Chat History ---
for message in st.session_state.messages[_profile]:
  message_role = message["role"]
  message_content = message["content"]
  
  st.chat_message(message_role).markdown(message_content)

# --- User Input ---
user_input = st.chat_input("Type your message here...")

# --- Starter Message ---
starter_msg_dict = {
  "General": {
    "role": "assistant",
    "content": "Hey! I am your personal assistant. You can ask me about anything!"
  },
  "Shopee": {
    "role": "assistant",
    "content": "Hey! I am your Shopee personal assistant. You can ask me anything about Shopee and its policies!"
  },
}

starter_msg = starter_msg_dict[_profile]
starter_msg_role = starter_msg["role"]
starter_msg_content = starter_msg["content"]
starter_msg_content_stream = convert_text_to_stream(starter_msg_content)

if len(st.session_state.messages[_profile]) == 0:
  st.chat_message(starter_msg_role).write_stream(starter_msg_content_stream)
  st.session_state.messages[_profile].append(starter_msg)
  
# --- On New Message ---
if user_input:
  # to write user_input first
  st.chat_message("user").write(user_input)
  user_message = {
    "role": "user",
    "content": user_input,
  }
  st.session_state.messages[_profile].append(user_message)
 
  # get response
  response_stream = get_response(_profile, user_input)
  ai_message_box = st.chat_message("assistant").empty()
  
  collected_chunks = ""
  
  for chunk in response_stream:
    collected_chunks += chunk
    ai_message_box.markdown(collected_chunks)
    
  assistant_message = {
    "role": "assistant",
    "content": collected_chunks,
  }

  st.session_state.messages[_profile].append(assistant_message)
  
# --- Download Button ---
# pdf_file = convert_conversation_for_download(st.session_state.messages[_profile])

# with open(pdf_file, "rb") as pdf_file:
#   pdf_bytes = pdf_file.read()

# st.download_button(
#   label="Download PDF",
#   data=pdf_bytes,
#   file_name=f"conversation_history_{time.time()}",
#   mime='application/octet-stream',
#   icon=":material/download:"
# )