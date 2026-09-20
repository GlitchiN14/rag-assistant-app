"""Load the persisted vector store and retrieve relevant chunks."""
import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    text: str
    source: str
    page: int
    distance: float  # cosine distance: lower = more similar


class Retriever:
    """Loads Chroma + the embedding model ONCE (at startup)."""

    def __init__(self, store_dir: Path):
        # Heavy imports are done here so unit tests can run without them.
        import chromadb
        from sentence_transformers import SentenceTransformer

        config_path = store_dir / "config.json"
        chroma_path = store_dir / "chroma"
        if not config_path.exists() or not chroma_path.exists():
            raise FileNotFoundError(
                f"Vector store not found in {store_dir}. Run notebooks/rag_pipeline.ipynb "
                "first (section 2.7 exports it into backend/data/vector_store/)."
            )

        self.config = json.loads(config_path.read_text(encoding="utf-8"))
        logger.info("Loading embedding model: %s", self.config["embedding_model"])
        self.embedder = SentenceTransformer(self.config["embedding_model"])

        client = chromadb.PersistentClient(path=str(chroma_path))
        self.collection = client.get_collection(self.config["collection_name"])
        logger.info("Vector store loaded: %d chunks", self.collection.count())

    @property
    def count(self) -> int:
        return self.collection.count()

    def retrieve(self, question: str, k: int = 4, max_distance: float | None = None) -> list[Chunk]:
        query_embedding = self.embedder.encode([question], normalize_embeddings=True).tolist()
        result = self.collection.query(
            query_embeddings=query_embedding,
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        chunks = [
            Chunk(text=doc, source=meta["source"], page=int(meta["page"]), distance=float(dist))
            for doc, meta, dist in zip(
                result["documents"][0], result["metadatas"][0], result["distances"][0]
            )
        ]
        if max_distance is not None:
            chunks = [c for c in chunks if c.distance <= max_distance]
        return chunks
