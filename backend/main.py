from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from config import settings

# Initialize FastAPI app
app = FastAPI(title="ReFind API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.metadata_dir, exist_ok=True)
os.makedirs(settings.vector_dir, exist_ok=True)

class Query(BaseModel):
    text: str

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a PDF file for processing.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # TODO: Implement PDF processing with GROBID
    return {"message": "File uploaded successfully", "filename": file.filename}

@app.get("/references")
async def get_references():
    """
    Get list of references from the processed PDF.
    """
    # TODO: Implement reference retrieval from metadata
    return {"references": []}

@app.post("/query")
async def process_query(query: Query):
    """
    Process a user query using the vector store and LLM.
    """
    # TODO: Implement query processing with FAISS and OpenAI
    return {"answer": "Query processing not implemented yet"} 