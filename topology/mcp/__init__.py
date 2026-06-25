"""DriveNets Topology MCP server package.

This directory is intentionally named ``mcp`` to match the public URL and plan,
but the Python environment also provides the upstream ``mcp`` package. Extend
our package path to include the upstream package directory so imports such as
``mcp.server.fastmcp`` continue to resolve when ``topology/`` is on PYTHONPATH.
"""

from __future__ import annotations

from pathlib import Path
import sys

VERSION = "0.1.0"

_here = Path(__file__).resolve().parent
for _entry in list(sys.path):
    try:
        _candidate = (Path(_entry).resolve() / "mcp")
    except Exception:
        continue
    if _candidate == _here:
        continue
    if (_candidate / "server").is_dir() and (_candidate / "__init__.py").is_file():
        __path__.append(str(_candidate))  # type: ignore[name-defined]
        break

