"""AWS Bedrock runtime client. Credentials stay in the environment."""

from __future__ import annotations

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import Settings
from app.core.errors import AppError


def bedrock_runtime_client(settings: Settings):
    kwargs: dict[str, str] = {"region_name": settings.aws_region}
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    return boto3.client("bedrock-runtime", **kwargs)


def bedrock_error_message(exc: Exception) -> str:
    if isinstance(exc, ClientError):
        detail = exc.response.get("Error", {}).get("Message")
        if isinstance(detail, str) and detail.strip():
            return f"AWS Bedrock request failed: {detail.strip()}"
    if isinstance(exc, (ClientError, BotoCoreError)):
        return "AWS Bedrock request failed."
    return "The model request failed."


def raise_bedrock(exc: Exception) -> None:
    raise AppError(bedrock_error_message(exc), 502) from exc
