"""API tests. The retriever/generator are replaced with fakes, so these tests
need neither Ollama nor the vector store."""
import pytest
from fastapi.testclient import TestClient

from app.api.routes.query import get_generator, get_retriever
from app.main import app
from app.services.retrieval import Chunk


class FakeRetriever:
    count = 3

    def __init__(self, chunks=None):
        self.chunks = chunks if chunks is not None else [
            Chunk(text="The CSF has six functions.", source="nist_csf_2_0.pdf", page=5, distance=0.2)
        ]

    def retrieve(self, question, k=4, max_distance=None):
        return self.chunks


class FakeGenerator:
    def generate(self, question, chunks):
        return "The CSF has six functions [1].", ["nist_csf_2_0.pdf (page 5)"]


@pytest.fixture
def client():
    app.dependency_overrides[get_retriever] = lambda: FakeRetriever()
    app.dependency_overrides[get_generator] = lambda: FakeGenerator()
    yield TestClient(app)  # no `with` -> lifespan (real model loading) is skipped
    app.dependency_overrides.clear()


def test_query_happy_path(client):
    response = client.post("/query", json={"question": "What are the CSF core functions?"})
    assert response.status_code == 200
    body = response.json()
    assert "six functions" in body["answer"]
    assert body["sources"] == ["nist_csf_2_0.pdf (page 5)"]


def test_query_invalid_input_returns_422(client):
    assert client.post("/query", json={}).status_code == 422          # missing field
    assert client.post("/query", json={"question": "a"}).status_code == 422  # too short


def test_query_no_relevant_chunks_refuses_without_llm():
    app.dependency_overrides[get_retriever] = lambda: FakeRetriever(chunks=[])
    app.dependency_overrides[get_generator] = lambda: None  # must never be called
    try:
        response = TestClient(app).post("/query", json={"question": "Who won the World Cup?"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["sources"] == []
    assert "couldn't find" in response.json()["answer"]


def test_health(client):
    app.state.retriever = FakeRetriever()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
