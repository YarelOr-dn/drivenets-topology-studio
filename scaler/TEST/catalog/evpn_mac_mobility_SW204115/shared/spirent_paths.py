"""Single source of truth for the SPIRENT tooling location.

PR6 (2026-04-14): every shared module that shells out to the spirent tool used
to define its own ``SPIRENT_TOOL = Path.home() / "SCALER" / "SPIRENT" / ...``
constant. That made the path impossible to override per-environment and led
to subtle drift between modules. This file replaces all of those copies.

Resolution order (first hit wins):

  1. ``$EVPN_MM_SPIRENT_TOOL`` -- explicit override for one suite invocation.
  2. ``$SPIRENT_HOME / spirent_tool.py`` -- when the user has the standard
     SPIRENT environment variable set (the same one the spirent_tool itself
     respects).
  3. ``$SCALER_HOME / SPIRENT / spirent_tool.py`` -- support sites that
     install the scaler tree somewhere other than ``~/SCALER``.
  4. ``~/SCALER/SPIRENT/spirent_tool.py`` -- the historical default.
  5. ``~/drivenets-topology-studio/scaler/SPIRENT/spirent_tool.py`` -- the
     in-repo worktree path (used during development before the
     install/sync step).
  6. Anything on ``$PATH`` named ``spirent_tool.py``.

Helpers:

  * ``spirent_tool_path()`` -> ``Path``: returns the resolved absolute path.
    Always returns SOMETHING (the historical default if nothing else
    resolves) so callers can still build error messages with a sensible
    string -- use ``spirent_tool_available()`` to decide whether to call it.
  * ``spirent_tool_available()`` -> ``bool``: cheap existence check.
  * ``spirent_tool_command(*args)`` -> ``list[str]``: builds the standard
    ``["python3", <tool>, *args]`` argv for ``subprocess.run``.

The result is cached at import time and re-checked only when the env vars
change between two ``spirent_tool_path(refresh=True)`` calls -- this keeps
the hot path in ``_run_spirent`` cheap.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

_HISTORICAL_DEFAULT: Path = Path.home() / "SCALER" / "SPIRENT" / "spirent_tool.py"
_WORKTREE_DEFAULT: Path = (
    Path.home() / "drivenets-topology-studio" / "scaler" / "SPIRENT" / "spirent_tool.py"
)

_cached_path: Optional[Path] = None
_cached_signature: Optional[Tuple[str, str, str]] = None


def _candidate_paths() -> List[Path]:
    """Return ordered candidate locations -- duplicates are filtered."""
    seen: set[Path] = set()
    out: List[Path] = []

    def _add(p: Optional[Path]) -> None:
        if p is None:
            return
        rp = Path(p).expanduser()
        if rp not in seen:
            seen.add(rp)
            out.append(rp)

    override = os.environ.get("EVPN_MM_SPIRENT_TOOL")
    if override:
        _add(Path(override))

    spirent_home = os.environ.get("SPIRENT_HOME")
    if spirent_home:
        _add(Path(spirent_home) / "spirent_tool.py")

    scaler_home = os.environ.get("SCALER_HOME")
    if scaler_home:
        _add(Path(scaler_home) / "SPIRENT" / "spirent_tool.py")

    _add(_HISTORICAL_DEFAULT)
    _add(_WORKTREE_DEFAULT)

    on_path = shutil.which("spirent_tool.py")
    if on_path:
        _add(Path(on_path))

    return out


def _current_signature() -> Tuple[str, str, str]:
    return (
        os.environ.get("EVPN_MM_SPIRENT_TOOL", ""),
        os.environ.get("SPIRENT_HOME", ""),
        os.environ.get("SCALER_HOME", ""),
    )


def spirent_tool_path(refresh: bool = False) -> Path:
    """Return the resolved spirent_tool.py path.

    The first existing candidate is returned. If none exist, the historical
    default ``~/SCALER/SPIRENT/spirent_tool.py`` is returned anyway -- this
    lets callers build human-readable error messages and avoids surprising
    ``None`` results in legacy code paths.
    """
    global _cached_path, _cached_signature
    sig = _current_signature()
    if not refresh and _cached_path is not None and _cached_signature == sig:
        return _cached_path

    for cand in _candidate_paths():
        if cand.is_file():
            _cached_path = cand
            _cached_signature = sig
            return cand

    _cached_path = _HISTORICAL_DEFAULT
    _cached_signature = sig
    return _cached_path


def spirent_tool_available() -> bool:
    """True only if a spirent_tool.py file actually exists on disk."""
    for cand in _candidate_paths():
        if cand.is_file():
            return True
    return False


def spirent_tool_command(*args: str) -> List[str]:
    """Build a ``subprocess`` argv that always uses the resolved tool path."""
    return ["python3", str(spirent_tool_path()), *args]


def all_candidate_paths() -> List[Path]:
    """Diagnostic helper -- returns the list the resolver searches, in order."""
    return _candidate_paths()


__all__ = [
    "spirent_tool_path",
    "spirent_tool_available",
    "spirent_tool_command",
    "all_candidate_paths",
]
