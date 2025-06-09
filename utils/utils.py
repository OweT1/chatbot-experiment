import os

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
  
def parse_all_text_files_in_folder(folder_path: str) -> list[str]:
  """
  Parses all text files in the folder_path

  Args:
      folder_path (str): Folder path to read all text files

  Returns:
      list[str]: List of text files' content
  """
  
  text_file_content = []
  for file_name in os.listdir(folder_path):
    file_path = os.path.join(folder_path, file_name)
    if os.path.isfile(file_path):
      content = parse_txt(file_path)
      text_file_content.append(content)
      
  return text_file_content
  