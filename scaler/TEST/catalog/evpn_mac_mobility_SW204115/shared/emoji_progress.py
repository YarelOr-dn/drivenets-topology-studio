"""Suite-level shim re-exporting :mod:`_shared.lib.emoji_progress`."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_TEST_DIR = _HERE.parents[3]
_SHARED_LIB = _TEST_DIR / "_shared" / "lib"
_SCALER_LIB = Path.home() / "SCALER" / "TEST" / "_shared" / "lib"
_WORKSPACE_LIB = Path.home() / "drivenets-topology-studio" / "scaler" / "TEST" / "_shared" / "lib"

for candidate in (_SHARED_LIB, _SCALER_LIB, _WORKSPACE_LIB):
    if candidate.exists() and str(candidate.parent) not in sys.path:
        sys.path.insert(0, str(candidate.parent))
        break

from lib.emoji_progress import *      # noqa: E402,F401,F403
from lib.emoji_progress import (      # noqa: E402
    phase_start,
    phase_end,
    command,
    anomaly,
    info,
    fail,
    set_sink,
    enable,
    disable,
    emoji_for_phase,
)

__all__ = [
    "phase_start",
    "phase_end",
    "command",
    "anomaly",
    "info",
    "fail",
    "set_sink",
    "enable",
    "disable",
    "emoji_for_phase",
]
