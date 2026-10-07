"""Grounded answers from Amazon Bedrock."""

from app.core.bedrock import raise_bedrock
from app.core.config import Settings
from app.core.errors import AppError
from app.services.generation.prompt import SYSTEM_PROMPT, build_user_prompt
from app.services.retrieval.types import RetrievedChunk


class BedrockGenerator:
    def __init__(self, client, settings: Settings) -> None:
        self._client = client
        self._model_id = settings.bedrock_chat_model

    def generate(
        self,
        *,
        query: str,
        chunks: list[RetrievedChunk],
        history: list[tuple[str, str]],
    ) -> str:
        user_prompt = build_user_prompt(query, chunks, history)
        try:
            response = self._client.converse(
                modelId=self._model_id,
                system=[{"text": SYSTEM_PROMPT}],
                messages=[{"role": "user", "content": [{"text": user_prompt}]}],
                inferenceConfig={"maxTokens": 1200, "temperature": 0.2},
            )
        except AppError:
            raise
        except Exception as exc:
            raise_bedrock(exc)
        text = _response_text(response)
        if not text:
            raise AppError("The model returned an empty answer.", 502)
        return text


def _response_text(response: dict) -> str:
    content = response.get("output", {}).get("message", {}).get("content", [])
    parts = [block.get("text", "") for block in content if isinstance(block, dict)]
    return "\n".join(part.strip() for part in parts if part and part.strip()).strip()
