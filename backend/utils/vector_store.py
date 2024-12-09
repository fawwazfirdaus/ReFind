import os
import json
import numpy as np
import faiss
from typing import List, Dict, Optional, Tuple, Any
import logging
from config import settings
import pickle

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, dimension: int = 1536):
        """Initialize the vector store."""
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata: List[Dict] = []
        
        # Create necessary directories
        os.makedirs(settings.VECTOR_DIR, exist_ok=True)
        os.makedirs(settings.metadata_dir_path, exist_ok=True)
    
    async def add_texts(self, embeddings: List[List[float]], metadata_list: List[Dict[str, Any]]) -> None:
        """Add embeddings and their metadata to the vector store."""
        try:
            if not embeddings:
                return
                
            # Convert embeddings to numpy array
            vectors = np.array(embeddings).astype('float32')
            
            # Normalize vectors
            faiss.normalize_L2(vectors)
            
            # Add to FAISS index
            self.index.add(vectors)
            
            # Add metadata
            if not isinstance(metadata_list, list):
                metadata_list = [metadata_list]
            self.metadata.extend(metadata_list)
            
            logger.info(f"Added {len(embeddings)} vectors to the index")
            
        except Exception as e:
            logger.error(f"Error adding vectors to index: {str(e)}")
            raise
    
    def search(self, query_embedding: List[float], k: int = 5) -> List[Tuple[float, int, Dict[str, Any]]]:
        """Search for similar texts using L2 distance."""
        if len(self.metadata) == 0:
            return []
            
        # Convert query to numpy array and reshape for FAISS
        query_array = np.array(query_embedding).astype('float32').reshape(1, -1)
        
        # Normalize the query vector
        faiss.normalize_L2(query_array)
        
        # Search the index
        D, I = self.index.search(query_array, min(k, len(self.metadata)))
        
        # Format results
        results = []
        for i in range(len(I[0])):
            idx = I[0][i]
            if idx < len(self.metadata):  # Safety check
                results.append((float(D[0][i]), idx, self.metadata[idx]))
        
        return results
        
    def save(self, base_filename: str) -> None:
        """Save vector store state to disk."""
        try:
            # Save the FAISS index
            index_path = os.path.join(settings.VECTOR_DIR, f"{base_filename}_index.faiss")
            faiss.write_index(self.index, index_path)
            
            # Save metadata
            metadata_path = os.path.join(settings.VECTOR_DIR, f"{base_filename}_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
                
            logger.info(f"Vector store saved successfully: {base_filename}")
            
        except Exception as e:
            logger.error(f"Error saving vector store: {str(e)}")
            raise
            
    def load(self, base_filename: str) -> None:
        """Load vector store state from disk."""
        try:
            # Load the FAISS index
            index_path = os.path.join(settings.VECTOR_DIR, f"{base_filename}_index.faiss")
            if os.path.exists(index_path):
                self.index = faiss.read_index(index_path)
                
            # Load metadata
            metadata_path = os.path.join(settings.VECTOR_DIR, f"{base_filename}_metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    self.metadata = json.load(f)
                    
            logger.info(f"Vector store loaded successfully: {base_filename}")
            
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
            raise
                
    def clear(self) -> None:
        """Clear the vector store state."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []

# Global instance
_vector_store: Optional[VectorStore] = None

async def get_vector_store() -> VectorStore:
    """Get or create the vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store