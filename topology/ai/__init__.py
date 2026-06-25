"""AI assistant module for the DriveNets Topology Studio.

Public surface used by serve.py:
  - service.LlmClient                -- provider-agnostic chat + tool-calls
  - service.load_knowledge_digest    -- mtime-cached app knowledge
  - service.reload_knowledge         -- admin "Reload AI Knowledge" hook
  - context.build_live_context       -- per-user, per-canvas snapshot
  - context.TOPOLOGY_TOOL_SCHEMA     -- JSON-schema for create_topology
  - context.CANVAS_EDITS_TOOL_SCHEMA -- JSON-schema for apply_canvas_edits
  - context.LIST_BLUEPRINTS_TOOL_SCHEMA / LOAD_BLUEPRINT_TOOL_SCHEMA
  - blueprints.list_blueprints / load_blueprint / reload_blueprints

Every entry point is per-user. Config + history live under the user's
~/.topology_users/<username>/ workspace via user_store helpers; nothing
is stored globally.
"""

from .service import (  # noqa: F401
    LlmClient,
    LlmError,
    load_knowledge_digest,
    reload_knowledge,
    resolve_client_for_user,
)
from .context import (  # noqa: F401
    build_live_context,
    TOPOLOGY_TOOL_SCHEMA,
    CANVAS_EDITS_TOOL_SCHEMA,
    LIST_BLUEPRINTS_TOOL_SCHEMA,
    LOAD_BLUEPRINT_TOOL_SCHEMA,
    normalize_topology_payload,
)
from .blueprints import (  # noqa: F401
    list_blueprints,
    load_blueprint,
    reload_blueprints,
    blueprint_summary_for_prompt,
    taxonomy,
)
