FROM python:3.11-slim
WORKDIR /app
COPY requirements-pipeline.txt .
RUN pip install --no-cache-dir -r requirements-pipeline.txt
COPY ingestion/ ./ingestion/
COPY sql/ ./sql/
CMD ["python", "ingestion/pipeline.py"]
