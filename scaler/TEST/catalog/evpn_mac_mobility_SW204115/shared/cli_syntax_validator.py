"""Suite-level shim that re-exports the shared CLI syntax validator.

The validator implementation lives in :mod:`scaler.TEST._shared.lib.cli_syntax_validator`.
Keeping a shim here means existing imports
(``from shared.cli_syntax_validator import CliSyntaxValidator``) keep working,
while the actual logic + cache layer is shared across every /TEST suite.

Why a shim instead of a hard symlink? Because the suites also live in
``~/SCALER/TEST/catalog/<suite>/`` after sync, and Python imports must work
from both ``drivenets-topology-studio/scaler/...`` and ``~/SCALER/...``. A
small import-shim is the cleanest way to get the right module regardless of
which copy is on the path.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Find _shared/lib regardless of whether we're imported from the worktree or
# from ~/SCALER/TEST/catalog/.
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve()
# .../catalog/<suite>/shared/cli_syntax_validator.py
#                ^suite_dir       ^catalog_dir       ^TEST_dir
_TEST_DIR = _HERE.parents[3]                # .../scaler/TEST  OR  ~/SCALER/TEST
_SHARED_LIB = _TEST_DIR / "_shared" / "lib"

# Also try the workspace path in case we're run from ~/SCALER and the lib
# isn't there yet (first-run before sync).
_WORKSPACE_LIB = Path.home() / "drivenets-topology-studio" / "scaler" / "TEST" / "_shared" / "lib"
_SCALER_LIB = Path.home() / "SCALER" / "TEST" / "_shared" / "lib"

for candidate in (_SHARED_LIB, _SCALER_LIB, _WORKSPACE_LIB):
    if candidate.exists() and str(candidate.parent) not in sys.path:
        sys.path.insert(0, str(candidate.parent))
        break

# Re-export the shared validator + supporting helpers.
from lib.cli_syntax_validator import (  # noqa: E402  (post sys.path tweak)
    CliSyntaxValidator,
    ValidationReport,
    _Cache,
    _StoreBackedCache,
)

__all__ = [
    "CliSyntaxValidator",
    "ValidationReport",
    "_Cache",
    "_StoreBackedCache",
]
