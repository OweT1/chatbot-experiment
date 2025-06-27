# chatbot-experiment

Used to be the use of Shopee's Refund policy to answer questions. Now expanded for general and specific questions, including Shopee's Refund Policy.

# Project Set-up

The old code can be found in `main.ipynb`. Before using the code, we will need to do an installation of Ollama, as we are using the `mistral` model from Ollama.

## Ollama

Ollama can be installed over at [https://ollama.com/download](https://ollama.com/download).

After the installation of Ollama, you will need to do `ollama pull mistral` in the Command Prompt to install the model in order to use the model for QA.

## Docker

Docker can be installed over at [https://docs.docker.com/get-started/get-docker/](https://docs.docker.com/get-started/get-docker/).

Docker is required to host the databases for our chatbot.

## Others

It is required to have an `.env` file containing the following information:

- TAVILY_API_KEY (to get an API key from the [Official Tavily Website](https://www.tavily.com/))
- POSTGRES_USERNAME (determined by you)
- POSTGRES_PASSWORD (determined by you)
- POSTGRES_DATABASE_NAME (determined by you)

# Project Start

1. Install the requirements in `requirements.txt` using `pip install -r requirements.txt`.
2. In the project folder, run `docker compose up -d` to run the docker containers for our databases
3. In the project folder, run `streamlit run src/streamlit/app.py` to run the streamlit app, which will automatically open in your current browser.

Feel free to try it out on your end! :D
