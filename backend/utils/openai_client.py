from openai import OpenAI
from config import settings
from typing import List, Dict, Tuple
import tiktoken
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def get_embedding(text: str) -> List[float]:
    """Get embeddings for a text using OpenAI's API."""
    try:
        response = client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=text
        )
        logger.debug(f"Generated embedding with dimension {len(response.data[0].embedding)}")
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise

def get_completion(
    system_prompt: str,
    user_query: str,
    context: str,
    temperature: float = settings.TEMPERATURE,
    max_tokens: int = settings.MAX_TOKENS
) -> Tuple[str, Dict]:
    """Get completion from OpenAI's API using the chat model."""
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_query}"}
        ]
        
        logger.info(f"Sending query to LLM: {user_query}")
        logger.debug(f"Context length: {len(context)} characters")
        
        response = client.chat.completions.create(
            model=settings.OPENAI_COMPLETION_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        answer = response.choices[0].message.content
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
        
        logger.info(f"LLM Response - Tokens used: {usage['total_tokens']} (Prompt: {usage['prompt_tokens']}, Completion: {usage['completion_tokens']})")
        
        return answer, usage
    except Exception as e:
        logger.error(f"Error getting completion: {str(e)}")
        raise

def chunk_text(
    text: str,
    chunk_size: int = settings.CHUNK_SIZE,
    overlap: int = settings.CHUNK_OVERLAP
) -> List[Dict[str, any]]:
    """Split text into chunks of specified size with overlap."""
    try:
        encoding = tiktoken.encoding_for_model(settings.OPENAI_EMBEDDING_MODEL)
        tokens = encoding.encode(text)
        
        total_tokens = len(tokens)
        logger.info(f"Text tokenization - Total tokens: {total_tokens}")
        
        chunks = []
        i = 0
        chunk_count = 0
        
        while i < len(tokens):
            # Get chunk tokens
            chunk_tokens = tokens[i:i + chunk_size]
            chunk_text = encoding.decode(chunk_tokens)
            
            # Calculate token statistics
            chunk_token_count = len(chunk_tokens)
            start_char = len(encoding.decode(tokens[:i]))
            end_char = start_char + len(chunk_text)
            
            chunk_info = {
                "text": chunk_text,
                "tokens": chunk_token_count,
                "start_char": start_char,
                "end_char": end_char,
                "chunk_index": chunk_count
            }
            
            chunks.append(chunk_info)
            chunk_count += 1
            i += chunk_size - overlap
        
        # Log chunking statistics
        avg_chunk_size = sum(len(c["text"]) for c in chunks) / len(chunks)
        avg_tokens = sum(c["tokens"] for c in chunks) / len(chunks)
        
        logger.info(f"Text chunking statistics:")
        logger.info(f"- Total chunks: {len(chunks)}")
        logger.info(f"- Average chunk size: {avg_chunk_size:.1f} characters")
        logger.info(f"- Average tokens per chunk: {avg_tokens:.1f}")
        logger.info(f"- Overlap size: {overlap} tokens")
        
        return chunks
    except Exception as e:
        logger.error(f"Error chunking text: {str(e)}")
        raise