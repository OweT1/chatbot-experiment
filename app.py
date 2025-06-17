import ollama
import streamlit as st
from utils.chromadb import generate_relevant_chunks
from utils.utils import (
  get_prompt, 
  collect_text_stream, 
  convert_text_to_stream)
import time

# --- Header ---
st.header("💬 My Personal Assistant Bot")

# --- Sidebar with profile selection ---
st.sidebar.header("Profile Settings")

profiles = [
  "General",
  "Shopee"
]
_profile = st.sidebar.selectbox("Profile", profiles)

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
  
  print('generating message...')
 
  stream = ollama.chat(
    model=model_name, 
    messages=messages,
    stream=True
  )
  
  for chunk in stream:
    chunk_content = chunk['message']['content']
    yield chunk_content
 
  print('time taken to generate message:', time.time() - start_time)

# --- Display Chat History ---
for message in st.session_state.messages[_profile]:
  message_role = message["role"]
  message_content = message["content"]
  
  st.chat_message(message_role).write(message_content)

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