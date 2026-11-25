"""OpenCode Go's documented usage API."""

from dataclasses import dataclass
from datetime import datetime
import math

import aiohttp

URL = "https://opencode.ai/inference/go/v1/usage"
WINDOWS = ("rolling", "weekly", "monthly")


class ProviderError(Exception):
    """Provider request or response failed."""


class AuthenticationError(ProviderError):
    """API key was rejected."""


class EntitlementError(ProviderError):
    """The key has no Go entitlement."""


@dataclass(frozen=True)
class Window:
    """One measured usage window."""

    percent: float
    status: str
    resets_at: datetime


class OpenCodeGoClient:
    """Fetch only usage; never send credentials to another host."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str) -> None:
        self._session = session
        self._api_key = api_key

    async def fetch(self) -> dict[str, Window]:
        """Validate the response, avoiding sensitive upstream error details."""
        try:
            async with self._session.get(
                URL,
                headers={"Authorization": f"Bearer {self._api_key}",
                         "User-Agent": "ha-llm-subscription-limits/0.1"},
                timeout=aiohttp.ClientTimeout(total=20),
                allow_redirects=False,
            ) as response:
                if response.status == 401:
                    raise AuthenticationError
                if response.status == 403:
                    raise EntitlementError
                if response.status != 200:
                    raise ProviderError(f"HTTP {response.status}")
                data = await response.json()
            usage = data["usage"]
            result = {}
            for name in WINDOWS:
                item = usage[name]
                value = item["percent"]
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError("invalid percentage")
                if not math.isfinite(value) or not 0 <= value <= 100:
                    raise ValueError("percentage outside range")
                status = item["status"]
                if not isinstance(status, str):
                    raise ValueError("invalid status")
                reset = datetime.fromisoformat(item["resetsAt"].replace("Z", "+00:00"))
                if reset.utcoffset() is None:
                    raise ValueError("timestamp has no timezone")
                result[name] = Window(value, status, reset)
            return result
        except (AuthenticationError, EntitlementError, ProviderError):
            raise
        except (aiohttp.ClientError, TimeoutError, ValueError, TypeError, KeyError, AttributeError) as err:
            raise ProviderError("Unable to retrieve valid usage data") from err
