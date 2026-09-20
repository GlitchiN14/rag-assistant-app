"""Request / response models for the API."""
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="The question to ask about the indexed documents.",
        examples=["What are the core functions of the NIST Cybersecurity Framework?"],
    )


class QueryResponse(BaseModel):
    answer: str
    sources: list[str] = Field(
        default_factory=list,
        description='Cited sources, e.g. "nist_csf_2_0.pdf (page 5)".',
    )
