# Topology MCP Workflows

## Choose A Destination Domain (Mandatory For Every Create)

Every create flow that produces a new topology -- mesh/star/chain helpers,
plan-from-network-mapper, plan-from-dnos, plan-from-image, bug topologies,
duplicate -- MUST ask the user which domain to save into. Do not silently
default to the first listed domain or to a "default" name.

1. `topology_list_domains()` -- fetch the user's own domains and any shared
   domains they have write access to.
2. Use AskQuestion with one option per writable domain plus a final
   "Create new domain..." option. If the call returns shared domains the
   user only has view access to, exclude them from the choices.
3. If the user picks "Create new domain...", AskQuestion again for the new
   domain name (and an optional description), then call
   `topology_create_domain(name=..., description=...)`. Use the returned
   `domain.id` as the destination.
4. Pass that resolved `domain_id` to the create call
   (`topology_create_from_plan`, `topology_create_mesh`, `topology_create_topology`,
   `topology_create_bug_topology`, etc.).
5. After save, list topologies in the destination and confirm visibility. If
   the new topology is not in the app dropdown, call
   `topology_repair_legacy_visibility(domain_id, topology_id)`.

Bug topologies are the only exception: `topology_create_bug_topology` always
saves into the per-user `__bugs` domain by design, so the AskQuestion step is
skipped.

## Create A 5-PE Mesh

1. Run the "Choose A Destination Domain" workflow above.
2. `topology_create_mesh(domain_id="<chosen id>", name="5 PE Mesh", device_count=5, device_type="PE", mesh_type="full")`
3. `topology_get_topology(domain_id="<chosen id>", topology_id="<new id>")` to verify.

## Add A Device To An Existing Canvas

1. `topology_get_topology(domain_id, topology_id)`
2. Pick a free coordinate.
3. `topology_add_device(domain_id, topology_id, properties={...})`

Useful properties:

```json
{
  "label": "PE-1",
  "deviceType": "PE",
  "x": 220,
  "y": 180,
  "color": "#0ea5e9",
  "splitColor": {
    "left": "#0ea5e9",
    "right": "#f97316"
  }
}
```

## Import From Network Mapper Or dnos-config

Topology MCP does not call other MCPs directly. Keep the source MCP as the
owner of live data, then hand the JSON to Topology MCP:

1. Call Network Mapper or dnos-config to collect device/link/path JSON.
2. Call `topology_plan_from_network_mapper` or `topology_plan_from_dnos_json`
   with that JSON.
3. Review `plan.summary`, `plan.warnings`, and `plan.validation`.
4. Save only accepted previews with `topology_create_from_plan`.

## Generate A Topology From An Image In Chat

When the user attaches a network diagram to chat and asks for a matching
canvas topology, the agent (not the MCP) parses the image. The MCP only
turns the agent's structured extraction into a saveable plan.

1. Read the image with the agent's own vision capability. Identify every
   device label, role/type (PE, P, RR, CE, leaf, spine, ...), every link
   between two devices, link labels (interfaces, protocols, BD/VRF, VLANs)
   when visible, and any visual clusters/swimlanes that should become groups.
2. Pick X/Y coordinates that match the layout in the image. Map the diagram
   bounding box into the canvas working area (roughly `x: 80..1500`,
   `y: 80..900`). Spread devices so labels do not collide.
3. Build a payload. Preserve visual styles, not just topology semantics:

   ```json
   {
     "devices": [
       {"label": "PE-1", "deviceType": "PE", "role": "PE", "x": 220, "y": 220,
        "visualStyle": "classic", "color": "#0ea5e9", "radius": 44},
       {"label": "CE-A", "deviceType": "CE", "role": "CE", "x": 220, "y": 520,
        "visualStyle": "server", "color": "#2563eb"},
       {"label": "P-1",  "deviceType": "P",  "role": "P",  "x": 600, "y": 80,
        "visualStyle": "hex", "color": "#64748b"}
     ],
     "links": [
       {"source": "PE-1", "target": "P-1", "label": "ge-0/0/0",
        "style": "dashed-arrow", "color": "#ffffff", "width": 3},
       {"source": "CE-A", "target": "PE-1", "label": "access",
        "style": "solid", "color": "#94a3b8", "width": 2},
       {"source": "PE-1", "target": "P-1", "protocol": "iBGP",
        "style": "dotted", "color": "#38bdf8"}
     ],
     "groups": [
       {"name": "Provider/Core", "members": ["PE-1", "P-1"]},
       {"name": "Customer Site", "members": ["CE-A"]}
     ],
     "shapes": [
       {"label": "Provider Edge", "x": 80, "y": 80, "width": 520, "height": 300, "fillColor": "#1f77b4"}
     ],
     "texts": [
       {"text": "IRB\nIP = 100.100.100.1/24", "x": 640, "y": 80}
     ]
   }
   ```

   Device fields may be flat or nested under `style: {...}`:
   `visualStyle`/`deviceStyle`, `color`/`fillColor`, `radius`/`size`,
   `rotation`, `labelColor`, `labelSize`, `fontFamily`, `fontWeight`.
   Link fields may be flat or nested: `style`/`lineStyle`/`linkStyle`,
   `color`/`strokeColor`, `width`/`strokeWidth`, and `curveOverride`.

4. Call `topology_plan_from_image(image_extraction_json=payload, name="<topology name>")`.
   Defaults keep the positions you extracted; pass `auto_layout=True` only if
   the image was too sparse to extract coordinates.
5. Show `plan.summary`, `plan.warnings`, and any `plan.validation.issues` to
   the user. Fix missing endpoints or duplicate IDs in the payload and
   re-preview before saving.
6. Use AskQuestion to ask which destination domain the new topology should
   live in (offer existing domains plus a "Create new domain..." option).
   If the user chooses a new domain, call `topology_create_domain(name=...)`
   first and use the returned `domain.id`.
7. Persist with `topology_create_from_plan(domain_id=<chosen>, plan_json=plan, name="<topology name>")`.
8. Confirm the save by listing topologies in that domain. If the user reports
   the new topology is not visible in the dropdown, call
   `topology_repair_legacy_visibility(domain_id, topology_id)`.

## Validate And Polish A Generated Topology

1. `topology_validate_topology(domain_id, topology_id)` checks missing link
   refs, duplicate IDs/names, orphan links, and broken group leaders.
2. `topology_clean_layout(domain_id, topology_id, group_by="role")` applies a
   deterministic grouped row layout.
3. `topology_auto_group(domain_id, topology_id, field="role")` creates manual
   groups when object metadata has enough matching values.

## Group Operations

- `topology_list_groups(domain_id, topology_id)` derives groups from object
  `groupId` fields.
- `topology_create_group(..., member_ids=[...])` stores group metadata on
  members using the same `groupId`, `groupLeaderId`, `groupName`, and
  `groupColor` fields as the web canvas.
- `topology_set_group_members` replaces membership.
- `topology_disband_group` removes group metadata from members.

## Share A Topology

Use `topology_call_tool`:

```json
{
  "tool_name": "topology_share_topology",
  "arguments": {
    "domain_id": "default",
    "topology_id": "abc123",
    "target_users": ["alice"],
    "permission": "edit"
  }
}
```

The API stores wire permission as `write`; tell users it is Edit access.

## Safe Wizard Dry-Run

Call wizard tools with the default `dry_run=true`.

Live execution requires:

- `dry_run=false`
- `execute=true`
- `confirm_phrase="I understand this is destructive on <device-name>"`

Do not invent the phrase. Ask the user to provide it if they really intend live execution.

