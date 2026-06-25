"""In-process event bus for per-user device-maintenance broadcasts.

Every browser tab that is logged in opens a WebSocket to
``/api/events/ws``. The bus keeps the open sockets per username and
pushes JSON frames whenever a maintenance action mutates the shared
device state. The channel is explicitly *per user* so a single user with
multiple tabs sees every event once per tab, and users who never
watched the device in question never see anything.

This is a light-weight pattern -- no external broker, no pub/sub server.
It runs inside the uvicorn worker process holding the WebSocket. When we
eventually grow past a single worker the right answer is to swap the
subscription map for Redis pub/sub; callers of ``publish`` don't need to
change.

Contract
--------

Events are dicts with ``type`` (string) + arbitrary payload. The bus
wraps outbound frames with ``{"type": "event", "event": {...}}`` so the
same WS channel can also carry service messages (``ping``, ``hello``,
``error``). Delivery is best-effort -- if a socket errors we drop it
from the subscription map but the publisher doesn't fail.

Watcher-aware publish
~~~~~~~~~~~~~~~~~~~~~

``publish_to_device_watchers(device_id, event_type, payload)`` is the
helper the device-maintenance code should call. It resolves the watcher
list from the shared ``device_state`` store and fans the event out to
every logged-in subscriber in that set. The actor (the user who
triggered the event) also receives it -- the frontend decides whether
to show a "you cleared this" banner vs a "another user cleared this"
banner based on ``actor_user`` vs ``self.username``.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Set

from fastapi import WebSocket

from .device_state import device_state
from .event_bus_backend import EventBusBackend, InProcessBackend


logger = logging.getLogger(__name__)


# Wave 3.2: per-WebSocket outbound queue. A slow/hung client can no
# longer block the publisher or other subscribers of the same user --
# we enqueue, then a dedicated writer task drains. On overflow we drop
# the OLDEST frame (client will reconcile on reconnect) rather than
# the newest, because for device events the freshest state matters
# more than historical replay.
_DEFAULT_QUEUE_SIZE = int(os.environ.get("TP_EVENT_WS_QUEUE_SIZE", "128"))


@dataclass
class _WSChannel:
    """One WebSocket + its private outbound queue and writer task."""

    ws: WebSocket
    queue: "asyncio.Queue[Optional[Dict[str, Any]]]"
    writer_task: Optional[asyncio.Task] = None
    enqueued: int = 0
    dropped: int = 0
    delivered: int = 0
    send_failures: int = 0
    alive: bool = True

    def snapshot(self) -> Dict[str, Any]:
        return {
            "enqueued": self.enqueued,
            "dropped": self.dropped,
            "delivered": self.delivered,
            "send_failures": self.send_failures,
            "queue_size": self.queue.qsize(),
            "queue_max": self.queue.maxsize,
            "alive": self.alive,
        }


class EventBus:
    """Per-user WebSocket broadcast. Safe to instantiate once and share."""

    def __init__(self, queue_size: int = _DEFAULT_QUEUE_SIZE) -> None:
        # username -> list of _WSChannel records.
        self._subs: Dict[str, List[_WSChannel]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._queue_size = max(4, int(queue_size))
        # Captured at the first successful subscribe() so sync callers
        # (uvicorn threadpool dispatching non-async endpoints) can still
        # schedule coroutines onto the main event loop. Without this,
        # `asyncio.get_running_loop()` raises RuntimeError from the
        # worker thread and broadcasts are silently dropped.
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
        # Wave 5.1: cross-process backend. The default is a no-op
        # :class:`InProcessBackend`; swap it in via ``attach_backend``
        # during app startup to enable Redis pub/sub or future
        # transports.
        self._backend: EventBusBackend = InProcessBackend()
        self._backend_started: bool = False

    def _capture_running_loop(self) -> None:
        """Remember the main event loop, ignoring redundant calls."""
        if self._main_loop is not None:
            return
        try:
            self._main_loop = asyncio.get_running_loop()
        except RuntimeError:
            self._main_loop = None

    def attach_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Explicitly bind a loop (e.g. during app startup)."""
        self._main_loop = loop

    # ------------------------------------------------------- backend wiring

    async def attach_backend(self, backend: EventBusBackend) -> None:
        """Install a cross-process backend and start its reader.

        Safe to call at app startup. If a previous backend is attached
        it will be stopped first so leftover tasks do not leak.
        """
        previous = self._backend
        self._backend = backend
        if self._backend_started:
            with contextlib.suppress(Exception):
                await previous.stop()
            self._backend_started = False
        await backend.start(self._deliver_from_backend)
        self._backend_started = True
        logger.info(
            "[event_bus] backend attached kind=%s", getattr(backend, "kind", "?"),
        )

    async def shutdown_backend(self) -> None:
        """Stop the backend. Called from the app shutdown hook."""
        if not self._backend_started:
            return
        self._backend_started = False
        with contextlib.suppress(Exception):
            await self._backend.stop()

    def backend_kind(self) -> str:
        return getattr(self._backend, "kind", "unknown")

    def backend_stats(self) -> Dict[str, Any]:
        try:
            return self._backend.stats()
        except Exception:  # noqa: BLE001
            return {"kind": self.backend_kind(), "error": "stats_failed"}

    async def _deliver_from_backend(
        self,
        username: str,
        event: Dict[str, Any],
    ) -> None:
        """Dispatch a cross-process event to local WS subscribers only.

        Must NOT call ``backend.publish`` -- that would create an echo
        loop with the broker. ``publish_to_user`` handles local +
        backend; this path is local only.
        """
        await self._local_publish_to_user(username, event)

    # -------------------------------------------------------- subscriptions

    def _find_channel(self, username: str, ws: WebSocket) -> Optional[_WSChannel]:
        for ch in self._subs.get(username, ()):  # type: ignore[arg-type]
            if ch.ws is ws:
                return ch
        return None

    async def subscribe(self, username: str, ws: WebSocket) -> None:
        if not username:
            raise ValueError("subscribe requires a non-empty username")
        self._capture_running_loop()
        async with self._lock:
            if self._find_channel(username, ws) is not None:
                return  # already subscribed; idempotent
            channel = _WSChannel(
                ws=ws,
                queue=asyncio.Queue(maxsize=self._queue_size),
            )
            channel.writer_task = asyncio.create_task(
                self._writer_loop(username, channel),
                name=f"eventbus-writer:{username}",
            )
            self._subs[username].append(channel)

    async def unsubscribe(self, username: str, ws: WebSocket) -> None:
        async with self._lock:
            chans = self._subs.get(username)
            if not chans:
                return
            idx = None
            for i, ch in enumerate(chans):
                if ch.ws is ws:
                    idx = i
                    break
            if idx is None:
                return
            channel = chans.pop(idx)
            if not chans:
                del self._subs[username]
        await self._shutdown_channel(channel)

    async def _shutdown_channel(self, channel: _WSChannel) -> None:
        channel.alive = False
        # Push sentinel to unblock writer.
        with contextlib.suppress(Exception):
            channel.queue.put_nowait(None)
        task = channel.writer_task
        if task is not None and not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task

    async def _writer_loop(self, username: str, channel: _WSChannel) -> None:
        """Per-WebSocket writer: drains queue, detaches on error."""
        try:
            while True:
                frame = await channel.queue.get()
                if frame is None:
                    return
                try:
                    await channel.ws.send_json(frame)
                    channel.delivered += 1
                except Exception as exc:  # noqa: BLE001
                    channel.send_failures += 1
                    channel.alive = False
                    logger.debug(
                        "[event_bus] writer failed user=%s err=%s", username, exc
                    )
                    # Detach asynchronously so we don't deadlock on our own task.
                    loop = self._main_loop or asyncio.get_event_loop()
                    loop.create_task(self._detach_on_failure(username, channel))
                    return
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.debug(
                "[event_bus] writer_loop crashed user=%s err=%s", username, exc
            )

    async def _detach_on_failure(self, username: str, channel: _WSChannel) -> None:
        async with self._lock:
            chans = self._subs.get(username)
            if not chans:
                return
            for i, ch in enumerate(chans):
                if ch is channel:
                    chans.pop(i)
                    break
            if not chans:
                del self._subs[username]

    def subscribers(self, username: str) -> List[WebSocket]:
        return [ch.ws for ch in self._subs.get(username, ()) if ch.alive]

    def subscriber_count(self, username: Optional[str] = None) -> int:
        if username is None:
            return sum(len(v) for v in self._subs.values())
        return len(self._subs.get(username, ()))

    def connected_users(self) -> List[str]:
        return [u for u, s in self._subs.items() if s]

    def stats(self) -> Dict[str, Any]:
        """Bus-wide metrics. Used by /api/health/concurrency (Wave 4.2)."""
        per_user: Dict[str, List[Dict[str, Any]]] = {}
        totals = {
            "users": 0,
            "sockets": 0,
            "enqueued": 0,
            "delivered": 0,
            "dropped": 0,
            "send_failures": 0,
        }
        for user, chans in self._subs.items():
            per_user[user] = [ch.snapshot() for ch in chans]
            totals["users"] += 1
            totals["sockets"] += len(chans)
            for ch in chans:
                totals["enqueued"] += ch.enqueued
                totals["delivered"] += ch.delivered
                totals["dropped"] += ch.dropped
                totals["send_failures"] += ch.send_failures
        return {
            "queue_max": self._queue_size,
            "totals": totals,
            "per_user": per_user,
            "backend": self.backend_stats(),
        }

    # ------------------------------------------------------------- publish

    def _enqueue(self, channel: _WSChannel, frame: Dict[str, Any]) -> bool:
        """Non-blocking enqueue with drop-oldest on overflow."""
        if not channel.alive:
            return False
        q = channel.queue
        try:
            q.put_nowait(frame)
            channel.enqueued += 1
            return True
        except asyncio.QueueFull:
            try:
                q.get_nowait()  # drop oldest
                channel.dropped += 1
            except asyncio.QueueEmpty:
                pass
            try:
                q.put_nowait(frame)
                channel.enqueued += 1
                return True
            except asyncio.QueueFull:
                channel.dropped += 1
                return False

    async def _local_publish_to_user(
        self,
        username: str,
        event: Dict[str, Any],
    ) -> int:
        """Enqueue one frame per live WS on THIS worker only.

        Internal helper shared by the public ``publish_to_user`` path
        and the cross-process ``_deliver_from_backend`` callback.
        """
        if not username:
            return 0
        frame = {"type": "event", "event": event}
        enqueued = 0
        for ch in list(self._subs.get(username, ())):
            if self._enqueue(ch, frame):
                enqueued += 1
        return enqueued

    async def publish_to_user(self, username: str, event: Dict[str, Any]) -> int:
        """Enqueue one frame per live WS for this username. Returns enqueued count.

        The return value reflects queued frames, not delivered ones -- the
        dedicated writer task completes delivery asynchronously. Callers
        that previously treated the count as "delivered" should treat it
        as "accepted for delivery".

        Wave 5.1: after local delivery, relay the event through the
        attached backend so peer workers can fan it out to their own
        subscribers. The backend echo is filtered via ``ORIGIN_ID`` so
        this worker never receives its own broadcast back.
        """
        enqueued = await self._local_publish_to_user(username, event)
        if self._backend_started and username:
            with contextlib.suppress(Exception):
                await self._backend.publish(username, event)
        return enqueued

    def enqueue_raw_to_ws(
        self,
        username: str,
        ws: WebSocket,
        frame: Dict[str, Any],
    ) -> bool:
        """Send a pre-built frame to one specific WS via its writer task.

        Used for handshake/keepalive frames (``hello``, ``pong``,
        ``__ping__``) that must not bypass the queue, because bypassing
        would race with the writer task on the same WebSocket.send_json
        (Starlette offers no built-in send lock).
        """
        channel = self._find_channel(username, ws)
        if channel is None:
            return False
        return self._enqueue(channel, frame)

    async def publish_to_users(
        self,
        usernames: Iterable[str],
        event: Dict[str, Any],
    ) -> Dict[str, int]:
        """Fan an event to several users. Returns per-user delivery counts."""
        seen = set()
        out: Dict[str, int] = {}
        for u in usernames:
            u = (u or "").strip()
            if not u or u in seen:
                continue
            seen.add(u)
            out[u] = await self.publish_to_user(u, event)
        return out

    async def publish_to_device_watchers(
        self,
        device_id: str,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        extra_users: Optional[Iterable[str]] = None,
    ) -> Dict[str, int]:
        """The common case: notify everyone with this device on their canvas.

        ``extra_users`` lets the caller force delivery to a user who may
        not appear as a watcher (e.g. the actor themselves -- the action
        may have just cleared them off the canvas, but they still want
        the UI feedback).
        """
        device_id = (device_id or "").strip()
        if not device_id or not event_type:
            return {}
        watchers = device_state.list_watchers_for_device(device_id, active_only=True)
        usernames = {w["username"] for w in watchers}
        if extra_users:
            for u in extra_users:
                if u:
                    usernames.add(u)
        event = {
            "type": event_type,
            "device_id": device_id,
            "payload": payload or {},
        }
        return await self.publish_to_users(usernames, event)

    # ------------------------------------------------------ sync publishers

    def publish_to_device_watchers_sync(
        self,
        device_id: str,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        extra_users: Optional[Iterable[str]] = None,
    ) -> None:
        """Fire-and-forget variant safe to call from sync handlers.

        The scaler bridge has plenty of non-async endpoints (`/probe`,
        `/verify-identity`, etc.). Uvicorn dispatches those onto a
        threadpool, where ``asyncio.get_running_loop()`` raises. We
        grabbed the main loop on the first WebSocket subscribe so we
        can schedule coroutines back onto it from any thread.

        Fallbacks, in order:
        1. Loop captured via subscribe() -> ``run_coroutine_threadsafe``.
        2. Currently running loop (when caller is async) -> ``ensure_future``.
        3. No loop available (pure CLI) -> drop silently; the audit log
           was already written by ``record_event``.
        """
        coro_factory = lambda: self.publish_to_device_watchers(
            device_id=device_id, event_type=event_type,
            payload=payload, extra_users=extra_users,
        )

        main_loop = self._main_loop
        if main_loop is not None and not main_loop.is_closed():
            with contextlib.suppress(Exception):
                asyncio.run_coroutine_threadsafe(coro_factory(), main_loop)
                return

        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if running is not None:
            with contextlib.suppress(Exception):
                running.create_task(coro_factory())
                return

        logger.debug(
            "[event_bus] no running loop for broadcast device=%s type=%s -- dropping",
            device_id, event_type,
        )

    async def send_ping(self, username: str) -> int:
        """Keepalive helper -- WS clients should also ping from their side."""
        return await self.publish_to_user(username, {"type": "__ping__"})

    # ------------------------------------------- sync fan-out to user set
    #
    # Used by the domain-knowledge layer (and any future code that needs to
    # fan an event to a domain's owner + every recipient of the share).
    # Mirrors ``publish_to_device_watchers_sync`` but takes the username
    # list directly instead of resolving it from ``device_state``.

    def publish_to_users_sync(
        self,
        usernames: Iterable[str],
        event: Dict[str, Any],
    ) -> None:
        """Fire-and-forget version of publish_to_users. Safe from any thread.

        Schedules the coroutine onto the captured main loop and returns
        immediately. If no loop is attached we drop the event silently --
        this is only used for optional live-update notifications, so
        losing one under unusual bootstrap conditions is not a bug.
        """
        user_list = [u for u in usernames if u]
        if not user_list or not event:
            return
        coro_factory = lambda: self.publish_to_users(user_list, event)
        main_loop = self._main_loop
        if main_loop is not None and not main_loop.is_closed():
            with contextlib.suppress(Exception):
                asyncio.run_coroutine_threadsafe(coro_factory(), main_loop)
                return
        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if running is not None:
            with contextlib.suppress(Exception):
                running.create_task(coro_factory())


event_bus = EventBus()
