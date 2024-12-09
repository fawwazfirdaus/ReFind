from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict
from pydantic import BaseModel

from utils.grobid import get_grobid_client
from utils.vector_store import get_vector_store

router = APIRouter(prefix="/papers", tags=["papers"])

class Paper(BaseModel):
    title: str
    authors: List[Dict]
    year: str = None
    abstract: str = None
    sections: List[Dict]
    references: List[Dict]

@router.post("/upload", response_model=Paper)
async def upload_paper(file: UploadFile = File(...)):
    """Upload and process a PDF paper."""
    try:
        # Save uploaded file
        content = await file.read()
        pdf_path = f"uploads/{file.filename}"
        with open(pdf_path, "wb") as f:
            f.write(content)
        
        # Process with GROBID
        grobid = get_grobid_client()
        tei_content = await grobid.process_pdf(pdf_path)
        if not tei_content:
            raise HTTPException(status_code=400, detail="Failed to process PDF")
        
        # Extract metadata and content
        metadata = await grobid.extract_metadata(tei_content)
        full_text = await grobid.extract_full_text(tei_content)
        
        # Add to vector store
        vector_store = await get_vector_store()
        if full_text:
            await vector_store.add_texts([full_text], [metadata])
        
        return Paper(
            title=metadata.get('title', ''),
            authors=metadata.get('authors', []),
            abstract=metadata.get('abstract', ''),
            sections=metadata.get('sections', []),
            references=metadata.get('references', [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=Paper)
async def get_paper():
    """Get the current paper's details."""
    try:
        # For now, just return the last processed paper
        vector_store = await get_vector_store()
        if not vector_store.metadata:
            raise HTTPException(status_code=404, detail="No paper found")
        
        last_paper = vector_store.metadata[-1]
        return Paper(
            title=last_paper.get('title', ''),
            authors=last_paper.get('authors', []),
            abstract=last_paper.get('abstract', ''),
            sections=last_paper.get('sections', []),
            references=last_paper.get('references', [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 