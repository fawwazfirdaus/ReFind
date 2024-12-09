from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Optional
from pydantic import BaseModel

from utils.reference_processor import ReferenceProcessor
from utils.vector_store import get_vector_store
from utils.grobid import get_grobid_client

router = APIRouter(prefix="/references", tags=["references"])

# Dependency to get ReferenceProcessor instance
async def get_reference_processor():
    vector_store = await get_vector_store()
    grobid_client = get_grobid_client()
    return ReferenceProcessor(vector_store, grobid_client)

# Models
class SearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 5

class SearchResult(BaseModel):
    ref_id: str
    title: str
    authors: List[Dict]
    matches: List[Dict]

class QueueStatus(BaseModel):
    queue_size: int
    processed_count: int
    is_processing: bool

@router.post("/search", response_model=List[SearchResult])
async def search_references(
    query: SearchQuery,
    ref_processor: ReferenceProcessor = Depends(get_reference_processor)
):
    """Search across all processed reference papers."""
    results = await ref_processor.search_references(query.query, query.limit)
    return results

@router.get("/queue/status", response_model=QueueStatus)
async def get_queue_status(
    ref_processor: ReferenceProcessor = Depends(get_reference_processor)
):
    """Get current status of the reference processing queue."""
    return ref_processor.get_queue_status()

@router.get("/{ref_id}/content")
async def get_reference_content(
    ref_id: str,
    ref_processor: ReferenceProcessor = Depends(get_reference_processor)
):
    """Get the full content of a specific reference."""
    content = ref_processor.get_reference_content(ref_id)
    if not content:
        raise HTTPException(status_code=404, detail="Reference not found")
    return content

@router.post("/{ref_id}/process")
async def process_reference(
    ref_id: str,
    background_tasks: BackgroundTasks,
    ref_processor: ReferenceProcessor = Depends(get_reference_processor)
):
    """Add a reference to the processing queue."""
    # Note: You'll need to implement the logic to get the PDF path
    pdf_path = f"{ref_id}.pdf"  # This is a placeholder
    ref_processor.add_to_queue(ref_id, pdf_path)
    
    # Start processing in the background
    background_tasks.add_task(ref_processor.process_queue)
    
    return {"status": "Reference added to processing queue"} 