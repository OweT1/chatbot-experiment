# --- Scrapping using Selenium --- #
from selenium import webdriver
from selenium.webdriver.common.by import By

def scrap_url_content(url, tag_name, class_name):
  '''
  Returns a list of text pertaining to the content with the html tag_name and class_name in the url.
  
  Input(s): url (str), tag_name (str), class_name (str)
  Output(s): items (List of str)
  
  Uses Selenium to extract out the text content in the input url. Utilises the input tag_name and class_name to specifically identify the required content on the website.
    
  '''
  # Initialise driver
  driver = webdriver.Chrome()
  driver.get(url)
  
  # Finds the web elements with the tag_name and class_name, afterwards converting from WebElement objects to their relevant text
  items = driver.find_elements(By.XPATH, f'//{tag_name}[@class={class_name}]')
  items = [item.text for item in items]
  
  # Closes the website
  driver.close()
  
  return items

# --- Scrapping using BS4 --- #
import requests
from bs4 import BeautifulSoup

def extract_text(item):
  return item.get_text(separator="\n", strip=True) if item else None

def scrap_url_text_context(url, tag_name, class_name):
  response = requests.get(url)
  
  if response.ok:
    soup = BeautifulSoup(response.text, 'html.parser')
    data = soup.find(tag_name, class_=class_name)
    text = extract_text(data)
    
    return text

import yaml
import pandas as pd
import re
import json
import os

def clean_file_name(name: str) -> str:
  return re.sub(r'[^a-zA-Z0-9\s]', '', name)

if __name__ == "__main__":
  with open('data_processing/shopee/url_links.yaml', 'r') as file:
    data_links = yaml.safe_load(file)
    file.close()
  
  common = data_links['common']
  content = data_links['links']
  
  os.makedirs('documents/Shopee', exist_ok=True)
  
  for item_category, config in common.items():
    base_url = config['base_url']
    
    website_content = content[item_category]
    results_df = pd.DataFrame()
    for big_category, sub_categories in website_content.items():
      for sub_category_name, sub_category_items in sub_categories.items():
        for item_name, item_details in sub_category_items.items():
          name = item_details['name']
          clean_name = clean_file_name(name)
          link_add = item_details['link_add']
          tag_name = item_details['tag_name']
          class_name = item_details['class_name']
          
          full_link = base_url + str(link_add)
          link_content = scrap_url_text_context(full_link, tag_name, class_name)
          
          item_details['clean_name'] = clean_name
          item_details['full_link'] = full_link
          item_details['link_content'] = link_content
          
          with open(f'documents/Shopee/{clean_name}.txt', 'w', encoding = 'UTF-8') as output:
            output.write(link_content)
            output.close()
          
          temp_df = pd.DataFrame(item_details, index=[0])
          results_df = pd.concat([results_df, temp_df], axis=0).reset_index(drop=True)
          
    results_json = {}
    for index, row in results_df.iterrows():
      clean_name = clean_file_name(row['name'])
      
      results_json[clean_name] = {
        "actual_name": row['name'],
        "link": row['full_link']
      }
      
    with open(f'documents/Shopee/list_of_supported_documents.json', 'w') as json_file:
      json.dump(results_json, json_file, indent=4)
        
  print(results_df)