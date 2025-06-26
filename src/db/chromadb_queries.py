def get_chromadb_collection(db, collection_name):
  client = db.client
  try:
    collection = client.get_collection(collection_name)
  except Exception as e:
    sig = inspect.signature(get_chromadb_collection)
    DEFAULT_COLLECTION_NAME = sig.parameters['collection_name'].default
    print(f'error occurred: {e}, defaulting to {DEFAULT_COLLECTION_NAME}')
    
    collection = client.get_collection(DEFAULT_COLLECTION_NAME)
    
  return collection

def query_chromadb(db, query, n, collection_name):
  collection = get_chromadb_collection(db, collection_name)

  results = collection.query(
    query_texts=[query],
    n_results=n
  )
  
  return results

def generate_relevant_chunks(db, query: str, collection_name) -> str:
  results = query_chromadb(db, query, 3, collection_name)
  output = results.get('documents', [''])[0]
  return output