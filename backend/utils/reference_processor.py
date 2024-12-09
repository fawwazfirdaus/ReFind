from typing import List, Dict, Optional, Set
import logging
import os
import json
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
from queue import PriorityQueue
import numpy as np
from datetime import datetime

from .grobid import GrobidClient
from .vector_store import VectorStore
from .text_chunker import TextChunker
from config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReferenceProcessor:
    def __init__(self, vector_store: VectorStore, grobid_client: GrobidClient):
        """Initialize the reference processor."""
        self.vector_store = vector_store
        self.grobid_client = grobid_client
        self.text_chunker = TextChunker()
        self.processing_queue = PriorityQueue()
        self.processed_refs: Set[str] = set()
        self.processing_lock = asyncio.Lock()
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Create necessary directories
        self.refs_dir = Path(settings.metadata_dir_path) / "references"
        self.refs_content_dir = Path(settings.metadata_dir_path) / "reference_contents"
        self.refs_dir.mkdir(exist_ok=True)
        self.refs_content_dir.mkdir(exist_ok=True)
        
        # Load previously processed references
        self._load_processed_refs()
    
    def _load_processed_refs(self):
        """Load list of previously processed references."""
        processed_file = self.refs_dir / "processed_refs.json"
        if processed_file.exists():
            with open(processed_file, 'r') as f:
                self.processed_refs = set(json.load(f))
    
    def _save_processed_refs(self):
        """Save list of processed references."""
        processed_file = self.refs_dir / "processed_refs.json"
        with open(processed_file, 'w') as f:
            json.dump(list(self.processed_refs), f)
    
    def add_to_queue(self, ref_id: str, pdf_path: str, priority: int = 1):
        """Add a reference to the processing queue."""
        if ref_id not in self.processed_refs:
            # Lower number = higher priority
            self.processing_queue.put((priority, {
                'ref_id': ref_id,
                'pdf_path': pdf_path,
                'added_time': datetime.now().isoformat()
            }))
            logger.info(f"Added reference to queue: {ref_id}")
    
    async def process_queue(self):
        """Process references in the queue."""
        while not self.processing_queue.empty():
            try:
                async with self.processing_lock:
                    _, ref_data = self.processing_queue.get_nowait()
                    ref_id = ref_data['ref_id']
                    pdf_path = ref_data['pdf_path']
                    
                    if ref_id in self.processed_refs:
                        continue
                    
                    logger.info(f"Processing reference: {ref_id}")
                    
                    # Process the PDF
                    success = await self.process_reference(ref_id, pdf_path)
                    
                    if success:
                        self.processed_refs.add(ref_id)
                        self._save_processed_refs()
                        logger.info(f"Successfully processed reference: {ref_id}")
                    else:
                        logger.error(f"Failed to process reference: {ref_id}")
                    
            except Exception as e:
                logger.error(f"Error processing reference queue: {str(e)}")
            
            # Small delay to prevent overwhelming the system
            await asyncio.sleep(1)
    
    async def process_reference(self, ref_id: str, pdf_path: str) -> bool:
        """Process a single reference paper."""
        try:
            # Extract text using GROBID
            tei_content = await self.grobid_client.process_pdf(pdf_path)
            if not tei_content:
                return False
            
            # Parse the TEI content
            metadata = await self.grobid_client.extract_metadata(tei_content)
            full_text = await self.grobid_client.extract_full_text(tei_content)
            
            if not full_text:
                return False
            
            # Chunk the text
            chunks = self.text_chunker.chunk_text(full_text)
            
            # Create embeddings and store in vector store
            chunk_data = []
            for chunk in chunks:
                chunk_data.append({
                    'text': chunk.text,
                    'metadata': {
                        'ref_id': ref_id,
                        'title': metadata.get('title', ''),
                        'authors': metadata.get('authors', []),
                        'chunk_index': chunk.index,
                        'start_line': chunk.start_line,
                        'end_line': chunk.end_line
                    }
                })
            
            # Add to vector store
            await self.vector_store.add_texts([c['text'] for c in chunk_data],
                                            [c['metadata'] for c in chunk_data])
            
            # Save processed content
            content_file = self.refs_content_dir / f"{ref_id}.json"
            with open(content_file, 'w') as f:
                json.dump({
                    'metadata': metadata,
                    'chunks': chunk_data
                }, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing reference {ref_id}: {str(e)}")
            return False
    
    async def search_references(self, query: str, limit: int = 5) -> List[Dict]:
        """Search across all processed references."""
        try:
            results = await self.vector_store.similarity_search(query, limit)
            
            # Group results by reference
            grouped_results = {}
            for result in results:
                ref_id = result['metadata']['ref_id']
                if ref_id not in grouped_results:
                    grouped_results[ref_id] = {
                        'ref_id': ref_id,
                        'title': result['metadata']['title'],
                        'authors': result['metadata']['authors'],
                        'matches': []
                    }
                grouped_results[ref_id]['matches'].append({
                    'text': result['text'],
                    'chunk_index': result['metadata']['chunk_index'],
                    'start_line': result['metadata']['start_line'],
                    'end_line': result['metadata']['end_line']
                })
            
            return list(grouped_results.values())
            
        except Exception as e:
            logger.error(f"Error searching references: {str(e)}")
            return []
    
    def get_queue_status(self) -> Dict:
        """Get current status of the processing queue."""
        return {
            'queue_size': self.processing_queue.qsize(),
            'processed_count': len(self.processed_refs),
            'is_processing': not self.processing_queue.empty()
        }
    
    def get_reference_content(self, ref_id: str) -> Optional[Dict]:
        """Get processed content for a specific reference."""
        try:
            content_file = self.refs_content_dir / f"{ref_id}.json"
            if content_file.exists():
                with open(content_file, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Error loading reference content for {ref_id}: {str(e)}")
            return None 