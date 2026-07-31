"""
BM25 Search Engine for project files.
Builds an inverted index and ranks files by relevance to a query.
"""

import math
import re
import time
from collections import Counter
from pathlib import Path

from app.services.project_scanner import ProjectFile, scan_project
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class BM25Search:
    """
    BM25 (Best Match 25) ranking algorithm.
    
    Scores files based on:
    - How often query words appear (term frequency)
    - How rare those words are across all files (inverse document frequency)
    - File length (longer files don't have unfair advantage)
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Args:
            k1: Term frequency saturation (default 1.5).
            b: Length normalization (default 0.75).
        """
        self.k1 = k1
        self.b = b
        
        # Index data
        self.documents: list[dict] = []
        self.doc_count: int = 0
        self.avg_doc_length: float = 0.0
        self.inverted_index: dict[str, dict[int, int]] = {}
        
        # Cache info
        self._is_built = False
        self._build_time: float = 0.0
        self._source_path: str = ""
    
    @staticmethod
    def tokenize(text: str) -> list[str]:
        """
        Split text into searchable tokens.
        Lowercase, extract words, filter short tokens.
        """
        text = text.lower()
        # Match code identifiers: snake_case, camelCase, PascalCase
        tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", text)
        # Also split on common code separators
        for token in list(tokens):
            # Split camelCase
            parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\b)', token)
            if len(parts) > 1:
                tokens.extend([p.lower() for p in parts if len(p) >= 2])
        return [t for t in tokens if len(t) >= 2]
    
    def build_index(
        self, files: list[ProjectFile], source_path: str = ""
    ) -> None:
        """
        Build the search index from project files.
        
        Args:
            files: List of ProjectFile objects.
            source_path: Project root path for cache identification.
        """
        start = time.time()
        self.documents = []
        self.inverted_index = {}
        self._source_path = source_path
        total_length = 0
        
        for doc_id, file in enumerate(files):
            tokens = self.tokenize(file.content)
            token_counts = Counter(tokens)
            
            self.documents.append({
                "file": file,
                "length": len(tokens),
                "tokens": token_counts,
            })
            
            total_length += len(tokens)
            
            # Build inverted index: word -> {doc_id: count}
            for token, count in token_counts.items():
                if token not in self.inverted_index:
                    self.inverted_index[token] = {}
                self.inverted_index[token][doc_id] = count
            
            # Free content from memory after indexing
            file.unload_content()
        
        self.doc_count = len(files)
        self.avg_doc_length = total_length / max(self.doc_count, 1)
        self._is_built = True
        self._build_time = time.time() - start
        
        logger.info(
            f"Index built: {self.doc_count} files, "
            f"{len(self.inverted_index)} unique terms, "
            f"{self._build_time:.2f}s"
        )
    
    def search(
        self, query: str, top_k: int = 5
    ) -> list[tuple[ProjectFile, float]]:
        """
        Search for files relevant to a query.
        
        Args:
            query: The search query.
            top_k: Number of results to return.
        
        Returns:
            List of (ProjectFile, score) tuples, sorted by relevance.
        """
        if not self._is_built or self.doc_count == 0:
            return []
        
        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []
        
        scores: list[float] = [0.0] * self.doc_count
        
        for token in query_tokens:
            if token not in self.inverted_index:
                continue
            
            posting_list = self.inverted_index[token]
            doc_freq = len(posting_list)
            
            # IDF: Rare words get higher weight
            idf = math.log(
                (self.doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0
            )
            
            for doc_id, term_freq in posting_list.items():
                doc_length = self.documents[doc_id]["length"]
                
                # BM25 formula
                numerator = term_freq * (self.k1 + 1)
                denominator = term_freq + self.k1 * (
                    1 - self.b + self.b * (doc_length / self.avg_doc_length)
                )
                scores[doc_id] += idf * (numerator / denominator)
        
        # Get top-k results
        scored = [
            (self.documents[i]["file"], scores[i])
            for i in range(self.doc_count)
            if scores[i] > 0
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return scored[:top_k]
    
    @property
    def stats(self) -> dict:
        """Return index statistics."""
        return {
            "documents": self.doc_count,
            "vocabulary": len(self.inverted_index),
            "avg_doc_length": round(self.avg_doc_length, 1),
            "build_time_seconds": round(self._build_time, 3),
            "source_path": self._source_path,
        }
    
    @property
    def is_built(self) -> bool:
        return self._is_built


# Module-level cache for built indexes
_index_cache: dict[str, BM25Search] = {}


def get_search_engine(project_path: str, force_rebuild: bool = False) -> BM25Search:
    """
    Get or create a cached search engine for a project.
    
    Builds the index once, returns cached version on subsequent calls.
    Call with force_rebuild=True if project files changed.
    """
    cache_key = str(Path(project_path).resolve())
    
    if not force_rebuild and cache_key in _index_cache:
        logger.debug(f"Using cached index for {cache_key}")
        return _index_cache[cache_key]
    
    logger.info(f"Building new index for {project_path}")
    files = scan_project(project_path, load_content=True)
    bm25 = BM25Search()
    bm25.build_index(files, source_path=cache_key)
    _index_cache[cache_key] = bm25
    
    return bm25


def invalidate_cache(project_path: str | None = None) -> None:
    """Clear search index cache."""
    global _index_cache
    if project_path:
        cache_key = str(Path(project_path).resolve())
        _index_cache.pop(cache_key, None)
        logger.info(f"Cache invalidated for {cache_key}")
    else:
        _index_cache.clear()
        logger.info("All caches invalidated")