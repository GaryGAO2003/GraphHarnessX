# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Bucket-level reputation — moving average of hit_rate per 4-bucket category.

Planner consumes this to shape brief distribution. Unknown buckets receive
a boost to encourage exploration of unexplored spaces.
"""
from __future__ import annotations

import logging
from collections import deque

BUCKETS = ("prompt", "tools", "config", "processor")
_UNKNOWN_BOOST = 0.7

_log = logging.getLogger(__name__)


class Reputation:
    def __init__(self, window: int = 5):
        self.window = window
        self._history: dict[str, deque[bool]] = {}

    def record(self, bucket: str, hit: bool) -> None:
        # Two ways a record used to disappear here, both silent. A list bucket
        # (which the structure gate accepts) is an unhashable key, so this
        # raised into the caller's `except Exception: pass`. And a key outside
        # BUCKETS survives in memory but is dropped by to_dict on save, so it
        # looks recorded right up until the round ends. Neither is worth
        # crashing a campaign over, but neither may pass unnoticed again.
        if not isinstance(bucket, str) or bucket not in BUCKETS:
            _log.warning(
                "reputation: refusing to record bucket %r — not one of %s; "
                "normalise at the call site (a list bucket needs one record per bucket)",
                bucket,
                ", ".join(BUCKETS),
            )
            return
        dq = self._history.setdefault(bucket, deque(maxlen=self.window))
        dq.append(hit)

    def score(self, bucket: str) -> float:
        dq = self._history.get(bucket)
        if not dq:
            return _UNKNOWN_BOOST
        return sum(1 for h in dq if h) / len(dq)

    def downweight_all(self, factor: float = 0.9) -> None:
        for bucket, dq in self._history.items():
            # Drop at least 1 True if any exist, otherwise drop based on factor
            n_drop = max(1, int(len(dq) * (1 - factor)))
            for _ in range(n_drop):
                if True in dq:
                    for i, v in enumerate(dq):
                        if v:
                            dq[i] = False
                            break

    def to_dict(self) -> dict:
        return {b: list(self._history.get(b, [])) for b in BUCKETS}

    @classmethod
    def from_dict(cls, data: dict, window: int = 5) -> "Reputation":
        rep = cls(window=window)
        for bucket, history in data.items():
            rep._history[bucket] = deque(history, maxlen=window)
        return rep
