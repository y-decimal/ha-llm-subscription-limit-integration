"""Tests for the provider client without Home Assistant."""

import asyncio
import importlib.util
from pathlib import Path
import sys
import unittest

path = Path(__file__).resolve().parents[1] / "custom_components/llm_subscription_limits/providers/opencode_go.py"
spec = importlib.util.spec_from_file_location("go_provider", path)
go = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = go
spec.loader.exec_module(go)


class Response:
    def __init__(self, status=200, data=None):
        self.status = status
        self.data = data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def json(self):
        return self.data


class Session:
    def __init__(self, response):
        self.response = response
        self.kwargs = None

    def get(self, url, **kwargs):
        self.url = url
        self.kwargs = kwargs
        return self.response


def payload():
    return {"usage": {key: {"percent": 25, "status": "ok", "resetsAt": "2026-12-01T00:00:00Z"}
                      for key in go.WINDOWS}}


class ProviderTests(unittest.TestCase):
    def fetch(self, response):
        session = Session(response)
        data = asyncio.run(go.OpenCodeGoClient(session, "fake-key").fetch())
        return session, data

    def test_success_and_security(self):
        session, data = self.fetch(Response(data=payload()))
        self.assertEqual(set(data), set(go.WINDOWS))
        self.assertEqual(data["rolling"].percent, 25)
        self.assertIsNotNone(data["weekly"].resets_at.utcoffset())
        self.assertEqual(session.url, go.URL)
        self.assertFalse(session.kwargs["allow_redirects"])

    def test_auth_and_entitlement(self):
        for status, error in ((401, go.AuthenticationError), (403, go.EntitlementError), (500, go.ProviderError)):
            with self.subTest(status=status), self.assertRaises(error):
                self.fetch(Response(status=status))

    def test_invalid_data(self):
        for value in (None, True, "5", -1, 101, float("nan")):
            data = payload()
            data["usage"]["weekly"]["percent"] = value
            with self.subTest(value=value), self.assertRaises(go.ProviderError):
                self.fetch(Response(data=data))

    def test_missing_window_and_timezone(self):
        data = payload()
        del data["usage"]["rolling"]
        with self.assertRaises(go.ProviderError):
            self.fetch(Response(data=data))
        data = payload()
        data["usage"]["rolling"]["resetsAt"] = "2026-12-01T00:00:00"
        with self.assertRaises(go.ProviderError):
            self.fetch(Response(data=data))
