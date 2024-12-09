from openai import OpenAI
from config import settings
from typing import List, Dict
import tiktoken

client = OpenAI(api_key=settings.openai_api_key)

def get_embedding(text: str) -> List[float]:
    """
    Get embeddings for a text using OpenAI's API.
    """
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=text
    )
    return response.data[0].embedding

def get_completion(
    system_prompt: str,
    user_query: str,
    context: str,
) -> str:
    """
    Get completion from OpenAI's API using the chat model.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_query}"}
    ]
    
    response = client.chat.completions.create(
        model=settings.completion_model,
        messages=messages,
        temperature=0.7,
        max_tokens=1000
    )
    
    return response.choices[0].message.content

def chunk_text(text: str, chunk_size: int = settings.chunk_size, overlap: int = settings.chunk_overlap) -> List[str]:
    """
    Split text into chunks of specified size with overlap.
    """
    encoding = tiktoken.encoding_for_model(settings.embedding_model)
    tokens = encoding.encode(text)
    chunks = []
    
    i = 0
    while i < len(tokens):
        chunk_tokens = tokens[i:i + chunk_size]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
        i += chunk_size - overlap
        
    return chunks 