"""Named worker fault barriers used by deterministic crash tests."""

from __future__ import annotations

import os
from typing import Protocol


class FaultInjector(Protocol):
    def hit(self, point: str) -> None: ...


class NoopFaultInjector:
    def hit(self, point: str) -> None:
        return None


class ExitAtFault:
    """Terminate the current process at one exact named barrier."""

    def __init__(self, point: str, exit_code: int = 97) -> None:
        self.point = point
        self.exit_code = exit_code

    def hit(self, point: str) -> None:
        if point == self.point:
            os._exit(self.exit_code)


NO_FAULTS = NoopFaultInjector()
