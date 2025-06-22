import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

def tavily_search(query:str) -> str:
  """
  Performs a search using the query to get relevant information from the web.

  Args:
      query (str): Query input by user

  Returns:
      str: Information on the web that is relevant to the query.
      
  The information returned should be used to craft a meaningful and informative response to the user. 
  """
  
  print('performing tavily search on', query)
  tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
  response = tavily_client.search(query)
  
  return response