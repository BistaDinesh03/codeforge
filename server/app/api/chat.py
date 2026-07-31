"""
Chat API endpoint - the main AI interaction point.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.model_manager import ModelManager
from app.services.inference import chat, generate_code, explain_code
from app.services.context_builder import build_context
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=100_000)
    max_tokens: int = Field(default=2048, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    include_context: bool = Field(default=False)
    project_path: str | None = Field(default=None)


class ChatResponse(BaseModel):
    response: str
    tokens_generated: int
    tokens_per_second: float
    model_used: str


class ExplainRequest(BaseModel):
    code: str = Field(..., min_length=1)
    language: str = Field(default="python")


class GenerateRequest(BaseModel):
    description: str = Field(..., min_length=1)
    language: str = Field(default="python")


class RewriteRequest(BaseModel):
    code: str = Field(..., min_length=1)
    language: str = Field(default="python")


def _get_manager() -> ModelManager:
    return ModelManager()


@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    manager = _get_manager()
    
    if not manager.is_loaded():
        raise HTTPException(status_code=503, detail="No AI model loaded")
    
    try:
        message = request.message
        
        if request.include_context and request.project_path:
            try:
                context = build_context(query=message, project_path=request.project_path, max_files=3)
                if context.context_text:
                    message = f"Here are relevant files:\n\n{context.context_text}\n\nUser: {request.message}"
            except Exception as e:
                logger.warning(f"Context failed: {e}")
        
        result = chat(message=message, max_tokens=request.max_tokens, temperature=request.temperature)
        
        return ChatResponse(
            response=result.text,
            tokens_generated=result.tokens_generated,
            tokens_per_second=round(result.tokens_per_second, 1),
            model_used=manager.current_model_name,
        )
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain", response_model=ChatResponse)
async def explain_endpoint(request: ExplainRequest):
    manager = _get_manager()
    if not manager.is_loaded():
        raise HTTPException(status_code=503, detail="No AI model loaded")
    try:
        result = explain_code(code=request.code, language=request.language)
        return ChatResponse(
            response=result.text,
            tokens_generated=result.tokens_generated,
            tokens_per_second=round(result.tokens_per_second, 1),
            model_used=manager.current_model_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=ChatResponse)
async def generate_endpoint(request: GenerateRequest):
    manager = _get_manager()
    if not manager.is_loaded():
        raise HTTPException(status_code=503, detail="No AI model loaded")
    try:
        result = generate_code(description=request.description, language=request.language)
        return ChatResponse(
            response=result.text,
            tokens_generated=result.tokens_generated,
            tokens_per_second=round(result.tokens_per_second, 1),
            model_used=manager.current_model_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rewrite", response_model=ChatResponse)
async def rewrite_endpoint(request: RewriteRequest):
    manager = _get_manager()
    if not manager.is_loaded():
        raise HTTPException(status_code=503, detail="No AI model loaded")
    try:
        prompt = f"Rewrite this {request.language} code to be cleaner. Return ONLY code:\n\n```{request.language}\n{request.code}\n```"
        result = chat(message=prompt, temperature=0.3)
        return ChatResponse(
            response=result.text,
            tokens_generated=result.tokens_generated,
            tokens_per_second=round(result.tokens_per_second, 1),
            model_used=manager.current_model_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))