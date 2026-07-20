"""mcp_common.profiles - modular per-MCP profile registry (additive scaffold).

Phase 1 goal: introduce the registry + shared-helper layer WITHOUT touching the
``command_profiles.py`` monolith, so:

* the six live MCP servers keep importing ``command_profiles`` exactly as today
  (zero behavior change), and
* NEW modular profiles (the SCALE vertical in Phase 2, then the verbatim moves in
  Phase 5) plug in here, each isolated in its own ``try/except`` so a broken new
  module degrades only itself (``PROFILE_LOAD_ERROR``) instead of crashing the
  fleet.

``_shared`` re-exports the schema/arg helpers from ``command_profiles`` (``_tool``,
``_text``, ``_object_array``, ...) so new profiles build identical tool schemas
without duplicating helper code.

``registry`` exposes ``PROFILES`` / ``HANDLERS`` / ``get_tool_definitions`` /
``handle_tool_call`` with behavior identical to the legacy module for legacy
profiles, plus routing for new ones.
"""

from __future__ import annotations

__all__ = ["registry", "_shared"]
