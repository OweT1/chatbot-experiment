import ollama
import streamlit as st
from fpdf import FPDF
import datetime #, time
import json

from src.db.chromadb_queries import generate_relevant_chunks

from src.utils.utils import (
  parse_json,
  parse_docx,
  get_prompt
)

from src.utils.tavily_search import tavily_search

# --- Helper functions --- #
def collapse_list_to_points(top_msg, list_of_items):
  output = f"{top_msg}:\n"
  
  for item in list_of_items:
    output += f"- {item}\n"
    
  return output
  
def convert_conversation_to_text(messages):
    lines = []
    for msg in messages:
        role = msg["role"].capitalize()
        content = msg["content"]
        lines.append(f"{role}:\n{content}\n")
    return "\n".join(lines)

def collapse_msg_dict(conversation_message: dict[str, str]) -> dict[str, str]:
  role = conversation_message["role"]
  content = conversation_message["content"]
  
  entity_mapping = {
    "assistant": "AI",
    "user": "User"
  }
  
  entity = entity_mapping[role]
  return {entity: content}

def format_datetime(datetime_obj):
  return datetime_obj.strftime("%d %B %Y, %H:%M:%S")
  
# --- Main functions --- #
def convert_conversation_to_pdf_file(conversation_history: list[dict[str, str]]):
  pdf = FPDF()
  pdf.add_page()
  pdf.set_auto_page_break(auto=True, margin=15)
  
  # set pdf settings
  pdf.set_font("Arial", size=12)
  
  # define and format conversation_history
  conversation_updated_history = [collapse_msg_dict(conversation_msg) for conversation_msg in conversation_history]
  
  for msg in conversation_updated_history:
    for speaker, text in msg.items():
      pdf.set_font("Arial", style="B", size=12)
      pdf.cell(0, 10, f"{speaker}:", ln=1)
      
      pdf.set_font("Arial", size=12)
      # Split text into multiple lines to fit page width
      pdf.multi_cell(0, 10, text)
      pdf.ln(2)  # Add a small vertical space after each message
    
  file_name = f"conversation_history.pdf"  
  pdf.output(name=file_name)
  
  return file_name

def get_starter_message(profile: str):
  shopee_documents = parse_json('documents/Shopee/list_of_supported_documents.json')
  shopee_list_of_documents = [f"{clean_document['actual_name']}: {clean_document['link']}" for clean_document in shopee_documents.values()]
  shopee_help_message = collapse_list_to_points(top_msg = "List of Supported Documents", list_of_items=shopee_list_of_documents)

  starter_msg_dict = {
    "General": {
      "role": "assistant",
      "content": "Hey! I am your personal assistant. You can ask me about anything!"
    },
    "Shopee": {
      "role": "assistant",
      "content": "Hey! I am your Shopee personal assistant. You can ask me anything about Shopee and its policies!",
      "help": shopee_help_message
    },
    "Personal": {
      "role": "assistant",
      "content": "Hey! I am your personal assistant. You can ask me about anything regarding Owen!"
    }
  }

  return starter_msg_dict[profile]

def get_profile_prompt(db, profile:str, query: str):
  formatted_profile = profile.lower()
  prompt = get_prompt(formatted_profile)
  
  current_datetime = datetime.datetime.now()

  metadata = []
  if formatted_profile == "shopee":
    chunks, metadata = generate_relevant_chunks(
      db=db, query=query, collection_name="shopee"
    )
    relevant_info = "\n- ".join(chunks)
    formatted_prompt = prompt.format(relevant_information=relevant_info, current_datetime=current_datetime)
    
  elif formatted_profile == "general":
    formatted_prompt = prompt.format(current_datetime=current_datetime)
    
  elif formatted_profile == "personal":
    person_profile = parse_docx("documents/Personal/Resume.docx")
    person_name = "Owen"
    formatted_prompt = prompt.format(person_profile=person_profile, person_name=person_name, current_datetime=current_datetime)
  
  return formatted_prompt, metadata

def get_response(db, profile: str, query: str, message_history: list[dict[str, str]]) -> str:
  system_message, metadata = get_profile_prompt(db, profile, query)
  
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
    *message_history,
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
  
def get_button_helper_and_label(conversation, profile_mapping):
  conversation_id = conversation.id
  profile = conversation.profile
  title = conversation.title
  created_at = format_datetime(conversation.created_at)
  updated_at = format_datetime(conversation.updated_at)
  icon = profile_mapping[profile]["icon"]
  
  help_msg = f"""
  Conversation ID: {conversation_id}\n
  Profile: {profile} {icon}\n
  Conversation Started: {created_at}\n
  Conversation Last Message: {updated_at}
  """
  
  label = f"""
  **{title}**
  :small[{icon} *{profile}* -- *{conversation_id}*]
  """
  
  return help_msg, label