"""
Context Builder - finds relevant files and builds prompts with project context.
Makes the AI aware of your actual codebase.
"""

from pathlib import Path

from app.services.project_scanner import scan_project, ProjectFile
from app.services.bm25_search import get_search_engine, BM25Search
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Maximum context size in characters (to fit in model's context window)
MAX_CONTEXT_CHARS = 8000
# Maximum number of files to include
MAX_CONTEXT_FILES = 5
# Maximum chars per file in context
MAX_CHARS_PER_FILE = 2000


class ContextResult:
    """Result of a context search."""
    
    def __init__(
        self,
        query: str,
        files: list[tuple[ProjectFile, float]],
        context_text: str,
        total_files_scanned: int,
    ):
        self.query = query
        self.files = files
        self.context_text = context_text
        self.total_files_scanned = total_files_scanned
    
    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "files_found": len(self.files),
            "total_files_scanned": self.total_files_scanned,
            "context_size_chars": len(self.context_text),
            "files": [
                {
                    "path": f.relative_path,
                    "score": round(score, 2),
                    "language": f.extension.lstrip("."),
                }
                for f, score in self.files
            ],
        }


def build_context(
    query: str,
    project_path: str,
    max_files: int = MAX_CONTEXT_FILES,
    max_chars: int = MAX_CONTEXT_CHARS,
) -> ContextResult:
    """
    Find relevant files and build a context string for the AI.
    
    Args:
        query: The user's question or request.
        project_path: Path to the project root.
        max_files: Maximum number of files to include.
        max_chars: Maximum total context size in characters.
    
    Returns:
        ContextResult with found files and formatted context text.
    """
    # Get or build search index
    engine = get_search_engine(project_path)
    
    # Search for relevant files
    results = engine.search(query, top_k=max_files)
    
    if not results:
        logger.info(f"No relevant files found for: '{query[:50]}...'")
        return ContextResult(
            query=query,
            files=[],
            context_text="",
            total_files_scanned=engine.doc_count,
        )
    
    # Build context text from top files
    context_parts = []
    total_chars = 0
    
    for file, score in results:
        content = file.content
        
        # Trim file content if needed
        if len(content) > MAX_CHARS_PER_FILE:
            content = content[:MAX_CHARS_PER_FILE] + "\n... (truncated)"
        
        # Format as code block with file path
        ext = file.extension.lstrip(".") or "text"
        file_context = (
            f"### {file.relative_path} (relevance: {score:.1%})\n"
            f"```{ext}\n{content}\n```\n"
        )
        
        # Check if adding this file would exceed max context
        if total_chars + len(file_context) > max_chars:
            break
        
        context_parts.append(file_context)
        total_chars += len(file_context)
        
        # Free content from memory
        file.unload_content()
    
    context_text = "\n".join(context_parts)
    
    logger.info(
        f"Context built: {len(results)} files found, "
        f"{len(context_parts)} included ({total_chars} chars)"
    )
    
    return ContextResult(
        query=query,
        files=results[:len(context_parts)],
        context_text=context_text,
        total_files_scanned=engine.doc_count,
    )


def build_chat_prompt_with_context(
    query: str,
    project_path: str,
    system_prompt: str | None = None,
) -> str:
    """
    Build a complete prompt that includes project context.
    
    Args:
        query: User's question.
        project_path: Path to project root.
        system_prompt: Optional system instruction.
    
    Returns:
        Formatted prompt string ready for the AI.
    """
    context = build_context(query, project_path)
    
    parts = []
    
    if system_prompt:
        parts.append(f"System: {system_prompt}\n")
    
    if context.context_text:
        parts.append(
            "Here are the most relevant files from the project:\n\n"
            f"{context.context_text}\n"
        )
    
    parts.append(f"User: {query}")
    
    return "\n".join(parts)