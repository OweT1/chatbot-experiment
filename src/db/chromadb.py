import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import inspect

from src.utils.utils import (
  parse_json,
  parse_text_files_in_folder
)

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
    # self.client.reset()
    
    collection = self.client.get_or_create_collection('shopee')

    documents = parse_text_files_in_folder('documents/Shopee')
    
    document_details = parse_json('documents/Shopee/list_of_supported_documents.json')
    
    text_splitter = RecursiveCharacterTextSplitter(
      chunk_size = 1000,
      chunk_overlap = 200,
      length_function = len
    )
    
    start_chunk = 1
    for doc_name, content in documents.items():
      chunks = text_splitter.split_text(content)
      num_chunks = len(chunks)
      
      doc_details = document_details.get(doc_name, {})
      full_doc_name = doc_details.get("actual_name", doc_name)
      full_doc_link = doc_details.get("link", "")
      
      metadatas = [{"document_name": full_doc_name, "document_link": full_doc_link}] * num_chunks
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