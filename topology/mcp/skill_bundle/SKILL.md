---
name: topology
description: Operate the user's DriveNets Topology Studio domains and topologies from Cursor chat: create/edit/share domains, edit canvas objects, trigger discovery, and run scaler wizard dry-runs through the installed topology MCP.
---

# DriveNets Topology Skill

Use this skill when the user asks Cursor to inspect, create, edit, share, or automate DriveNets Topology Studio domains and topologies.

## Required MCP

This skill requires the `topology` MCP server installed from the web app's **Connect Cursor** flow.

Verify before work:

1. Call `topology_health`.
2. Confirm `ok=true` and the returned `username` matches the current user.
3. If auth fails, ask the user to reopen the Topology Studio Connect Cursor dialog and rotate the token.

## Operating Rules

- Work only through the `topology` MCP tools.
- Never assume access to another user's domains. Permission errors are expected and must not be worked around.
- Treat `read` as View and `write` as Edit in user-facing text.
- For live wizard actions, keep `dry_run=true` unless the user explicitly provides the required confirmation phrase.
- Prefer `topology_call_tool` for less common operations; pass `{ "tool_name": "...", "arguments": {...} }`.

## Common Workflows

- Inspect available work: `topology_list_domains`, then `topology_list_topologies`.
- Fetch a canvas: `topology_get_topology`.
- Create a domain: `topology_create_domain`.
- Create a blank topology: `topology_create_topology`.
- Validate or summarize: `topology_validate_topology`, `topology_summarize_topology`.
- Group objects: `topology_list_groups`, `topology_create_group`,
  `topology_set_group_members`, `topology_disband_group`, `topology_auto_group`.
- Import from other MCPs: call Network Mapper or dnos-config first, then pass the
  already-fetched JSON to `topology_plan_from_network_mapper` or
  `topology_plan_from_dnos_json`; save only with `topology_create_from_plan`
  after preview review.
- Build automatically: `topology_call_tool` with `topology_create_mesh`, `topology_create_chain`, or `topology_create_star`.
- Edit an object: `topology_call_tool` with `topology_update_object`,
  `topology_batch_update_objects`, or a typed helper such as `topology_add_device`.
- Share: `topology_call_tool` with `topology_share_domain` or `topology_share_topology`.

See `tools.md` and `workflows.md` for the full tool list.

