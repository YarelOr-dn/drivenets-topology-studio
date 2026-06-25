"""Event bus backends for cross-process event propagation.

The in-process :class:`~topology.api.event_bus.EventBus` handles fan-out
to WebSocket clients of *this* uvicorn worker. When topology is run
with multiple workers or replicas, events published on one worker
would never reach subscribers on another worker without a
cross-process pub/sub layer.

This module defines the :class:`EventBusBackend` interface and two
concrete implementations:

* :class:`InProcessBackend` -- a no-op. This is the default and
  matches the behaviour of topology before Wave 5.
* :class:`RedisPubsubBackend` -- a stub that publishes and subscribes
  via Redis pub/sub under an ``TP_EVENT_BUS_BACKEND=redis`` flag.
  If the ``redis`` python package is unavailable or the broker is
  unreachable, the backend logs a warning and degrades to no-op so
  the server still starts.

The backend is paired with an :class:`EventBus` via
:meth:`EventBus.attach_backend`. When ``publish_to_user`` is called on
the bus, it first delivers locally and then asks the backend to
propagate the event to peer workers. Incoming messages from the
backend are delivered via the bus's ``_deliver_from_backend`` callback
so remote events fan out to local WebSockets without re-entering
``publish`` (preventing loops).

A per-process :data:`ORIGIN_ID` tag on every outgoing payload lets the
publishing worker ignore its own echo when the broker replays the
message.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import uuid
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, Optional


logger = logging.getLogger(__name__)


ORIGIN_ID = uuid.uuid4().hex


OnMessage = Callable[[str, Dict[str, Any]], Awaitable[None]]


class EventBusBackend(ABC):
    """Abstract base class for cross-process event-bus propagation."""

    kind: str = "abstract"

    @abstractmethod
    async def start(self, on_message: OnMessage) -> None:
        """Register the incoming-message callback and start any I/O."""

    @abstractmethod
    async def publish(self, username: str, event: Dict[str, Any]) -> None:
        """Relay an event to peer workers."""

    @abstractmethod
    async def stop(self) -> None:
        """Shut down connections and background tasks."""

    def stats(self) -> Dict[str, Any]:
        """Return monitoring counters. Overridden per backend."""
        return {"kind": self.kind}


class InProcessBackend(EventBusBackend):
    """No-op backend used when topology is a single uvicorn worker."""

    kind = "inprocess"

    async def start(self, on_message: OnMessage) -> None:
        return None

    async def publish(self, username: str, event: Dict[str, Any]) -> None:
        return None

    async def stop(self) -> None:
        return None


class RedisPubsubBackend(EventBusBackend):
    """Redis pub/sub backend (stub).

    * ``publish(user, event)`` -> ``PUBLISH tp:events:<user> <payload>``
    * ``start()`` -> ``PSUBSCRIBE tp:events:*``; incoming messages
      are decoded, checked against :data:`ORIGIN_ID`, and dispatched
      to the registered callback.

    Payload format::

        {"__origin__": "<hex>", "event": {...}}

    On start, if :mod:`redis.asyncio` cannot be imported or the
    broker is unreachable, the backend logs a warning and turns
    itself into a no-op. This keeps the server startable in
    environments that set ``TP_EVENT_BUS_BACKEND=redis`` but don't
    have the infra up yet.

    This is a stub implementation: we pattern-subscribe to all
    channels rather than dynamically track per-user subscriptions.
    Traffic is filtered on the receiver side. That keeps the
    implementation small and correct, at the cost of some wasted
    bandwidth for deployments with many idle users.
    """

    kind = "redis"
    channel_pattern = "tp:events:*"
    channel_prefix = "tp:events:"

    def __init__(self, url: str) -> None:
        self._url = url
        self._redis: Any = None
        self._pubsub: Any = None
        self._reader_task: Optional[asyncio.Task] = None
        self._on_message: Optional[OnMessage] = None
        self._started = False
        self._degraded = False
        self._publish_count = 0
        self._receive_count = 0
        self._echo_drops = 0
        self._errors = 0

    async def start(self, on_message: OnMessage) -> None:
        if self._started or self._degraded:
            return
        self._on_message = on_message
        try:
            import redis.asyncio as _redis  # type: ignore
        except ImportError:
            logger.warning(
                "[event_bus_backend] redis.asyncio unavailable; "
                "RedisPubsubBackend degrading to no-op "
                "(install `redis>=4.2` to enable)"
            )
            self._degraded = True
            return
        try:
            self._redis = _redis.Redis.from_url(self._url, decode_responses=True)
            await self._redis.ping()
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[event_bus_backend] redis connect %s failed: %s; "
                "degrading to no-op", self._url, exc,
            )
            self._redis = None
            self._degraded = True
            return
        self._pubsub = self._redis.pubsub()
        await self._pubsub.psubscribe(self.channel_pattern)
        self._reader_task = asyncio.create_task(
            self._reader_loop(), name="eventbus-redis-reader",
        )
        self._started = True
        logger.info(
            "[event_bus_backend] redis pubsub started url=%s origin=%s",
            self._url, ORIGIN_ID[:8],
        )

    async def publish(self, username: str, event: Dict[str, Any]) -> None:
        if not self._started or self._redis is None:
            return
        try:
            payload = json.dumps({"__origin__": ORIGIN_ID, "event": event})
            await self._redis.publish(
                f"{self.channel_prefix}{username}", payload,
            )
            self._publish_count += 1
        except Exception as exc:  # noqa: BLE001
            self._errors += 1
            logger.debug(
                "[event_bus_backend] publish failed user=%s: %s",
                username, exc,
            )

    async def _reader_loop(self) -> None:
        assert self._pubsub is not None
        try:
            async for msg in self._pubsub.listen():
                if not msg:
                    continue
                if msg.get("type") not in ("pmessage", "message"):
                    continue
                channel = msg.get("channel") or ""
                if isinstance(channel, (bytes, bytearray)):
                    channel = channel.decode(errors="replace")
                if not channel.startswith(self.channel_prefix):
                    continue
                username = channel[len(self.channel_prefix):]
                raw = msg.get("data") or ""
                if isinstance(raw, (bytes, bytearray)):
                    raw = raw.decode(errors="replace")
                try:
                    decoded = json.loads(raw) if isinstance(raw, str) else {}
                except Exception:  # noqa: BLE001
                    self._errors += 1
                    continue
                if decoded.get("__origin__") == ORIGIN_ID:
                    self._echo_drops += 1
                    continue
                event = decoded.get("event") or {}
                self._receive_count += 1
                if self._on_message is not None:
                    try:
                        await self._on_message(username, event)
                    except Exception as exc:  # noqa: BLE001
                        self._errors += 1
                        logger.debug(
                            "[event_bus_backend] on_message failed "
                            "user=%s: %s", username, exc,
                        )
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.debug("[event_bus_backend] reader loop crashed: %s", exc)

    async def stop(self) -> None:
        self._started = False
        task = self._reader_task
        self._reader_task = None
        if task is not None and not task.done():
            task.cancel()
            with contextlib.suppress(Exception):
                await task
        if self._pubsub is not None:
            with contextlib.suppress(Exception):
                await self._pubsub.punsubscribe(self.channel_pattern)
                await self._pubsub.close()
            self._pubsub = None
        if self._redis is not None:
            with contextlib.suppress(Exception):
                await self._redis.close()
            self._redis = None

    def stats(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "url": self._url,
            "started": self._started,
            "degraded": self._degraded,
            "publish_count": self._publish_count,
            "receive_count": self._receive_count,
            "echo_drops": self._echo_drops,
            "errors": self._errors,
        }


def select_backend() -> EventBusBackend:
    """Pick a backend from environment configuration.

    Respects ``TP_EVENT_BUS_BACKEND`` (``inprocess`` or ``redis``) and
    ``TP_REDIS_URL`` for the Redis variant. Falls back to in-process
    if the selector is unrecognised.
    """
    kind = (os.environ.get("TP_EVENT_BUS_BACKEND") or "inprocess").strip().lower()
    if kind == "redis":
        url = os.environ.get("TP_REDIS_URL", "redis://localhost:6379/0")
        return RedisPubsubBackend(url)
    if kind and kind not in ("inprocess", "memory", "local"):
        logger.warning(
            "[event_bus_backend] unknown TP_EVENT_BUS_BACKEND=%r -- "
            "using in-process backend", kind,
        )
    return InProcessBackend()


__all__ = [
    "EventBusBackend",
    "InProcessBackend",
    "RedisPubsubBackend",
    "OnMessage",
    "ORIGIN_ID",
    "select_backend",
]
