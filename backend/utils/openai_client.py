from openai import OpenAI
from config import settings
from typing import List, Dict, Tuple
import tiktoken
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def get_embedding(text: str, max_retries: int = 3, retry_delay: float = 1.0) -> List[float]:
    """Get embeddings for a text using OpenAI's API with retries."""
    for attempt in range(max_retries):
        try:
            logger.info(f"Generating embedding (attempt {attempt + 1}/{max_retries})")
            response = client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=text
            )
            logger.debug(f"Generated embedding with dimension {len(response.data[0].embedding)}")
            return response.data[0].embedding
            
        except Exception as e:
            if "rate limit" in str(e).lower():
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Rate limit hit, waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
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
    source_type: str,
    section_title: str = "Main Text",
    chunk_size: int = settings.CHUNK_SIZE,
    overlap: int = settings.CHUNK_OVERLAP
) -> List[Dict[str, any]]:
    """Split text into chunks of specified size with overlap."""
    try:
        logger.info(f"Starting text chunking for section: {section_title}")
        encoding = tiktoken.encoding_for_model(settings.OPENAI_EMBEDDING_MODEL)
        tokens = encoding.encode(text)
        
        total_tokens = len(tokens)
        logger.info(f"Text tokenization - Total tokens: {total_tokens}")
        
        # Safety check for overlap
        if overlap >= chunk_size:
            logger.warning(f"Overlap ({overlap}) >= chunk_size ({chunk_size}). Reducing overlap.")
            overlap = chunk_size // 4  # Set overlap to 25% of chunk size
        
        chunks = []
        chunk_count = 0
        start_idx = 0
        
        while start_idx < len(tokens):
            # Get chunk tokens
            end_idx = min(start_idx + chunk_size, len(tokens))
            chunk_tokens = tokens[start_idx:end_idx]
            
            # If we're at the end and the chunk is too small, merge with previous chunk
            if len(chunk_tokens) < chunk_size // 2 and chunks:
                logger.info(f"Last chunk too small ({len(chunk_tokens)} tokens), merging with previous chunk")
                break
            
            chunk_text = encoding.decode(chunk_tokens)
            
            # Calculate token statistics and positions
            chunk_token_count = len(chunk_tokens)
            start_char = len(encoding.decode(tokens[:start_idx]))
            end_char = start_char + len(chunk_text)
            
            # Calculate line numbers (approximate)
            text_before = text[:start_char]
            text_chunk = text[start_char:end_char]
            start_line = text_before.count('\n') + 1
            end_line = start_line + text_chunk.count('\n')
            
            logger.info(f"Creating chunk {chunk_count}: tokens {start_idx}-{end_idx} (size: {chunk_token_count})")
            
            chunk_info = {
                "text": chunk_text,
                "tokens": chunk_token_count,
                "start_char": start_char,
                "end_char": end_char,
                "start_line": start_line,
                "end_line": end_line,
                "chunk_index": chunk_count,
                "source_type": source_type,
                "section": section_title
            }
            
            chunks.append(chunk_info)
            chunk_count += 1
            
            # Move to next chunk with overlap
            # Ensure we make forward progress
            next_start = end_idx - overlap
            if next_start <= start_idx:
                logger.warning(f"Overlap causing no forward progress at position {start_idx}. Adjusting.")
                next_start = start_idx + max(1, chunk_size // 4)
            start_idx = min(next_start, len(tokens))
            
            # Safety check - prevent infinite loops
            if chunk_count > total_tokens / (chunk_size // 2):
                logger.error("Too many chunks created. Possible infinite loop. Stopping.")
                break
        
        # Log chunking statistics
        if chunks:
            avg_chunk_size = sum(len(c["text"]) for c in chunks) / len(chunks)
            avg_tokens = sum(c["tokens"] for c in chunks) / len(chunks)
            
            logger.info(f"Text chunking statistics:")
            logger.info(f"- Total chunks: {len(chunks)}")
            logger.info(f"- Average chunk size: {avg_chunk_size:.1f} characters")
            logger.info(f"- Average tokens per chunk: {avg_tokens:.1f}")
            logger.info(f"- Overlap size: {overlap} tokens")
        else:
            logger.warning("No chunks were created!")
        
        return chunks
    except Exception as e:
        logger.error(f"Error chunking text: {str(e)}")
        raise