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

url = "https://help.shopee.sg/portal/4/article/77152-Refunds-and-Return-Policy"
tag_name = 'div'
class_name = '"use-tiny-editor"'

text = scrap_url_content(url=url, tag_name=tag_name, class_name=class_name)[0]

with open('Refund Policy Document.txt', 'w', encoding = 'UTF-8') as output:
    output.write(text)
    output.close()

