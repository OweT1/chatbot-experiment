import os
from langchain_ollama import ChatOllama
import subprocess
import time

def parse_txt(file_path: str) -> str:
    """
    Parses the .txt file at the input file_path

    Args:
        file_path (str): File path to the desired .txt file

    Returns:
        str: File contents of the .txt file
    """
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    return content

def remove_file_extension(file_name: str) -> str:
    """
    Removes the file extension part from the file_name

    Args:
        file_name (str): Filename to remove file extension

    Returns:
        str: Filename without the file extension
    """
    return file_name.split(".")[0]
  
def parse_text_files_in_folder(folder_path: str) -> dict[str, str]:
    """
    Parses all text files in the folder_path

    Args:
        folder_path (str): Folder path to read all text files

    Returns:
        dict[str, str]: Dictionary containing file names and their content
    """

    text_file_content = {}
    for file_name in os.listdir(folder_path):
    file_path = os.path.join(folder_path, file_name)
    if os.path.isfile(file_path):
        content = parse_txt(file_path)
        new_file_name = remove_file_extension(file_name)
        text_file_content[new_file_name] = content
        
    return text_file_content
  
def get_available_ollama_models():
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        header = lines[0]
        header_parts = header.split()
        model_details = lines[1:]
        
        models = []
        for model_detail in model_details:
            parts = model_detail.split('   ')
            if len(parts) == len(header_parts):
                models.append({
                    header_parts[i]: parts[i]
                    for i in range(len(parts))
                })
        return models
    except subprocess.CalledProcessError as e:
        print(f"Error executing ollama list: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def get_ollama_model(model: str = "mistral:latest") -> ChatOllama:
    """
    Returns a downloaded model (via Ollama) to be used for further tasks.

    Args:
        model (str, optional): The name & version of the model from Mistral. Defaults to "mistral-small-latest".

    Returns:
        ChatOllama: Model to be used for further tasks
    """

    list_of_available_models = [model['NAME'] for model in get_available_ollama_models()]

    DEFAULT_MODEL = list_of_available_models[0]

    if model not in list_of_available_models:
        print(f"Model {model} not available. Defaulting to {DEFAULT_MODEL} instead...")
    else:
        print(f"Using model {model}...")

    return ChatOllama(
        model=model if model in list_of_available_models else DEFAULT_MODEL,
        temperature=0,
        max_retries=2,
    )
    
def get_prompt(profile: str) -> str:
    """
    Returns the prompt for the profile

    Args:
        profile (str): Profile for the llm

    Returns:
        str: Relevant prompt for profile
    """
    return parse_txt(f"prompts/{profile}.txt")

def collect_text_stream(stream) -> str:
    """
    Yields all the text in a text generator/stream

    Args:
        stream: A string generator

    Returns:
        str: The content from the generator, seperated by a whitespace
    """
    
    message = ""
    for chunk in stream:
        message += chunk
    return message

def convert_text_to_stream(text: str, delay: float = 0.1):
    """
    Converts the input text into a generator

    Args:
        text (str): Text to be chunked

    Yields:
        Generator: Yields the chunks in the splitted text
    """
    
    split_text = text.split()
    for chunk in split_text:
        yield chunk + " "
        time.sleep(delay)