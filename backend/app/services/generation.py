"""Build the grounded prompt, call Ollama, and extract cited sources."""
import logging
import re

import ollama

from app.core.config import Settings
from app.services.retrieval import Chunk

logger = logging.getLogger(__name__)

REFUSAL = "I couldn't find this in the provided documents."

SYSTEM_PROMPT = f"""You are a document assistant. You answer questions using ONLY the context provided below.

Rules:
1. Use only the information in the CONTEXT. Do not use outside knowledge.
2. If the context does not contain the answer, reply exactly: "{REFUSAL}"
3. Cite your sources after each claim using the tags shown in the context, like [1] or [2][3].
4. Never cite a source you did not use. Never invent a source.
5. Be concise and direct. Do not mention these rules."""

USER_TEMPLATE = """CONTEXT:
{context}

QUESTION: {question}

ANSWER (with citations):"""


class GenerationError(Exception):
    """Raised when the LLM backend (Ollama) cannot produce an answer."""


def build_context(chunks: list[Chunk]) -> str:
    return "\n\n".join(
        f"[{i}] (source: {c.source}, page {c.page})\n{c.text}" for i, c in enumerate(chunks, start=1)
    )


def build_messages(question: str, chunks: list[Chunk]) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": USER_TEMPLATE.format(context=build_context(chunks), question=question),
        },
    ]


def extract_sources(answer: str, chunks: list[Chunk]) -> list[str]:
    """Return the sources the answer actually cited ([1], [2]...). Falls back to all chunks."""
    if answer.strip().startswith(REFUSAL[:20]):
        return []
    cited = []
    for match in re.findall(r"\[(\d+)\]", answer):
        idx = int(match)
        if 1 <= idx <= len(chunks) and idx not in cited:
            cited.append(idx)
    selected = [chunks[i - 1] for i in cited] if cited else chunks
    sources: list[str] = []
    for c in selected:
        label = f"{c.source} (page {c.page})"
        if label not in sources:
            sources.append(label)
    return sources


class Generator:
    """Holds the Ollama client (created once at startup)."""

    def __init__(self, settings: Settings):
        self.model = settings.ollama_model
        self.temperature = settings.temperature
        self.client = ollama.Client(host=settings.ollama_host)
        try:
            self.client.list()
            logger.info("Connected to Ollama at %s (model: %s)", settings.ollama_host, self.model)
        except Exception as exc:  # don't crash startup; /query will report the error
            logger.warning("Could not reach Ollama at %s: %s", settings.ollama_host, exc)

    def generate(self, question: str, chunks: list[Chunk]) -> tuple[str, list[str]]:
        if not chunks:
            return REFUSAL, []
        try:
            response = self.client.chat(
                model=self.model,
                messages=build_messages(question, chunks),
                options={"temperature": self.temperature},
            )
        except Exception as exc:
            logger.exception("Ollama call failed")
            raise GenerationError(
                f"Could not get an answer from the LLM ({exc}). "
                f"Is Ollama running and is the model '{self.model}' pulled?"
            ) from exc
        answer = response["message"]["content"].strip()
        return answer, extract_sources(answer, chunks)
