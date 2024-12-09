from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import aiofiles
import httpx
from typing import List, Dict, Optional
import json
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from config import settings
from utils.grobid import GrobidClient
from utils.vector_store import VectorStore
from utils.openai_client import get_embedding, get_completion, chunk_text

# Initialize FastAPI app
app = FastAPI(title="ReFind API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
os.makedirs(settings.upload_dir_path, exist_ok=True)
os.makedirs(settings.metadata_dir_path, exist_ok=True)
os.makedirs(settings.vector_dir_path, exist_ok=True)

# Initialize components
grobid_client = GrobidClient()
vector_store = VectorStore()

# Store current paper metadata and chunk counter
current_paper: Optional[Dict] = None
global_chunk_counter: int = 0

class Query(BaseModel):
    text: str

class Author(BaseModel):
    firstname: str
    lastname: str
    email: Optional[str] = None
    affiliation: Optional[str] = None
    orcid: Optional[str] = None

class Section(BaseModel):
    title: str
    content: str

class Reference(BaseModel):
    title: str
    authors: List[Author]
    doi: Optional[str] = None
    year: Optional[str] = None
    abstract: Optional[str] = None
    venue: Optional[str] = None

class Paper(BaseModel):
    title: str
    authors: List[Author]
    year: Optional[str] = None
    abstract: Optional[str] = None
    sections: List[Section] = []
    references: List[Reference] = []

async def process_paper_text(text: str, source: str, section: str = "Main Text") -> List[Dict]:
    """Process paper text into chunks and create metadata."""
    global global_chunk_counter
    logger.info(f"Processing text from source: {source}, section: {section}")
    
    try:
        # Get chunks with metadata
        chunks = chunk_text(text, source_type=source, section_title=section)
        chunk_metadata = []
        
        logger.info(f"Starting embedding generation for {len(chunks)} chunks")
        for chunk_index, chunk in enumerate(chunks):
            try:
                logger.info(f"Generating embedding for chunk {global_chunk_counter + 1}")
                logger.info(f"Chunk text length: {len(chunk['text'])} characters")
                
                embedding = get_embedding(chunk["text"])
                logger.info(f"Successfully generated embedding for chunk {global_chunk_counter + 1}")
                
                metadata = {
                    "text": chunk["text"],
                    "source": source,
                    "section": chunk["section"],
                    "chunk_index": global_chunk_counter,  # Use global counter instead of local
                    "tokens": chunk["tokens"],
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                    "start_char": chunk["start_char"],
                    "end_char": chunk["end_char"]
                }
                chunk_metadata.append(metadata)
                vector_store.add_embeddings([embedding], [metadata])
                
                logger.info(f"Added chunk {global_chunk_counter + 1} to vector store")
                global_chunk_counter += 1  # Increment global counter
                
            except Exception as e:
                logger.error(f"Error processing chunk {global_chunk_counter + 1}: {str(e)}")
                continue
        
        logger.info(f"Completed processing {len(chunk_metadata)} chunks from {source}")
        return chunk_metadata
        
    except Exception as e:
        logger.error(f"Error in process_paper_text: {str(e)}")
        raise

@app.post("/upload", response_model=Paper)
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a PDF file."""
    global global_chunk_counter  # Reset counter for each new file
    global_chunk_counter = 0
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        logger.info(f"Processing uploaded file: {file.filename}")
        
        # Save the uploaded file
        file_path = os.path.join(settings.upload_dir_path, file.filename)
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        logger.info("File saved successfully, processing with GROBID")
        
        # Process with GROBID
        metadata = grobid_client.process_pdf(file_path)
        
        # Save metadata
        base_filename = os.path.splitext(file.filename)[0]
        grobid_client.save_metadata(metadata, base_filename)
        
        # Process sections
        logger.info("Processing paper sections")
        for section in metadata.get("sections", []):
            await process_paper_text(
                section["content"],
                f"section:{base_filename}",
                section["title"]
            )
        
        # Process abstract if available
        if metadata["abstract"]:
            logger.info("Processing abstract")
            await process_paper_text(
                metadata["abstract"],
                f"abstract:{base_filename}",
                "Abstract"
            )
        
        # Save vector store
        vector_store.save(base_filename)
        logger.info("Vector store saved successfully")
        
        # Store current paper metadata
        global current_paper
        current_paper = metadata
        
        # Return paper metadata with proper typing
        return Paper(
            title=metadata["title"],
            authors=[Author(**author) for author in metadata["authors"]],
            year=metadata.get("year"),
            abstract=metadata.get("abstract", ""),
            sections=[Section(**section) for section in metadata.get("sections", [])],
            references=[Reference(**ref) for ref in metadata.get("references", [])]
        )
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/paper", response_model=Paper)
async def get_paper():
    """Get current paper metadata."""
    if not current_paper:
        raise HTTPException(status_code=404, detail="No paper has been uploaded yet")
    return Paper(
        title=current_paper["title"],
        authors=[Author(**author) for author in current_paper["authors"]],
        year=current_paper.get("year"),
        abstract=current_paper.get("abstract", ""),
        sections=[Section(**section) for section in current_paper.get("sections", [])],
        references=[Reference(**ref) for ref in current_paper.get("references", [])]
    )

@app.get("/references", response_model=List[Reference])
async def get_references():
    """Get list of references from the processed PDF."""
    if not current_paper:
        return []
    return [Reference(**ref) for ref in current_paper.get("references", [])]

@app.post("/query")
async def process_query(query: Query):
    """Process a user query using the vector store and LLM."""
    try:
        logger.info(f"Processing query: {query.text}")
        
        # Get query embedding
        query_embedding = get_embedding(query.text)
        
        # Search vector store
        results = vector_store.search(query_embedding, k=settings.TOP_K_RESULTS)
        logger.info(f"Found {len(results)} relevant chunks")
        
        # Prepare context from search results
        context_chunks = []
        chunk_sources = []
        total_tokens = 0
        
        for distance, _, metadata in results:
            # Format source information
            source_info = {
                "text": metadata["text"],
                "section": metadata["section"],
                "start_line": metadata["start_line"],
                "end_line": metadata["end_line"],
                "similarity": float(1 - distance)  # Convert distance to similarity score
            }
            chunk_sources.append(source_info)
            
            # Log each chunk's relevance
            logger.info(f"Chunk from {metadata['section']} (similarity: {1-distance:.4f}):")
            logger.info(f"- Lines {metadata['start_line']}-{metadata['end_line']}")
            logger.info(f"- Text preview: {metadata['text'][:100]}...")
            
            context_chunks.append(
                f"[From {metadata['section']}, Lines {metadata['start_line']}-{metadata['end_line']}]:\n{metadata['text']}"
            )
            total_tokens += metadata.get('tokens', len(metadata['text'].split()))
        
        context = "\n\n".join(context_chunks)
        logger.info(f"Total context size: {len(context)} characters, ~{total_tokens} tokens")
        
        # Get completion from LLM
        system_prompt = """You are a helpful research assistant. Answer the question based on the provided context. 
        Always cite the source information provided in square brackets at the start of each context chunk.
        Format your citations like this: [Section Name, Lines X-Y]."""
        
        answer, usage = get_completion(
            system_prompt, 
            query.text, 
            context,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS
        )
        
        # Log completion statistics
        logger.info("Query processing complete:")
        logger.info(f"- Input tokens: {usage['prompt_tokens']}")
        logger.info(f"- Output tokens: {usage['completion_tokens']}")
        logger.info(f"- Total tokens: {usage['total_tokens']}")
        logger.info(f"- Answer length: {len(answer)} characters")
        
        return {
            "answer": answer,
            "metadata": {
                "chunks_used": len(results),
                "token_usage": usage,
                "sources": chunk_sources
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 