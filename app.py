import gradio as gr
from utils.utils import query_chroma_db

def hello_world(text: str) -> str:
  return "Hello World"

app = gr.Interface(hello_world, inputs="textbox", outputs="textbox")

if __name__ == "__main__":
  
  app.launch()