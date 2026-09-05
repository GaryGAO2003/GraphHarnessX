"""Shared runtime-only processor stub for the graph tests."""

from harnessx.core.processor import MultiHookProcessor


class _RtProc(MultiHookProcessor):
    """Runtime-only processor: not serializable, no class hook."""

    _order = 7

    async def on_task_start(self, event):
        yield event
