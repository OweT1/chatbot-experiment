import streamlit as st
from fpdf import FPDF
import time

def convert_dict_to_list(conversation_message: dict[str, str]) -> list[str]:
  
  role = conversation_message["role"]
  content = conversation_message["content"]
  
  entity_mapping = {
    "assistant": "AI",
    "user": "User"
  }
  
  entity = entity_mapping[role]
  
  return [entity, content]
  
@st.cache_data
def convert_conversation_for_download(conversation_history: list[dict[str, str]]):
  
  pdf = FPDF()
  pdf.add_page()
  
  # set pdf settings
  pdf.set_font("Arial", size=12)
  
  # define and format conversation_history
  headers = ["Entity", "Conversation"]
  
  conversation = [convert_dict_to_list(conversation_msg) for conversation_msg in conversation_history]
  
  for col in headers:
    pdf.cell(40, 10, col, border=1, align="C")
  pdf.ln()
  
  for conversation_message in conversation:
    for conversation_data in conversation_message:
      pdf.cell(40, 10, conversation_data, border=1, align="L")
    pdf.ln()
    
  file_name = f"conversation_history_{time.time()}.pdf"
  file_dir = f"conversation_history/{file_name}"
  
  pdf.output(file_dir)
  
  print(f"Conversation history saved at {file_dir}")
  
  return file_dir