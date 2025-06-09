import chromadb
from utils import parse_all_text_files_in_folder

def get_chromadb_client():
  storage_path = "../chroma_data"
  client = chromadb.PersistentClient(path=storage_path)
  
  return client

def get_chromadb_collection(collection_name='shopee-refund-policy'):
  client = get_chromadb_client()
  # try:
  #   collection = client.get_collection(collection_name)
  return

def setup_chromadb():
  # gets the client and resets the database
  client = get_chromadb_client()
  client.reset()
  
  collection = client.get_or_create_collection('shopee-refund-policy')

  documents = parse_all_text_files_in_folder('../documents')

  collection.upsert(
    documents=documents,
    ids=[str(x) for x in list(range(1, len(documents)+1))]
  )
  
def query_chromadb(query, n, collection_name='shopee-refund-policy'):
  client = get_chromadb_client()
  
  results = client


if __name__ == "__main__":
  client = get_chromadb_client()
  
  client.delete_collection('shopee-refund-policy')
  client.get_collection('shopee_refund_policy')