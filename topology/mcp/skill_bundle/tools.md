# Topology MCP Tools

## First-Class Tools

- `topology_health()` -- verify auth and server health.
- `topology_list_tools()` -- list every registered v1 tool and schema.
- `topology_call_tool(tool_name, arguments)` -- call any registered `topology_*` tool.
- `topology_list_domains(include_shared=true)` -- list own and shared domains.
- `topology_list_topologies(domain_id="", include_shared=true)` -- list topologies.
- `topology_get_topology(domain_id, topology_id)` -- fetch full topology state.
- `topology_create_domain(name, description="")` -- create a domain.
- `topology_create_topology(domain_id, name, state_json={})` -- create a topology.
- `topology_save_topology(domain_id, topology_id, name, state_json)` -- save topology JSON.
- `topology_add_device(domain_id, topology_id, properties)` -- add a canvas device.
- `topology_batch_update_objects(domain_id, topology_id, patches)` -- update several objects in one save.
- `topology_summarize_topology(...)` and `topology_validate_topology(...)` -- check object/link/group integrity.
- `topology_list_groups`, `topology_create_group`, `topology_set_group_members`, `topology_disband_group`, `topology_auto_group` -- operate manual object groups.
- `topology_create_mesh(domain_id, name, device_count, device_type="PE", mesh_type="full")` -- generate a mesh topology.
- `topology_clean_layout(domain_id, topology_id, ...)` -- deterministic row layout for imported/generated topologies.
- `topology_plan_from_network_mapper(network_mapper_json, ...)` -- preview a topology from already-fetched Network Mapper JSON.
- `topology_plan_from_dnos_json(dnos_json, ...)` -- preview a topology from already-fetched dnos-config/DNOS JSON.
- `topology_plan_from_image(image_extraction_json, name="Image Import", auto_group_by="", auto_layout=False)` -- preview a topology that the agent extracted from an image attached in chat. The MCP itself never sees the image; the agent reads the diagram with vision and emits `{"devices": [...], "links": [...], "groups": [...], "shapes": [...], "texts": [...]}` with image-derived X/Y and visible styling. Defaults preserve those positions and styles; pass `auto_layout=True` only when no usable coordinates were extracted. Device style fields include `visualStyle`/`deviceStyle`, `color`, `radius`, `rotation`, `labelColor`, and `labelSize`; link style fields include `style`/`lineStyle`, `color`, and `width`.
- `topology_create_from_plan(domain_id, plan_json, name="")` -- save an accepted preview plan.
- `topology_run_image_upgrade(...)` -- dry-run image upgrade wizard integration.

## Full Registry Via `topology_call_tool`

Use `topology_list_tools()` for the current registry. Categories:

- Read-only inspect: `topology_get_topology_metadata`, `topology_search`.
- Domain CRUD: `topology_rename_domain`, `topology_delete_domain`, `topology_share_domain`, `topology_unshare_domain`.
- Topology CRUD: `topology_delete_topology`, `topology_share_topology`, `topology_unshare_topology`.
- Object CRUD: `topology_add_object`, `topology_update_object`, `topology_move_object`, `topology_delete_object`, plus typed device/link/shape/text-box helpers.
- Batch and groups: `topology_batch_update_objects`, `topology_patch_objects`, `topology_list_groups`, `topology_create_group`, `topology_update_group`, `topology_set_group_members`, `topology_delete_group`, `topology_disband_group`, `topology_auto_group`.
- Validation: `topology_validate_topology`, `topology_summarize_topology`.
- Import previews: `topology_plan_from_network_mapper`, `topology_plan_from_dnos_json`, `topology_plan_from_image`, `topology_create_from_plan`.
- Bulk creation: `topology_create_from_spec`, `topology_create_mesh`, `topology_create_chain`, `topology_create_star`, `topology_duplicate_topology`, `topology_apply_layout`, `topology_clean_layout`.
- Discovery: `topology_discovery_trigger`, `topology_discovery_status`, `topology_discovery_results`, `topology_discovery_accept`.
- Wizard dry-runs: `topology_run_image_upgrade`, `topology_run_config_push`, `topology_run_bul_links`.

