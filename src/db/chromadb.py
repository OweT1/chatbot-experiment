import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.utils.utils import parse_text_files_in_folder
import inspect

class ChromaDB:
  def __init__(self):
    self.storage_path = "../chroma_data"
    self.settings = Settings(allow_reset=True)
    self.client = chromadb.PersistentClient(
      path=self.storage_path,
      settings=self.settings
    )
  
  def setup(self):
    # gets the client and resets the database
    self.client.reset()
    
    collection = self.client.get_or_create_collection('shopee')

    documents = parse_text_files_in_folder('documents/')
    
    text_splitter = RecursiveCharacterTextSplitter(
      chunk_size = 1000,
      chunk_overlap = 200,
      length_function = len
    )
    
    start_chunk = 1
    for doc_name, content in documents.items():
      chunks = text_splitter.split_text(content)
      num_chunks = len(chunks)
      metadatas = [{"document_name": doc_name}] * num_chunks
      ids = [str(x) for x in list(range(start_chunk, start_chunk + num_chunks))]
      
      collection.upsert(
        documents=chunks,
        metadatas=metadatas,
        ids=ids
      )

      start_chunk += num_chunks 
    
    # get the metadata from collection
    metadatas = collection.get(
      include=["metadatas"]
    )['metadatas']
    processed_document_names = list(set([document.get('document_name', '') for document in metadatas]))

    print(f"collection documents: {processed_document_names}")
    print("chromadb has been setup successfully!")