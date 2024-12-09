# ReFind Backend

This is the backend service for ReFind, a PDF reference management and querying system.

## Prerequisites

1. Python 3.8+
2. GROBID service running locally
3. OpenAI API key
4. Docker Desktop

## Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy the example environment file and update it with your settings:
```bash
cp .env.example .env
```

4. Install and run GROBID (requires Docker Desktop):
```bash
# Download and run GROBID using Docker
docker pull lfoppiano/grobid:0.8.1
docker run --rm --init --ulimit core=0 -p 8070:8070 lfoppiano/grobid:0.8.1
```

## Running the Server

Start the FastAPI server:
```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

## API Endpoints

- `POST /upload`: Upload a PDF file for processing
- `GET /references`: Get list of references from the processed PDF
- `POST /query`: Submit a query about the paper and its references

## Directory Structure

- `main.py`: FastAPI application and endpoints
- `config.py`: Configuration settings
- `utils/`:
  - `grobid.py`: GROBID client for PDF processing
  - `vector_store.py`: FAISS vector store management
  - `openai_client.py`: OpenAI API integration
- `uploads/`: Directory for uploaded PDF files
- `metadata/`: Directory for storing extracted metadata
- `vectors/`: Directory for storing FAISS indexes 