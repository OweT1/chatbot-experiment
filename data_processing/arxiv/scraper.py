import requests
from bs4 import BeautifulSoup
import pandas as pd

def extract_text(item):
  return item.get_text() if item else None

def scrap_from_link(link):
  response = requests.get(link)
  
  # check request response
  if response.ok:
    soup = BeautifulSoup(response.text, 'html.parser')
    data = soup.find_all('li', 'arxiv-result')

    field_mapping = {
      'title': 'title is-5 mathjax',
      'authors': 'authors',
      'abstract': 'abstract mathjax',
      'submission_details': 'is-size-7',
      'comments': 'comments is-size-7',
    }
    fields = field_mapping.keys()
    
    query_details = pd.DataFrame()

    for entry in data:
      output = {field: [extract_text(entry.find('p', field_mapping[field]))] for field in fields}
      output_df = pd.DataFrame(output)
      query_details = pd.concat([query_details, output_df], axis=0).reset_index(drop=True)
      
    return query_details
  
  # else return none
  else:
    print("link not valid, please try again")
    return None

def scrap_query_n_results(query, n=50):
  size = 50
  start = 0
  
  final_result = pd.DataFrame()
  while start < n:
    print(f'progress: scrapping {start} out of {n}')
    
    link = f'https://arxiv.org/search/?query={query}&start={start}&size={size}&searchtype=all&source=header&abstracts=show'
    scrap_results = scrap_from_link(link)
    final_result = pd.concat([final_result, scrap_results], axis=0).reset_index(drop=True)
    
    start += size # add size to the start point of link
  
  return final_result
    
if __name__ == "__main__":
  query = 'llm'
  query_output = scrap_query_n_results(query, n=50)
  
  print(query_output)
