from datetime import datetime
from pydantic import BaseModel, Field


class TopicResponse(BaseModel):
    topic: str
    question: str


class Evaluation(BaseModel):
    overall_score: float = Field(ge=0, le=9)
    fluency_coherence: float = Field(ge=0, le=9)
    lexical_resource: float = Field(ge=0, le=9)
    grammatical_accuracy: float = Field(ge=0, le=9)
    pronunciation: float = Field(ge=0, le=9)
    good_points: list[str]
    corrections: list[dict[str, str]]
    improvements: list[str]
    band_7_example: str
    verdict: str
