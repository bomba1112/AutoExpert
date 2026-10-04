# ruff: noqa: E501
"""Push notifications of the Garage feed (product phase, stage 2): the sending interface only.

Today the feed is shown in the app ("Моя машина"); nothing leaves the server. A real sender (APNs /
FCM) implements PushSender and is set with set_sender() when the app is deployed to the server.
The default sender writes to the log and marks nothing as pushed.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Protocol

log = logging.getLogger("autoexpert.garage.push")


class PushMessage(dict):
    """user_id, vehicle_id, kind, key, payload."""


class PushSender(Protocol):
    def send(self, messages: list[PushMessage]) -> list[bool]:
        """Send the messages; one result per message (True: delivered to the push service)."""


class LogOnlySender:
    """No push service is connected: the messages are logged, none is marked as pushed."""

    def __init__(self) -> None:
        self.sent: list[PushMessage] = []

    def send(self, messages: list[PushMessage]) -> list[bool]:
        for m in messages:
            log.info("push (not connected) %s %s %s", m["user_id"], m["kind"], m["key"])
        self.sent.extend(messages)
        return [False] * len(messages)


_SENDER: PushSender = LogOnlySender()


def set_sender(sender: PushSender) -> None:
    global _SENDER
    _SENDER = sender


def sender() -> PushSender:
    return _SENDER


def deliver(db, vehicle, items, chosen: PushSender | None = None) -> None:
    messages = [PushMessage(user_id=vehicle.user_id, vehicle_id=vehicle.id, kind=i.kind, key=i.key, payload=i.payload)
                for i in items]
    results = (chosen or _SENDER).send(messages)
    now = datetime.now(UTC)
    for item, ok in zip(items, results, strict=False):
        if ok:
            item.pushed_at = now
