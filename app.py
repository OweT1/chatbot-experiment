import gradio as gr
from utils.chromadb import (
  setup_chromadb,
  query_chromadb
)
from utils.utils import get_ollama_model
import chromadb
import time

def generate_relevant_chunks(query: str) -> str:
  results = query_chromadb(query, 3)
  output = results.get('documents', [''])[0]
  return output

def generate_answer_mistral(query: str, history) -> str:
  llm = get_ollama_model()
  
  chunks = generate_relevant_chunks(query)
  context = "\n".join(chunks)
  
  n = 5
  last_few_messages = history[-n:]
  conversation_history = "\n".join(last_few_messages)
  
  system_message = """
  You are an expert question-answering assistant working at Shopee. You are tasked to answer questions related to Shopee's Refund Policy based on the provided context (found in the <context> </context> tags) and the conversation history (found in the <conversation_history> </conversation_history> tags).
  If there is no such context, or if the question is not related to Shopee, reply with "I am only tasked to reply questions related to Shopee's Refund Policy."
  
  Always end your answer with "For more details, you may refer to https://help.shopee.sg/portal/4/article/77152-Refunds-and-Return-Policy."
  Do not make up answers or provide information beyond the context.

  <context>
  {context}
  </context>
  
  <conversation_history>
  {conversation_history}
  </conversation_history>
  """.format(context=context, conversation_history=conversation_history)
  
  messages = [
    (
      "system",
      system_message
    ),
    (
      "human",
      query
    ),
  ]
  
  ai_msg = llm.invoke(messages)
  output = ai_msg.content
  
  letters = 2
  rate = 0.03
  for i in range(0, len(output), letters):
    time.sleep(rate)
    yield output[:i + 1]

def vote(data: gr.LikeData):
  print(data)
  if data.liked:
      print("You upvoted this response: " + data.value["value"])
  else:
      print("You downvoted this response: " + data.value["value"])

markdown = "!['Shopee Logo'](assets/Shopee_Logo.svg)"
html = "<img src='assets/Shopee_Logo.svg'>"
app = gr.ChatInterface(fn=generate_answer_mistral, type="messages", title="Shopee Bot")

if __name__ == "__main__":
  setup_chromadb()
  # demo.launch()
  app.launch()