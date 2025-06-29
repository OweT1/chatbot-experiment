import streamlit as st
from fpdf import FPDF
import time
import json

def get_starter_message(profile: str):
  with open('documents/Shopee/list_of_supported_documents.json', 'r') as json_file:
    shopee_documents = json.load(json_file)
  list_of_documents = "\n".join([f"{key}: {value}" for key, value in shopee_documents.items()])
  
  starter_msg_dict = {
    "General": {
      "role": "assistant",
      "content": "Hey! I am your personal assistant. You can ask me about anything!"
    },
    "Shopee": {
      "role": "assistant",
      "content": "Hey! I am your Shopee personal assistant. You can ask me anything about Shopee and its policies!",
      "help": f"{list_of_documents}"
    },
  }
  
  return starter_msg_dict[profile]
  
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