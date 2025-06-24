# shopee-refund-policy

Use the context of Shopee's Refund Policy to answer questions

# Project Set-up

The old code can be found in `main.ipynb`. Before using the code, we will need to do an installation of Ollama, as we are using the `mistral` model from Ollama.

## Ollama

Ollama can be installed over at [https://ollama.com/download](https://ollama.com/download).

After the installation of Ollama, you will need to do `ollama pull mistral` in the Command Prompt to install the model in order to use the model for QA.

## Others

It is required to have an `.env` file containing the following information:

- TAVILY_API_KEY (to get an API key from the [Official Tavily Website](https://www.tavily.com/))
- POSTGRES_USERNAME (determined by you)
- POSTGRES_PASSWORD (determined by you)
- POSTGRES_DATABASE_NAME (determined by you)
- PYTHONPATH (your full folder directory to this project)
