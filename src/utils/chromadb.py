import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.utils.utils import parse_text_files_in_folder
import inspect

def get_chromadb_client():
  storage_path = "../chroma_data"
  settings = Settings(
    allow_reset=True
  )
  
  client = chromadb.PersistentClient(path=storage_path, settings=settings)
  return client

def get_chromadb_collection(collection_name='shopee-refund-policy'):
  client = get_chromadb_client()
  try:
    collection = client.get_collection(collection_name)
  except Exception as e:
    sig = inspect.signature(get_chromadb_collection)
    DEFAULT_COLLECTION_NAME = sig.parameters['collection_name'].default
    print(f'error occurred: {e}, defaulting to {DEFAULT_COLLECTION_NAME}')
    
    collection = client.get_collection(DEFAULT_COLLECTION_NAME)
    
  return collection

def setup_chromadb():
  # gets the client and resets the database
  client = get_chromadb_client()
  client.reset()
  
  collection = client.get_or_create_collection('shopee')

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

  
def query_chromadb(query, n, collection_name):
  collection = get_chromadb_collection(collection_name)

  results = collection.query(
    query_texts=[query],
    n_results=n
  )
  
  return results

def generate_relevant_chunks(query: str, collection_name) -> str:
  results = query_chromadb(query, 3, collection_name)
  output = results.get('documents', [''])[0]
  return output