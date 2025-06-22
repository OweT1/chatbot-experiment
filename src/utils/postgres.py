from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# GETTING OF .ENV VARIABLES
load_dotenv()

POSTGRES_USERNAME = os.environ.get("POSTGRES_USERNAME")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_DATABASE_NAME = os.environ.get("POSTGRES_DATABASE_NAME")

# CONNECTION TO POSTGRES
DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_DATABASE_NAME}:5432/postgresdb"

def setup_postgresdb():
  engine = create_engine(DATABASE_URL)
  Session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
  
  with Session_local() as session:
    print('-')
  
  return Session_local()

def add_message(session):
  
  return

def get_top_message(session, k=5):
  return


    
  