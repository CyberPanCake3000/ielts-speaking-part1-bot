import json
import logging

import anthropic

from app.config import settings
from app.models import Evaluation, TopicResponse

logger = logging.getLogger(__name__)


class ClaudeService:
    def __init__(self) -> None:
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def generate_part1_topic(self, previous_topics: list[str]) -> TopicResponse:
        previous = ", ".join(previous_topics[-30:]) or "none"

        prompt = f"""
You are an experienced IELTS Speaking examiner.

Generate ONE fresh IELTS Speaking Part 1 question.
The question must be natural, conversational, and suitable for Part 1.
Avoid repeating these recently used topics: {previous}.

Return ONLY valid JSON:
{{
  "topic": "short topic name",
  "question": "the exact question"
}}
"""

        response = await self.client.messages.create(
            model=settings.claude_model,
            max_tokens=1024,
            system="You generate realistic IELTS Speaking Part 1 questions.",
            messages=[{"role": "user", "content": prompt}],
        )

        raw = _extract_text(response)
        return TopicResponse.model_validate(_parse_json(raw))

    async def evaluate(
        self,
        topic: str,
        question: str,
        transcript: str,
    ) -> Evaluation:
        prompt = f"""
You are an IELTS Speaking examiner.

Evaluate the candidate's answer to this IELTS Speaking Part 1 question.

Topic: {topic}
Question: {question}

Candidate transcript:
{transcript}

Important:
- Be fair and realistic.
- Do not penalize harmless transcription artifacts.
- ALL score fields (overall_score, fluency_coherence, lexical_resource,
  grammatical_accuracy, pronunciation) MUST be numbers only, e.g. 6.0, 6.5, 7.0.
  Never put text, explanations, or notes in score fields.
- Pronunciation cannot be perfectly judged from transcript alone. Always give a
  numeric pronunciation score (use a conservative estimate if needed). If audio
  is unavailable or evidence is limited, mention that limitation in "verdict",
  not in the pronunciation field.
- Keep the user-facing feedback concise, friendly and useful.
- Corrections must quote short fragments from the transcript and provide a natural correction.
- The Band 7 example must answer the actual question, not discuss the evaluation.

Return ONLY valid JSON:
{{
  "overall_score": 0.0,
  "fluency_coherence": 0.0,
  "lexical_resource": 0.0,
  "grammatical_accuracy": 0.0,
  "pronunciation": 0.0,
  "good_points": ["...", "..."],
  "corrections": [
    {{"original": "...", "correction": "...", "why": "..."}}
  ],
  "improvements": ["...", "..."],
  "band_7_example": "...",
  "verdict": "2-4 friendly sentences with the key takeaway."
}}

Use IELTS-style half-band scores where appropriate, e.g. 6.0, 6.5, 7.0.
"""

        response = await self.client.messages.create(
            model=settings.claude_model,
            max_tokens=4096,
            system=(
                "You are a strict but supportive IELTS Speaking examiner. "
                "Return valid JSON only. All score fields must be numbers, never text."
            ),
            messages=[{"role": "user", "content": prompt}],
        )

        raw = _extract_text(response)
        return Evaluation.model_validate(_parse_json(raw))


def _extract_text(response) -> str:
    for block in response.content:
        if block.type == "text" and block.text.strip():
            return block.text.strip()
    raise ValueError("Claude returned no text block")


def _parse_json(raw: str):
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]
    return json.loads(raw.strip())