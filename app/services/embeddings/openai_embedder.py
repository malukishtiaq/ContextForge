from __future__ import annotations

import time
import logging
from typing import List
from openai import OpenAI
from openai import RateLimitError, APIError, APIConnectionError

logger = logging.getLogger(__name__)


class OpenAIEmbedder:
    def __init__(self, api_key: str, base_url: str, model: str, 
                 batch_size: int = 512, max_retries: int = 5) -> None:
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embed multiple texts with batching and retry logic.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        vectors: list[list[float]] = []
        
        # Process in configurable batches
        for i in range(0, len(texts), self.batch_size):
            chunk = texts[i : i + self.batch_size]
            logger.debug(f"Processing batch {i//self.batch_size + 1}, size: {len(chunk)}")
            vectors.extend(self._embed_with_retry(chunk))
        
        return vectors

    def embed_query(self, text: str) -> list[float]:
        """
        Embed a single query text.
        
        Args:
            text: Query text to embed
            
        Returns:
            Embedding vector
        """
        return self._embed_with_retry([text])[0]

    def _embed_with_retry(self, inputs: list[str]) -> list[list[float]]:
        """
        Embed with exponential backoff and specific error handling.
        
        Args:
            inputs: List of input texts
            
        Returns:
            List of embedding vectors
            
        Raises:
            Exception: After max retries exceeded
        """
        delay = 1.0
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                resp = self._client.embeddings.create(model=self.model, input=inputs)
                return [d.embedding for d in resp.data]
                
            except RateLimitError as e:
                last_exception = e
                wait_time = delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Rate limit hit, waiting {wait_time}s (attempt {attempt + 1})")
                time.sleep(wait_time)
                
            except APIConnectionError as e:
                last_exception = e
                wait_time = delay * (2 ** attempt)
                logger.warning(f"API connection error, waiting {wait_time}s (attempt {attempt + 1})")
                time.sleep(wait_time)
                
            except APIError as e:
                if e.status_code >= 500:  # Server errors
                    last_exception = e
                    wait_time = delay * (2 ** attempt)
                    logger.warning(f"Server error {e.status_code}, waiting {wait_time}s (attempt {attempt + 1})")
                    time.sleep(wait_time)
                else:  # Client errors (4xx) - don't retry
                    logger.error(f"Client error {e.status_code}: {e.message}")
                    raise
                    
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error during embedding: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(delay)
                delay *= 2
        
        # If we get here, all retries failed
        logger.error(f"All {self.max_retries} embedding attempts failed")
        raise last_exception or Exception("Embedding failed after all retries")


