"""
BM25 search engine for finding relevant project files.
Supports index caching — build once, reuse across requests.
"""

import math
import re
import time
from collections import Counter
from pathlib import Path
from .project_scanner import ProjectFile, scan_project


class BM25Search:
    """
    BM25 (Best Match 25) search implementation.
    Ranks documents by relevance to a search query.
    Supports caching the index for performance.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: list[dict] = []
        self.doc_count: int = 0
        self.avg_doc_length: float = 0
        self.inverted_index: dict[str, dict[int, int]] = {}
        self._is_built = False
        self._build_time: float = 0
        self._source_path: str = ""

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """Splits text into tokens (words)."""
        text = text.lower()
        tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", text)
        return [t for t in tokens if len(t) >= 2]

    def build_index(self, files: list[ProjectFile], source_path: str = "") -> None:
        """
        Builds the BM25 search index from a list of project files.
        
        Args:
            files: List of ProjectFile objects to index.
            source_path: Path to the project (for cache identification).
        """
        start_time = time.time()
        
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

            for token, count in token_counts.items():
                if token not in self.inverted_index:
                    self.inverted_index[token] = {}
                self.inverted_index[token][doc_id] = count

        self.doc_count = len(files)
        self.avg_doc_length = total_length / max(self.doc_count, 1)
        self._is_built = True
        self._build_time = time.time() - start_time

    def search(self, query: str, top_k: int = 5) -> list[tuple[ProjectFile, float]]:
        """
        Searches for files relevant to the query.
        
        Args:
            query: The search query string.
            top_k: Number of top results to return.
            
        Returns:
            List of (ProjectFile, score) tuples, sorted by score descending.
        """
        if not self._is_built or self.doc_count == 0:
            return []

        query_tokens = self.tokenize(query)
        scores: list[float] = [0.0] * self.doc_count

        for token in query_tokens:
            if token not in self.inverted_index:
                continue

            posting_list = self.inverted_index[token]
            doc_freq = len(posting_list)

            idf = math.log(
                (self.doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0
            )

            for doc_id, term_freq in posting_list.items():
                doc_length = self.documents[doc_id]["length"]

                numerator = term_freq * (self.k1 + 1)
                denominator = term_freq + self.k1 * (
                    1 - self.b + self.b * (doc_length / self.avg_doc_length)
                )
                scores[doc_id] += idf * (numerator / denominator)

        scored_docs = [
            (self.documents[i]["file"], scores[i])
            for i in range(self.doc_count)
            if scores[i] > 0
        ]
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return scored_docs[:top_k]

    @property
    def stats(self) -> dict:
        """Returns statistics about the current index."""
        return {
            "documents": self.doc_count,
            "vocabulary": len(self.inverted_index),
            "avg_doc_length": round(self.avg_doc_length, 1),
            "build_time_seconds": round(self._build_time, 3),
            "source_path": self._source_path,
        }


# Module-level cache
_index_cache: dict[str, BM25Search] = {}


def get_search_engine(project_path: str, force_rebuild: bool = False) -> BM25Search:
    """
    Get or create a cached BM25 search engine for a project.
    
    Args:
        project_path: Path to the project root.
        force_rebuild: If True, rebuild the index even if cached.
        
    Returns:
        A BM25Search instance with built index.
    """
    cache_key = str(Path(project_path).resolve())

    if not force_rebuild and cache_key in _index_cache:
        return _index_cache[cache_key]

    files = scan_project(project_path)
    bm25 = BM25Search()
    bm25.build_index(files, source_path=cache_key)
    _index_cache[cache_key] = bm25

    return bm25


def invalidate_cache(project_path: str | None = None) -> None:
    """
    Invalidate the search index cache.
    
    Args:
        project_path: If provided, only invalidate this project.
                      If None, invalidate all caches.
    """
    global _index_cache
    if project_path:
        cache_key = str(Path(project_path).resolve())
        _index_cache.pop(cache_key, None)
    else:
        _index_cache.clear()