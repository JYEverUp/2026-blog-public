"""Optional SDK wiring; importing this file does not send model requests."""
from __future__ import annotations

import os
from typing import Any

from model_demo import ChatService, ModelFactory, ModelResolver, ModelSelection


def build_deepseek(selection: ModelSelection, api_key: str) -> Any:
    from langchain.chat_models import init_chat_model

    return init_chat_model(
        model=selection.model,
        model_provider="deepseek",
        api_key=api_key,
        api_base=selection.provider.base_url,
        timeout=30,
        max_retries=1,
    )


def build_openai_compatible(selection: ModelSelection, api_key: str) -> Any:
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=selection.model,
        base_url=selection.provider.base_url,
        api_key=api_key,
        use_responses_api=False,
        stream_usage=selection.provider.stream_usage,
        timeout=30,
        max_retries=1,
    )


def build_service(resolver: ModelResolver) -> ChatService:
    from deepagents import create_deep_agent

    factory = ModelFactory(
        builders={
            "deepseek": build_deepseek,
            "openai-compatible": build_openai_compatible,
        },
        read_secret=os.environ.__getitem__,
    )
    return ChatService(
        resolver=resolver,
        factory=factory,
        build_agent=lambda model: create_deep_agent(model=model),
    )
