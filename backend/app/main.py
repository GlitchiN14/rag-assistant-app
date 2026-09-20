"""FastAPI app: CORS, startup loading (lifespan), routes."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.query import router as query_router
from app.core.config import get_settings
from app.services.generation import Generator
from app.services.retrieval import Retriever
from app.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the vector store and the LLM client ONCE, not on every request."""
    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info("Starting %s", settings.app_name)
    app.state.retriever = Retriever(settings.vector_store_path)
    app.state.generator = Generator(settings)
    yield
    logger.info("Shutting down")


settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query_router)
