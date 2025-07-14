# chatbot-experiment

Used to be the use of Shopee's Refund policy to answer questions. Now expanded for general and specific questions, including Shopee's Refund Policy.

# Project Set-up

The old code can be found in `main.ipynb`. Before using the code, we will need to do an installation of Ollama, as we are using the `mistral` model from Ollama.

## Ollama

Ollama can be installed over at [https://ollama.com/download](https://ollama.com/download).

After the installation of Ollama, you will need to install the Mistral model by doing:

```
ollama pull mistral
```

## Docker

Docker can be installed over at [https://docs.docker.com/get-started/get-docker/](https://docs.docker.com/get-started/get-docker/).

Docker is required to host the databases for our chatbot.

## Others

It is required to have an `.env` file containing the following information:

- TAVILY_API_KEY (to get an API key from the [Official Tavily Website](https://www.tavily.com/))
- POSTGRES_USERNAME (determined by you)
- POSTGRES_PASSWORD (determined by you)
- POSTGRES_DATABASE_NAME (determined by you)

You can get a copy of the `.env` file by doing:

```
cp .env.template .env
```

## Installing of Project Dependencies

Install the necessary requirements by doing:

```
pip install -r requirements.txt
```

# Project Start

1. In the project folder, run the docker containers for our databases by doing:

```
docker compose up -d
```

2. In the project folder, run the streamlit app by doing:

```
streamlit run src/streamlit/app.py
```

Feel free to try it out on your end! :D
