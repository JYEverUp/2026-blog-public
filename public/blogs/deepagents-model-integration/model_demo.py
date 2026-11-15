"""Python 3.12+; offline demo, no SDK, credentials, or model calls required."""
from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class Provider:
    id: str
    owner_id: str | None  # None means platform-shared in this example.
    adapter: str
    base_url: str
    secret_ref: str
    models: tuple[str, ...]
    enabled: bool = True
    stream_usage: bool = False


@dataclass(frozen=True)
class AgentConfig:
    id: str
    owner_id: str
    provider_id: str
    model: str


@dataclass(frozen=True)
class ModelSelection:
    provider: Provider
    model: str


class ModelResolver:
    def __init__(
        self,
        providers: Mapping[str, Provider],
        agents: Mapping[str, AgentConfig],
    ) -> None:
        self.providers = providers
        self.agents = agents

    def resolve(
        self, *, user_id: str, agent_id: str, model: str | None = None
    ) -> ModelSelection:
        agent = self.agents[agent_id]
        if agent.owner_id != user_id:
            raise PermissionError("agent is not owned by current user")

        provider = self.providers[agent.provider_id]
        if provider.owner_id not in (None, user_id):
            raise PermissionError("provider is not visible to current user")
        if not provider.enabled:
            raise ValueError("provider is disabled")

        selected = model if model is not None else agent.model
        if selected not in provider.models:
            raise ValueError("model is not enabled for this provider")
        return ModelSelection(provider=provider, model=selected)


ModelBuilder = Callable[[ModelSelection, str], Any]


class ModelFactory:
    def __init__(
        self,
        builders: Mapping[str, ModelBuilder],
        read_secret: Callable[[str], str],
    ) -> None:
        self.builders = builders
        self.read_secret = read_secret

    def create(self, selection: ModelSelection) -> Any:
        builder = self.builders[selection.provider.adapter]
        api_key = self.read_secret(selection.provider.secret_ref)
        return builder(selection, api_key)


class AgentRuntime(Protocol):
    async def ainvoke(self, state: dict[str, Any]) -> dict[str, Any]: ...


class ChatService:
    def __init__(
        self,
        resolver: ModelResolver,
        factory: ModelFactory,
        build_agent: Callable[[Any], AgentRuntime],
    ) -> None:
        self.resolver = resolver
        self.factory = factory
        self.build_agent = build_agent

    async def ask(self, *, user_id: str, agent_id: str, text: str) -> Any:
        selection = self.resolver.resolve(user_id=user_id, agent_id=agent_id)
        model = self.factory.create(selection)
        agent = self.build_agent(model)
        return await agent.ainvoke({
            "messages": [{"role": "user", "content": text}]
        })


@dataclass(frozen=True)
class FakeModel:
    provider_id: str
    model: str


class FakeAgent:
    def __init__(self, model: FakeModel) -> None:
        self.model = model

    async def ainvoke(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "selected": f"{self.model.provider_id}/{self.model.model}",
            "input": state["messages"][-1]["content"],
        }


async def main() -> None:
    # All addresses, model names, and secret values here are offline fixtures.
    providers = {
        "alice-deepseek": Provider(
            "alice-deepseek", "alice", "deepseek", "https://example.invalid/v1",
            "ALICE_MODEL_KEY", ("reasoning-model",),
        ),
        "team-qwen": Provider(
            "team-qwen", None, "openai-compatible", "https://example.invalid/v1",
            "TEAM_MODEL_KEY", ("chat-model",),
        ),
    }
    agents = {
        "alice-assistant": AgentConfig(
            "alice-assistant", "alice", "alice-deepseek", "reasoning-model"
        ),
        "bob-assistant": AgentConfig(
            "bob-assistant", "bob", "team-qwen", "chat-model"
        ),
        "bob-invalid-binding": AgentConfig(
            "bob-invalid-binding", "bob", "alice-deepseek", "reasoning-model"
        ),
    }
    secrets = {
        "ALICE_MODEL_KEY": "offline-placeholder-a",
        "TEAM_MODEL_KEY": "offline-placeholder-b",
    }
    created: list[str] = []

    def fake_builder(selection: ModelSelection, api_key: str) -> FakeModel:
        assert api_key.startswith("offline-placeholder-")
        created.append(selection.provider.id)
        return FakeModel(selection.provider.id, selection.model)

    resolver = ModelResolver(providers, agents)
    factory = ModelFactory(
        {"deepseek": fake_builder, "openai-compatible": fake_builder},
        secrets.__getitem__,
    )
    service = ChatService(resolver, factory, FakeAgent)

    alice = await service.ask(
        user_id="alice", agent_id="alice-assistant", text="分析设备告警"
    )
    bob = await service.ask(
        user_id="bob", agent_id="bob-assistant", text="整理交接班记录"
    )
    assert alice["selected"] == "alice-deepseek/reasoning-model"
    assert bob["selected"] == "team-qwen/chat-model"
    print("PASS: Alice and Bob resolve different configured models")

    for agent_id in ("alice-assistant", "bob-invalid-binding"):
        try:
            await service.ask(user_id="bob", agent_id=agent_id, text="hello")
        except PermissionError:
            pass
        else:
            raise AssertionError("unauthorized selection was accepted")
    assert len(created) == 2  # Denied requests never reach model construction.
    print("PASS: foreign agents and private providers are rejected before build")

    try:
        resolver.resolve(
            user_id="alice", agent_id="alice-assistant", model="not-enabled"
        )
    except ValueError:
        print("PASS: models outside the enabled list are rejected")
    else:
        raise AssertionError("unknown model was accepted")


if __name__ == "__main__":
    asyncio.run(main())
