from typing import List, NamedTuple
import re

class TextChunk(NamedTuple):
    text: str
    index: int
    start_line: int
    end_line: int

class TextChunker:
    def __init__(self, max_tokens: int = 512, overlap: int = 50):
        self.max_tokens = max_tokens
        self.overlap = overlap
        
    def _estimate_tokens(self, text: str) -> int:
        """Rough estimation of tokens in text."""
        return len(text.split())
    
    def _get_line_numbers(self, text: str, start_idx: int, end_idx: int) -> tuple[int, int]:
        """Get line numbers for a text span."""
        prefix = text[:start_idx]
        chunk = text[start_idx:end_idx]
        start_line = prefix.count('\n') + 1
        end_line = start_line + chunk.count('\n')
        return start_line, end_line
    
    def chunk_text(self, text: str) -> List[TextChunk]:
        """Split text into overlapping chunks."""
        chunks = []
        words = text.split()
        current_chunk = []
        current_size = 0
        chunk_index = 0
        start_idx = 0
        
        for i, word in enumerate(words):
            current_chunk.append(word)
            current_size += 1
            
            if current_size >= self.max_tokens:
                # Get the text span for line numbers
                chunk_text = ' '.join(current_chunk)
                end_idx = start_idx + len(chunk_text)
                start_line, end_line = self._get_line_numbers(text, start_idx, end_idx)
                
                # Create chunk
                chunks.append(TextChunk(
                    text=chunk_text,
                    index=chunk_index,
                    start_line=start_line,
                    end_line=end_line
                ))
                
                # Keep overlap tokens for next chunk
                overlap_tokens = current_chunk[-self.overlap:] if self.overlap > 0 else []
                current_chunk = overlap_tokens
                current_size = len(overlap_tokens)
                chunk_index += 1
                start_idx = end_idx - len(' '.join(overlap_tokens))
        
        # Add remaining text as final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            end_idx = start_idx + len(chunk_text)
            start_line, end_line = self._get_line_numbers(text, start_idx, end_idx)
            
            chunks.append(TextChunk(
                text=chunk_text,
                index=chunk_index,
                start_line=start_line,
                end_line=end_line
            ))
        
        return chunks 