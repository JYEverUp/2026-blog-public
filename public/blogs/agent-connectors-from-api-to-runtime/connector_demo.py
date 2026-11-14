"""Offline connector example. Python 3.12+, standard library only.

Run: python connector_demo.py
Test: python connector_demo.py --test
The fake adapter never makes network requests. All identities and tokens are fake.
"""

from __future__ import annotations

import json
import sys
import unittest
from collections.abc import Callable
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class RequestContext:
    tenant_id: str
    user_id: str
    selected_connections: frozenset[str]


@dataclass(frozen=True)
class ConnectionInstance:
    id: str
    tenant_id: str
    kind: str
    base_url: str
    credential_ref: str
    enabled: bool = True


class FakeCRMAdapter:
    """Stand-in for an API client; supports account and token isolation checks."""

    def __init__(self) -> None:
        self.calls = 0
        self.accounts = {
            ("https://crm-a.example.invalid", "demo-token-a"): "远山公司",
            ("https://crm-a.example.invalid", "demo-token-a-v2"): "远山公司",
            ("https://crm-b.example.invalid", "demo-token-b"): "星河公司",
        }

    def search(
        self, instance: ConnectionInstance, token: str, query: str, limit: int
    ) -> list[dict[str, str]]:
        self.calls += 1
        account = self.accounts.get((instance.base_url, token))
        if account is None:
            raise PermissionError("External credential is invalid")
        rows = [{"id": f"{instance.id}-customer-1", "name": account, "status": "active"}]
        return [row for row in rows if query in row["name"]][:limit]


class ConnectorService:
    def __init__(self) -> None:
        self.connections: dict[str, ConnectionInstance] = {}
        self.grants: set[tuple[str, str, str, str]] = set()
        self.secrets: dict[str, str] = {}
        self.adapters = {"crm": FakeCRMAdapter()}

    def authorize(
        self, ctx: RequestContext, connection_id: str, action: str
    ) -> ConnectionInstance:
        instance = self.connections[connection_id]
        grant = (ctx.tenant_id, ctx.user_id, connection_id, action)
        if (
            not instance.enabled
            or instance.tenant_id != ctx.tenant_id
            or connection_id not in ctx.selected_connections
            or grant not in self.grants
        ):
            raise PermissionError("Connection or operation is not allowed")
        return instance

    def search(
        self, ctx: RequestContext, connection_id: str, query: str, limit: int = 10
    ) -> list[dict[str, str]]:
        if not isinstance(query, str) or not 1 <= len(query.strip()) <= 100:
            raise ValueError("query must contain 1..100 non-blank characters")
        if type(limit) is not int or not 1 <= limit <= 20:
            raise ValueError("limit must be an integer in 1..20")
        instance = self.authorize(ctx, connection_id, "customers:read")
        token = self.secrets[instance.credential_ref]
        adapter = self.adapters[instance.kind]
        return adapter.search(instance, token, query.strip(), limit)


def bind_search(
    service: ConnectorService, ctx: RequestContext, connection_id: str
) -> Callable[..., list[dict[str, str]]]:
    """Bind one immutable request context; recheck live grants on every call."""
    service.authorize(ctx, connection_id, "customers:read")

    def search_customers(query: str, limit: int = 10) -> list[dict[str, str]]:
        """按客户名称查询当前已授权 CRM，最多返回 20 条客户摘要。"""
        return service.search(ctx, connection_id, query, limit)

    return search_customers


def make_demo() -> tuple[ConnectorService, RequestContext]:
    service = ConnectorService()
    for suffix in ("a", "b"):
        connection_id = f"crm-{suffix}"
        service.connections[connection_id] = ConnectionInstance(
            id=connection_id,
            tenant_id=f"tenant-{suffix}",
            kind="crm",
            base_url=f"https://crm-{suffix}.example.invalid",
            credential_ref=f"secret-{suffix}",
        )
        service.secrets[f"secret-{suffix}"] = f"demo-token-{suffix}"
        service.grants.add(
            (f"tenant-{suffix}", f"user-{suffix}", connection_id, "customers:read")
        )
    return service, RequestContext("tenant-a", "user-a", frozenset({"crm-a"}))


class ConnectorChecks(unittest.TestCase):
    def setUp(self) -> None:
        self.service, self.ctx = make_demo()
        self.tool = bind_search(self.service, self.ctx, "crm-a")

    def test_authorized_search(self) -> None:
        rows = self.tool(query="远山", limit=5)
        self.assertEqual(rows, [{"id": "crm-a-customer-1", "name": "远山公司", "status": "active"}])

    def test_other_tenant_is_rejected_before_external_call(self) -> None:
        ctx = replace(self.ctx, selected_connections=frozenset({"crm-b"}))
        self.service.grants.add((ctx.tenant_id, ctx.user_id, "crm-b", "customers:read"))
        with self.assertRaises(PermissionError):
            self.service.search(ctx, "crm-b", "星河")
        self.assertEqual(self.service.adapters["crm"].calls, 0)

    def test_other_user_is_rejected(self) -> None:
        with self.assertRaises(PermissionError):
            self.service.search(replace(self.ctx, user_id="other-user"), "crm-a", "远山")

    def test_unselected_connection_is_rejected(self) -> None:
        with self.assertRaises(PermissionError):
            self.service.search(replace(self.ctx, selected_connections=frozenset()), "crm-a", "远山")

    def test_revocation_after_tool_binding(self) -> None:
        self.service.grants.clear()
        with self.assertRaises(PermissionError):
            self.tool(query="远山")
        self.assertEqual(self.service.adapters["crm"].calls, 0)

    def test_disabled_connection_after_tool_binding(self) -> None:
        self.service.connections["crm-a"] = replace(self.service.connections["crm-a"], enabled=False)
        with self.assertRaises(PermissionError):
            self.tool(query="远山")

    def test_credentials_are_read_at_call_time(self) -> None:
        self.service.secrets["secret-a"] = "demo-token-a-v2"
        self.assertEqual(self.tool(query="远山")[0]["name"], "远山公司")

    def test_bound_contexts_do_not_overwrite_each_other(self) -> None:
        ctx_b = RequestContext("tenant-b", "user-b", frozenset({"crm-b"}))
        tool_b = bind_search(self.service, ctx_b, "crm-b")
        self.assertEqual(tool_b(query="星河")[0]["name"], "星河公司")
        self.assertEqual(self.tool(query="远山")[0]["name"], "远山公司")

    def test_invalid_arguments(self) -> None:
        for arguments in ({"query": " "}, {"query": "远山", "limit": 21}, {"query": "远山", "limit": True}):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                self.tool(**arguments)
        self.assertEqual(self.service.adapters["crm"].calls, 0)

    def test_model_cannot_choose_identity_or_account(self) -> None:
        with self.assertRaises(TypeError):
            self.tool(query="远山", connection_id="crm-b")

    def test_result_contains_no_credential(self) -> None:
        self.assertNotIn("demo-token", json.dumps(self.tool(query="远山")))


if __name__ == "__main__":
    if "--test" in sys.argv:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
    else:
        service, context = make_demo()
        search = bind_search(service, context, "crm-a")
        print(json.dumps(search(query="远山", limit=5), ensure_ascii=False, indent=2))
