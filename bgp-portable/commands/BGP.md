---
description: Portable BGP peering via this DNAAS host ExaBGP (MCP-backed)
---
# /BGP - Portable (ExaBGP stays on the DNAAS host)

Orchestrate BGP peering from the **shared DNAAS-connected ExaBGP host**. Do not run ExaBGP or `bgp_tool.py` on this laptop. Native MCP only: `user-exabgp-mcp` (SSH tunnel to host `127.0.0.1:9304`).

## First skill load (mandatory)

If `~/.cursor/bgp_profile.json` is missing (or user said `/BGP setup` / `/BGP reset-profile`):

1. **AskQuestion** (plan mode; include an All option where lists apply):
   - Allocated global VLAN **range** (e.g. `2100-2199`)
   - **VLAN ID** for this peering (must sit in that range; reject otherwise)
   - Target **DUT** hostname
   - Inband **subnet**, **DUT IP**, **gateway** (do not assume `100.70.0.0/24`)
   - DNAAS **leaf** / **bundle** if more than one (or "discover")
2. `exabgp_session_lock` with `owner` = their username, `dut` = DUT.
3. `exabgp_onboard` with `execute` **false** (dry-run): `vlan`, `vlan_range`, `device`, optional `dnaas_leaf`/`bundle`.
4. If verdict `BD_AMBIGUOUS` or `NO_BD`: AskQuestion on discovered BD names. Never attach `g_mgmt_v999` unless they typed VLAN **999**.
5. AskQuestion confirm BD + sub-if from dry-run.
6. Persist `~/.cursor/bgp_profile.json` (chmod 0600) with keys: `vlan`, `vlan_range`, `bd_name`, `subnet`, `dut_ip`, `gateway`, `dut`, `dnaas_leaf`, `bundle`, `subif`, `onboarded_at`.
7. After confirm: `exabgp_onboard` `execute=true` then apply `dnos_deltas` via **host** `dnos_atomic_commit` (dry_run first) through the ExaBGP MCP path / suggested_next_call. Then `exabgp_start` only if no live session or they hold the lease **and** the current message is an explicit switch/stop. Then `exabgp_verify`.

Later `/BGP` with a profile skips the wizard unless `/BGP setup` or `/BGP reset-profile`.

## Native MCP

First choice: `exabgp_preflight`, `exabgp_onboard`, `exabgp_session_lock`, `exabgp_session_release`, `exabgp_start`, `exabgp_inject`, `exabgp_withdraw`, `exabgp_verify`, `exabgp_diagnose`, `exabgp_stop`.

Do not run the host ExaBGP CLI or the BGP learning-prune helper from this laptop. If MCP is disconnected: tell them to start `ssh -N -L 9304:127.0.0.1:9304 <exabgp-host>` and reload Cursor. CLI fallback only if MCP still down: SSH to the ExaBGP host and run `bgp_tool.py list` (read-only).

## Hard rules

- ExaBGP is single-instance on the host (`:179` + `/run/exabgp`). Never start a second session.
- Never stop/kill ExaBGP unless the **current** user message is an explicit stop **and** they hold `exabgp_session_lock`.
- `exabgp_start` requires `confirmed_no_live_session=true` or an explicit switch.
- VLAN outside the stored/asked range is rejected.

## Modes

| Input | Mode |
|---|---|
| `/BGP` | STATUS via `exabgp_verify` / lock status; if no profile, first-load wizard |
| `/BGP <Device>` | SETUP: profile + onboard + start/verify |
| `/BGP stop` | STOP only with lock + explicit phrase via `exabgp_stop` |
| `/BGP setup` / `/BGP reset-profile` | Re-run first-load AskQuestion |
