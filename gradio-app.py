import gradio as gr
from utils.chromadb import (
  setup_chromadb,
  query_chromadb
)
# from utils.utils import get_ollama_model
import chromadb
import time
import ollama

def generate_relevant_chunks(query: str) -> str:
  results = query_chromadb(query, 3)
  output = results.get('documents', [''])[0]
  return output

def generate_answer_mistral(query: str, history) -> str:
  # llm = get_ollama_model()
  
  chunks = generate_relevant_chunks(query)
  context = "\n".join(chunks)
  
  system_message = """
  You are an expert question-answering assistant working at Shopee. You are tasked to answer questions related to Shopee's Refund Policy based on the provided context (found in the <context> </context> tags).
  If there is no such context, or if the question is not related to Shopee, reply with "I am only tasked to reply questions related to Shopee's Refund Policy."
  
  Always end your answer with "For more details, you may refer to https://help.shopee.sg/portal/4/article/77152-Refunds-and-Return-Policy."
  Do not make up answers or provide information beyond the context.

  <context>
  {context}
  </context>
  """.format(context=context)
  
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
    *history,
    user_message_formatted,
  ]
  print(messages)
  model_name = 'mistral:latest'
  start_time = time.time()
  
  print('generating message...')
 
  stream = ollama.chat(
    model=model_name, 
    messages=messages,
    stream=True
  )
  
  message = ''
  for chunk in stream:
    message += chunk['message']['content']
    yield message
  print('time taken to generate message:', time.time() - start_time)

# markdown = "!['Shopee Logo'](assets/Shopee_Logo.svg)"
# html = "<img src='assets/Shopee_Logo.svg'>"

examples = [
  "What is Shopee's Refund Policy?",
  "If I have just received my product today, how long do I have to return it and get a full refund?",
  "Will I lose money if I cancel my order?"
]

app = gr.ChatInterface(
  fn=generate_answer_mistral,
  examples=examples,
  type="messages", 
  title="Shopee Bot")

if __name__ == "__main__":
  setup_chromadb()
  # demo.launch()
  app.launch()