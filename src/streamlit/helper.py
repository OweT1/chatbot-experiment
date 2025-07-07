import ollama
import streamlit as st
import streamlit.components.v1 as components
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
def collapse_list_to_points(top_msg: str, list_of_items: list[str]) -> str:
  """
  Takes in a top_msg and a list_of_items and compiles them together

  Args:
      top_msg (str): Message describing the list of items
      list_of_items (list[str]): List of items, usually some form of content

  Returns:
      str: Output with the format of:
        {top_msg}:
        - {item}
        - {item}
        ....
  
  Used primarily for `help` in the streamlit chat messages.
  """
  output = f"{top_msg}:\n"
  
  for item in list_of_items:
    output += f"- {item}\n"
    
  return output
  
def convert_conversation_to_text(messages: list[dict[str, str]]) -> str:
  """
  Converts a conversation (which is a list of dictionary of strings with "role" and "content") into a string

  Args:
      messages (list[dict[str, str]]): List of Dictionary of Strings with "role" and "content" keys

  Returns:
      str: A conversation string in the following format:
        {role}: {content}\n
        {role}: {content}\n
        ...
  
  Used primarily to convert the conversation into a text form for `.txt` and `.docx` files.
  """
  lines = []
  for msg in messages:
      role = msg["role"].capitalize()
      content = msg["content"]
      lines.append(f"{role}: {content}\n")
  return "\n".join(lines)

def collapse_msg_dict(conversation_message: dict[str, str]) -> dict[str, str]:
  """
  Collapses the conversation_message with "role" and "content" keys into a dictionary {role: content}

  Args:
      conversation_message (dict[str, str]): Conversation message with "role" and "content" keys

  Returns:
      dict[str, str]: A dictionary in the format {role: content}
  """
  role = conversation_message["role"]
  content = conversation_message["content"]
  
  entity_mapping = {
    "assistant": "AI",
    "user": "User"
  }
  
  entity = entity_mapping[role]
  return {entity: content}

def format_datetime(datetime_obj):
  """Formats the datetime into a simple format, eg '03 Jan 2025, 14:12:53'"""
  return datetime_obj.strftime("%d %B %Y, %H:%M:%S")

def create_message_format(role: str, content: str, help: str = ""):
  """Returns the input values in the form of a dictionary."""
  return {
    "role": role,
    "content": content,
    "help": help
  }
  
# --- Main functions --- #
def convert_conversation_to_pdf_file(conversation_history: list[dict[str, str]]) -> str:
  """
  Converts the conversation into a PDF file to be downloaded

  Args:
      conversation_history (list[dict[str, str]]): List of conversation messages, in the form of a dictionary with keys "role" and "content"

  Returns:
      str: Name of the PDF file generated
  """
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

def get_starter_message(profile: str) -> dict[str, str]:
  """
  Takes in a profile and returns the starter message in the form of a dictionary.

  Args:
      profile (str): Profile of the chat

  Returns:
      dict[str, str]: Dictionary containing the key details of the starter message for the input profile, with the keys "role", "content" and "help".
  """
  shopee_documents = parse_json('documents/Shopee/list_of_supported_documents.json')
  shopee_list_of_documents = [f"{clean_document['actual_name']}: {clean_document['link']}" for clean_document in shopee_documents.values()]
  shopee_help_message = collapse_list_to_points(top_msg = "List of Supported Documents", list_of_items=shopee_list_of_documents)

  starter_msg_dict = {
    "General": {
      "role": "assistant",
      "content": "Hey! I am your personal assistant. You can ask me about anything!",
      "help": "Powered by Tavily Search!"
    },
    "Shopee": {
      "role": "assistant",
      "content": "Hey! I am your Shopee personal assistant. You can ask me anything about Shopee and its policies!",
      "help": shopee_help_message
    },
    "Personal": {
      "role": "assistant",
      "content": "Hey! I am your personal assistant. You can ask me about anything regarding Owen!",
      "help": "Currently Supporting Resume"
    }
  }

  return starter_msg_dict[profile]

def get_profile_prompt(profile: str) -> str:
  """
  Takes in the profile and returns the formatted prompt.

  Args:
      profile (str): Profile of the chat

  Returns:
      str: Formatted prompt for the chat profile.
  """
  formatted_profile = profile.lower()
  prompt = get_prompt(formatted_profile)
  
  current_datetime = datetime.datetime.now()

  if formatted_profile == "shopee":
    formatted_prompt = prompt.format(current_datetime=current_datetime)
    
  elif formatted_profile == "general":
    formatted_prompt = prompt.format(current_datetime=current_datetime)
    
  elif formatted_profile == "personal":
    person_profile = parse_docx("documents/Personal/Resume.docx")
    person_name = "Owen"
    formatted_prompt = prompt.format(person_profile=person_profile, person_name=person_name, current_datetime=current_datetime)
  
  return formatted_prompt  

def get_response(profile: str, query: str, message_history: list[dict[str, str]], chunks: list[str]) -> str:
  """
  Takes in various information to generate a response using our LLM.

  Args:
      profile (str): Profile of the chat
      query (str): User input Query
      message_history (list[dict[str, str]]): Conversation history of the chat
      chunks (list[str]): List of chunks of relevant information

  Yields:
      Iterator[str]: Chunks of the response
  """
  system_message = get_profile_prompt(profile=profile)
  system_message_formatted = {
    "role": "system",
    "content": system_message,
  }
  
  starter_context = ""
  if chunks:
    starter_context = collapse_list_to_points("Relevant Information", chunks)
    
  user_message_formatted = {
    "role": "user",
    "content": f"{starter_context}\n\n{query}",
  }

  messages = [
    system_message_formatted,
    *message_history,
    user_message_formatted
  ]

  model_name = 'mistral:latest'
  
  tools_mapping = {
    "General": [tavily_search]
  }
  
  tools = tools_mapping.get(profile, [])
 
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
  
def get_button_help_and_label(conversation, profile_mapping):
  """Generates the Conversation Button and Label"""
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

def close_dialog():
  """Function to close Streamlit dialog boxes"""
  components.html(
      """\
      <script>
      document.addEventListener('DOMContentLoaded', function() {
        const modal = parent.document.querySelector('div[data-baseweb="modal"]');
        if (modal) {
            // Apply a fade-out transition
            modal.style.transition = 'opacity 0.5s ease';
            modal.style.opacity = '0';

            // Remove the modal after the fade-out effect finishes
            setTimeout(function() {
                modal.remove();
            }, 100);  // Time corresponds to the transition duration (0.1s)
        }
      });
      </script>
      """,
      height=0,
      scrolling=False,
  )