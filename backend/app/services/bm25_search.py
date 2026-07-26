"""
BM25 search engine for finding relevant project files.
Builds an index from file contents and searches with TF-IDF scoring.
"""

import math
import re
from collections import Counter
from .project_scanner import ProjectFile


class BM25Search:
    """
    BM25 (Best Match 25) search implementation.
    Ranks documents by relevance to a search query.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Args:
            k1: Controls term frequency saturation (default 1.5).
            b: Controls document length normalization (default 0.75).
        """
        self.k1 = k1
        self.b = b
        self.documents: list[dict] = []
        self.doc_count: int = 0
        self.avg_doc_length: float = 0
        self.inverted_index: dict[str, dict[int, int]] = {}
        self._is_built = False

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """
        Splits text into tokens (words).
        Lowercases, splits on non-alphanumeric, filters short tokens.
        """
        text = text.lower()
        tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", text)
        return [t for t in tokens if len(t) >= 2]

    def build_index(self, files: list[ProjectFile]) -> None:
        """
        Builds the BM25 search index from a list of project files.

        Args:
            files: List of ProjectFile objects to index.
        """
        self.documents = []
        self.inverted_index = {}
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

            # Build inverted index: token -> {doc_id -> count}
            for token, count in token_counts.items():
                if token not in self.inverted_index:
                    self.inverted_index[token] = {}
                self.inverted_index[token][doc_id] = count

        self.doc_count = len(files)
        self.avg_doc_length = total_length / max(self.doc_count, 1)
        self._is_built = True

    def search(
        self, query: str, top_k: int = 5
    ) -> list[tuple[ProjectFile, float]]:
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

            # IDF (Inverse Document Frequency)
            idf = math.log(
                (self.doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0
            )

            for doc_id, term_freq in posting_list.items():
                doc_length = self.documents[doc_id]["length"]

                # BM25 scoring formula
                numerator = term_freq * (self.k1 + 1)
                denominator = term_freq + self.k1 * (
                    1 - self.b + self.b * (doc_length / self.avg_doc_length)
                )
                scores[doc_id] += idf * (numerator / denominator)

        # Get top-k results
        scored_docs = [
            (self.documents[i]["file"], scores[i])
            for i in range(self.doc_count)
            if scores[i] > 0
        ]
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return scored_docs[:top_k]