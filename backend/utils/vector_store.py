import faiss
import numpy as np
import json
import os
from typing import List, Dict, Tuple
from config import settings

class VectorStore:
    def __init__(self):
        self.dimension = 1536  # OpenAI ada-002 embedding dimension
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata: List[Dict] = []
        
    def add_embeddings(self, embeddings: List[List[float]], metadata_list: List[Dict]):
        """
        Add embeddings and their metadata to the vector store.
        """
        vectors = np.array(embeddings).astype('float32')
        self.index.add(vectors)
        self.metadata.extend(metadata_list)
        
    def search(self, query_embedding: List[float], k: int = settings.top_k_results) -> List[Tuple[int, float, Dict]]:
        """
        Search for similar vectors and return their metadata.
        """
        query_vector = np.array([query_embedding]).astype('float32')
        distances, indices = self.index.search(query_vector, k)
        
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.metadata):
                results.append((idx, float(dist), self.metadata[idx]))
                
        return results
    
    def save(self, filename: str):
        """
        Save the index and metadata to disk.
        """
        index_path = os.path.join(settings.vector_dir, f"{filename}.index")
        metadata_path = os.path.join(settings.vector_dir, f"{filename}_metadata.json")
        
        faiss.write_index(self.index, index_path)
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata, f)
            
    def load(self, filename: str):
        """
        Load the index and metadata from disk.
        """
        index_path = os.path.join(settings.vector_dir, f"{filename}.index")
        metadata_path = os.path.join(settings.vector_dir, f"{filename}_metadata.json")
        
        if os.path.exists(index_path) and os.path.exists(metadata_path):
            self.index = faiss.read_index(index_path)
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f) 