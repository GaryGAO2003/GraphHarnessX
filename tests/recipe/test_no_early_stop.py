# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""--no-early-stop, this branch's twin of the baseline's 0b16a20.

The pilot stops after two consecutive noop evolves. Right for an open-ended
run; fatal for a fixed-horizon campaign, where every arm must reach the same
round: M20's L0 arm was cut at R2 of 3 by exactly this ("EARLY STOP: 2
consecutive unchanged configs"), and the 16-round reference run falsely
early-stopped at R13. An arm cut at a different round than its siblings breaks
every cross-arm reading downstream.
"""
from __future__ import annotations

import inspect


def test_the_flag_exists_and_defaults_off():
    from recipe.gaia_evolver.run_meta_aegis import _build_argparser

    p = _build_argparser()
    base = ["--tasks", "x.json"]
    assert p.parse_args(base).no_early_stop is False, (
        "unset must reproduce the official build, same as every other knob"
    )
    assert p.parse_args(base + ["--no-early-stop"]).no_early_stop is True


def test_the_stop_is_guarded_by_the_flag():
    import recipe.gaia_evolver.run_meta_aegis as m

    src = inspect.getsource(m)
    assert "if noop_streak >= 2 and not args.no_early_stop:" in src, (
        "the break must consult the flag — M20_L0_ghx0 died at R2/3 without it"
    )
    # And the kept-alive path still says out loud that a default run would have
    # stopped, so a fixed-horizon log remains comparable with a default log.
    assert "would have early-stopped" in src
