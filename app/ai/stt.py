from pathlib import Path

from openai import AsyncOpenAI

from app.config import settings


class SpeechToTextService:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def transcribe(self, audio_path: Path) -> str:
        with audio_path.open("rb") as audio:
            result = await self.client.audio.transcriptions.create(
                model=settings.stt_model,
                file=audio,
                language="en",
            )
        return result.text.strip()
