# python distribution
FROM python:3.10

# set working directory
WORKDIR /app

# copies requirements.txt file to working directory and runs
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy streamlit files
COPY . .

# exposes port for streamlit app
EXPOSE 8501

# runs command to run streamlit app
CMD ["streamlit", "run", "src/streamlit/app.py", "--server.port", "8501"]