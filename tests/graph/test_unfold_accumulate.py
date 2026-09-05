# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""τ² port: one U per task when the bed calls run() once per conversational turn."""
from __future__ import annotations

import threading

import pytest

from harnessx.graph.unfold import (
    recorder_for_run,
    release_recorder,
    unfold_accumulate_enabled,
)


def test_flag_defaults_off_and_reads_at_call_time(monkeypatch):
    monkeypatch.delenv("HARNESSX_GHX_UNFOLD_ACCUMULATE", raising=False)
    assert unfold_accumulate_enabled() is False
    monkeypatch.setenv("HARNESSX_GHX_UNFOLD_ACCUMULATE", "1")
    assert unfold_accumulate_enabled() is True
    monkeypatch.setenv("HARNESSX_GHX_UNFOLD_ACCUMULATE", "off")
    assert unfold_accumulate_enabled() is False


def test_same_run_id_reuses_one_recorder():
    release_recorder("r1", "s1")
    a = recorder_for_run("r1", "s1")
    b = recorder_for_run("r1", "s1")
    assert a is b
    # a different run (another task running concurrently) gets its own
    c = recorder_for_run("r2", "s1")
    assert c is not a
    release_recorder("r1", "s1")
    release_recorder("r2", "s1")


def test_ordinals_stay_monotonic_across_turns():
    """The whole point: turn 2's nodes must not restart at ordinal 0 and
    collide with turn 1's, or the merged U would have duplicate ids."""
    release_recorder("r3", "s3")
    rec = recorder_for_run("r3", "s3")
    n1 = rec.record_invocation(actor=None, processor=_Proc("p"), hook="before_model", step=0, prev_in_firing=None)
    # a later turn resumes into the same run id and gets the same recorder
    rec2 = recorder_for_run("r3", "s3")
    n2 = rec2.record_invocation(actor=None, processor=_Proc("p"), hook="before_model", step=4, prev_in_firing=None)
    assert rec2 is rec
    assert n1 != n2
    u = rec.finalize(None)
    assert len(u.nodes) == 2
    steps = sorted(n.step for n in u.nodes)
    assert steps == [0, 4]  # both turns present, not just the last
    release_recorder("r3", "s3")


def test_release_frees_the_entry():
    rec = recorder_for_run("r4", "s4")
    release_recorder("r4", "s4")
    assert recorder_for_run("r4", "s4") is not rec
    release_recorder("r4", "s4")


def test_concurrent_creation_yields_one_recorder():
    """tau2 runs simulations in threads; two turns of the same task must never
    race into two recorders (the second would silently drop the first's nodes)."""
    release_recorder("r5", "s5")
    seen: list = []
    barrier = threading.Barrier(8)

    def grab():
        barrier.wait()
        seen.append(recorder_for_run("r5", "s5"))

    threads = [threading.Thread(target=grab) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len({id(r) for r in seen}) == 1
    release_recorder("r5", "s5")


class _Proc:
    def __init__(self, name):
        self.__class__.__name__ = "Proc"
        self._name = name

    @property
    def __name__(self):  # the recorder labels by name when there is no actor
        return self._name


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__, "-q"])
