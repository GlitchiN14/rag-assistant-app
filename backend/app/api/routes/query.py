"""GET /health and POST /query."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.config import Settings, get_settings
from app.schemas.query import QueryRequest, QueryResponse
from app.services.generation import REFUSAL, GenerationError

logger = logging.getLogger(__name__)
router = APIRouter()


def get_retriever(request: Request):
    return request.app.state.retriever


def get_generator(request: Request):
    return request.app.state.generator


@router.get("/health")
def health(request: Request):
    retriever = getattr(request.app.state, "retriever", None)
    return {
        "status": "ok",
        "vector_store_loaded": retriever is not None,
        "chunks": retriever.count if retriever is not None else 0,
    }


# Plain `def` (not async): the retrieval + Ollama calls are blocking, so FastAPI
# runs this in a worker thread and the server stays responsive.
@router.post("/query", response_model=QueryResponse)
def query(
    payload: QueryRequest,
    retriever=Depends(get_retriever),
    generator=Depends(get_generator),
    settings: Settings = Depends(get_settings),
):
    question = payload.question.strip()
    logger.info("Question: %s", question)

    # Retrieve the top-k chunks (nearest first). Gate on the BEST chunk only: if even the
    # closest passage is farther than MAX_DISTANCE, nothing relevant exists -> refuse without
    # calling the LLM. Otherwise ALL top-k chunks are used as context (filtering the weaker
    # chunks too would starve list-style questions of context).
    chunks = retriever.retrieve(question, k=settings.top_k)
    if not chunks or chunks[0].distance > settings.max_distance:
        return QueryResponse(answer=REFUSAL, sources=[])

    try:
        answer, sources = generator.generate(question, chunks)
    except GenerationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return QueryResponse(answer=answer, sources=sources)
