"""
Code completion API endpoint.
Provides inline code suggestions (Copilot-style ghost text).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.model_manager import ModelManager
from app.services.inference import chat, InferenceResult
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/complete", tags=["completion"])


class CompletionRequest(BaseModel):
    """Request for inline code completion."""
    prefix: str = Field(
        ...,
        min_length=1,
        max_length=50_000,
        description="Code before the cursor"
    )
    suffix: str = Field(
        default="",
        max_length=50_000,
        description="Code after the cursor"
    )
    language: str = Field(
        default="python",
        description="Programming language"
    )
    filepath: str = Field(
        default="",
        description="Current file path for context"
    )
    max_tokens: int = Field(
        default=64,
        ge=1,
        le=256,
        description="Max tokens to generate (keep short for completions)"
    )


class CompletionResponse(BaseModel):
    """Response with completion text."""
    completion: str
    tokens_generated: int
    tokens_per_second: float


def _get_manager() -> ModelManager:
    return ModelManager()


@router.post("", response_model=CompletionResponse)
async def complete(request: CompletionRequest):
    """
    Generate inline code completion.
    
    Uses fill-in-the-middle (FIM) style prompting:
    <prefix> is code before cursor, <suffix> is code after.
    Model generates what goes in between.
    """
    manager = _get_manager()
    
    if not manager.is_loaded():
        raise HTTPException(
            status_code=503,
            detail="No AI model loaded"
        )
    
    try:
        # Build fill-in-the-middle prompt
        prefix = request.prefix
        suffix = request.suffix
        
        # Trim prefix to last few lines for context
        prefix_lines = prefix.split("\n")
        if len(prefix_lines) > 50:
            prefix = "\n".join(prefix_lines[-50:])
        
        # Build prompt
        if suffix:
            prompt = (
                f"Complete the following {request.language} code. "
                f"Return ONLY the code that goes between the prefix and suffix. "
                f"Do not repeat the prefix or suffix.\n\n"
                f"<prefix>\n{prefix}\n</prefix>\n"
                f"<suffix>\n{suffix}\n</suffix>\n"
                f"<middle>"
            )
        else:
            prompt = (
                f"Complete the following {request.language} code. "
                f"Return ONLY the completion. Do not repeat the prefix.\n\n"
                f"```{request.language}\n{prefix}\n```\n"
                f"Completion:"
            )
        
        # Generate completion (low temperature for deterministic results)
        result = chat(
            message=prompt,
            max_tokens=request.max_tokens,
            temperature=0.1,  # Very low for completions
        )
        
        # Clean up response
        completion = result.text.strip()
        # Remove common artifacts
        completion = completion.replace("```", "").strip()
        
        return CompletionResponse(
            completion=completion,
            tokens_generated=result.tokens_generated,
            tokens_per_second=round(result.tokens_per_second, 1),
        )
        
    except Exception as e:
        logger.error(f"Completion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))