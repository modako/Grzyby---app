"""Open-Meteo client: batching of many coordinates, pauses, retries and API call accounting.

Call weight follows the formula of the Open-Meteo website (results-preview.svelte, 2026-10):
weight = max(1, max(v/10, days/14 * v/10)) * locations, with v = variables x models.
Free non-commercial limits: 600 calls/min, 5 000/h, 10 000/day.
"""

import logging
import time

import requests

from pipeline.sources.http import USER_AGENT

log = logging.getLogger(__name__)

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
MAX_CALLS_PER_MINUTE = 400  # stay well below the 600/min limit


class LimitExceeded(RuntimeError):
    """Daily or hourly quota of the free API is used up: stop and resume on the next run."""


def call_weight(n_variables: int, n_days: int, n_locations: int = 1, n_models: int = 1) -> float:
    v = n_variables * max(n_models, 1) / 10.0
    return max(1.0, max(v, n_days / 14.0 * v)) * n_locations


class Client:
    def __init__(self, budget: float | None = None):
        self.calls = 0.0
        self.budget = budget
        self._window: list[tuple[float, float]] = []

    def get(self, url: str, params: dict, weight: float) -> list[dict]:
        """GET with accounting. Returns a list (one dict per location)."""
        if self.budget is not None and self.calls + weight > self.budget:
            raise RuntimeError(f"Call budget {self.budget} would be exceeded ({self.calls:.0f} used)")
        self._throttle(weight)
        for attempt in range(6):
            try:
                resp = requests.get(url, params=params, timeout=180, headers={"User-Agent": USER_AGENT})
            except (requests.ConnectionError, requests.Timeout) as exc:
                self._backoff(attempt, str(exc))
                continue
            if resp.status_code == 429 or resp.status_code >= 500:
                reason = _reason(resp)
                if "daily" in reason.lower() or "hourly" in reason.lower():
                    raise LimitExceeded(reason)
                self._backoff(attempt, f"HTTP {resp.status_code} {reason}")
                continue
            if resp.status_code != 200:
                raise RuntimeError(f"Open-Meteo HTTP {resp.status_code}: {_reason(resp)}")
            self.calls += weight
            self._window.append((time.monotonic(), weight))
            data = resp.json()
            return data if isinstance(data, list) else [data]
        raise RuntimeError(f"Open-Meteo failed after retries: {url}")

    def _throttle(self, weight: float) -> None:
        now = time.monotonic()
        self._window = [(t, w) for t, w in self._window if now - t < 60]
        used = sum(w for _, w in self._window)
        if self._window and used + weight > MAX_CALLS_PER_MINUTE:
            wait = 60 - (now - self._window[0][0]) + 1
            log.info("Pausing %.0f s to respect the per-minute limit", wait)
            time.sleep(max(wait, 1))
            self._window = []
        else:
            time.sleep(1)  # small pause between requests

    @staticmethod
    def _backoff(attempt: int, reason: str) -> None:
        wait = min(2 ** (attempt + 2), 120)
        log.warning("Open-Meteo: %s, retry in %d s", reason, wait)
        time.sleep(wait)


def _reason(resp: requests.Response) -> str:
    try:
        return resp.json().get("reason", resp.text[:200])
    except ValueError:
        return resp.text[:200]


def coord_params(points: list[tuple[float, float]]) -> dict:
    return {"latitude": ",".join(f"{lat:.2f}" for lat, _ in points),
            "longitude": ",".join(f"{lon:.2f}" for _, lon in points)}


def batches(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]
