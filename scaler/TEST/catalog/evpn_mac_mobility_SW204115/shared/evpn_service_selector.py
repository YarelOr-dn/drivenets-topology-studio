#!/usr/bin/env python3
"""
EVPN service selection + RT completeness validation.

Purpose
-------
Before a /TEST run starts producing/checking traffic, the orchestrator must
prove that the EVPN instance it intends to drive can actually exchange the
routes the recipe expects. The classic failure (proven on YOR_PE-1 in
SESSION_2026-04-30_2102_PE-1_evpn-rt2-not-advertised.md) is an EVI that has
ONLY Seamless-Integration BGP-VPLS RTs but is missing the native EVPN RTs
(`export-l2vpn-evpn` / `import-l2vpn-evpn`). The MAC is learned and the AC
is up, but RT-2 is never advertised because the EVPN address-family has no
export RT for that EVI -- by configuration, not by bug.

This module:
  1. Inventories EVPN instances + their RT capabilities by parsing the
     device's `show config network-services evpn` output.
  2. Classifies each instance as one of:
        - EVPN_ONLY    -- has native EVPN RTs only (no SI VPLS RTs)
        - VPLS_SI_ONLY -- has SI VPLS RTs only (no native EVPN RTs)  <-- the bug pattern
        - BOTH_RTS     -- has both (full SI ELAN service)
        - NO_RTS       -- has neither (incomplete / decorative instance)
  3. Given a recipe's required capabilities, picks an action:
        - REUSE  -- an existing instance already satisfies the requirements
        - EXTEND -- an existing instance is close (e.g. has SI RTs, missing EVPN)
                    so we can add only the missing lines
        - CREATE -- no instance is close enough; build a new one
  4. For EXTEND, generates the SURGICAL fix snippet (just the missing lines)
     so the orchestrator can show it to the user and call dnos_atomic_commit.

This is consumed by `prerequisite_engine.check_prerequisites` via a new check
id `evpn_si_rt_complete`. The check reads `recipe["service_capabilities"]` to
know what the test needs. If the field is absent, the check is a soft WARN
(backward compatible -- never breaks existing recipes).

Recipe schema addition (optional, backward compatible)
------------------------------------------------------
    "service_capabilities": {
        "requires": ["native_evpn_rt", "seamless_integration_rt"],
        "preferred_instance": "EVPN_SI_VPLS_1"   // optional hint
    }

Capability tokens:
    native_evpn_rt          -> instance must have export/import-l2vpn-evpn
    seamless_integration_rt -> instance must have export/import-l2vpn-vpls
                                under seamless-integration subtree
    seamless_integration    -> instance must have a seamless-integration block
                                (with or without RTs -- caller usually pairs
                                this with seamless_integration_rt)

Author: 2026-04-30 (post-debug-dnos finding -- SESSION_2026-04-30_2102)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Capability tokens (single source of truth)
# ---------------------------------------------------------------------------

CAP_NATIVE_EVPN_RT = "native_evpn_rt"
CAP_SI_VPLS_RT = "seamless_integration_rt"
CAP_SI_BLOCK = "seamless_integration"

ALL_CAPABILITY_TOKENS = {
    CAP_NATIVE_EVPN_RT,
    CAP_SI_VPLS_RT,
    CAP_SI_BLOCK,
}


# ---------------------------------------------------------------------------
# Service classification
# ---------------------------------------------------------------------------

CLASS_BOTH_RTS = "BOTH_RTS"
CLASS_EVPN_ONLY = "EVPN_ONLY"
CLASS_VPLS_SI_ONLY = "VPLS_SI_ONLY"
CLASS_NO_RTS = "NO_RTS"


@dataclass
class EvpnInstanceInfo:
    """What we discovered about a single EVPN instance on the DUT."""

    name: str
    rd: str = ""
    has_si_block: bool = False
    has_native_evpn_export_rt: bool = False
    has_native_evpn_import_rt: bool = False
    has_si_vpls_export_rt: bool = False
    has_si_vpls_import_rt: bool = False
    native_evpn_rts: List[str] = field(default_factory=list)
    si_vpls_rts: List[str] = field(default_factory=list)
    raw_block: str = ""  # the full per-instance config text (for debugging)

    @property
    def has_native_evpn_rt(self) -> bool:
        return self.has_native_evpn_export_rt and self.has_native_evpn_import_rt

    @property
    def has_si_vpls_rt(self) -> bool:
        return self.has_si_vpls_export_rt and self.has_si_vpls_import_rt

    @property
    def classification(self) -> str:
        if self.has_native_evpn_rt and self.has_si_vpls_rt:
            return CLASS_BOTH_RTS
        if self.has_native_evpn_rt and not self.has_si_vpls_rt:
            return CLASS_EVPN_ONLY
        if self.has_si_vpls_rt and not self.has_native_evpn_rt:
            return CLASS_VPLS_SI_ONLY
        return CLASS_NO_RTS

    def supports(self, capability: str) -> bool:
        if capability == CAP_NATIVE_EVPN_RT:
            return self.has_native_evpn_rt
        if capability == CAP_SI_VPLS_RT:
            return self.has_si_vpls_rt
        if capability == CAP_SI_BLOCK:
            return self.has_si_block
        return False

    def missing_capabilities(self, required: List[str]) -> List[str]:
        return [c for c in required if not self.supports(c)]


# ---------------------------------------------------------------------------
# Decision result
# ---------------------------------------------------------------------------

DECISION_REUSE = "REUSE"
DECISION_EXTEND = "EXTEND"
DECISION_CREATE = "CREATE"
DECISION_NONE = "NONE"  # no requirements declared / nothing to do


@dataclass
class ServiceDecision:
    """The orchestrator presents this to the user before traffic starts."""

    action: str  # REUSE | EXTEND | CREATE | NONE
    instance_name: Optional[str] = None
    reason: str = ""
    missing_capabilities: List[str] = field(default_factory=list)
    fix_snippet: str = ""
    candidates_considered: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "instance_name": self.instance_name,
            "reason": self.reason,
            "missing_capabilities": list(self.missing_capabilities),
            "fix_snippet": self.fix_snippet,
            "candidates_considered": list(self.candidates_considered),
        }


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_INSTANCE_RE = re.compile(r"^\s*instance\s+(\S+)\s*$")
_RD_RE = re.compile(r"route-distinguisher\s+(\S+)")
_EXP_EVPN_RT_RE = re.compile(r"export-l2vpn-evpn\s+route-target\s+(\S+)")
_IMP_EVPN_RT_RE = re.compile(r"import-l2vpn-evpn\s+route-target\s+(\S+)")
_EXP_VPLS_RT_RE = re.compile(r"export-l2vpn-vpls\s+route-target\s+(\S+)")
_IMP_VPLS_RT_RE = re.compile(r"import-l2vpn-vpls\s+route-target\s+(\S+)")


def _split_evpn_instances(evpn_config: str) -> Dict[str, str]:
    """Split a `show config network-services evpn` blob into per-instance text.

    Robust to indent variations and to `flatten` output. Returns
    { instance_name: raw_text }. Lines are kept verbatim so the caller can
    detect where things sit relative to `seamless-integration` blocks.
    """
    instances: Dict[str, List[str]] = {}
    current: Optional[str] = None
    indent_at_open: Optional[int] = None

    for raw in evpn_config.splitlines():
        m = _INSTANCE_RE.match(raw)
        if m:
            current = m.group(1)
            indent_at_open = len(raw) - len(raw.lstrip(" "))
            instances.setdefault(current, []).append(raw)
            continue
        if current is None:
            continue
        if raw.strip() == "!":
            indent = len(raw) - len(raw.lstrip(" "))
            # `instance` block closes at the `!` whose indent matches the
            # one where the instance was opened.
            if indent_at_open is not None and indent <= indent_at_open:
                instances[current].append(raw)
                current = None
                indent_at_open = None
                continue
        instances[current].append(raw)

    return {name: "\n".join(lines) for name, lines in instances.items()}


def _parse_instance_block(name: str, block_text: str) -> EvpnInstanceInfo:
    """Extract structured RT/SI info from one EVPN instance config block."""
    info = EvpnInstanceInfo(name=name, raw_block=block_text)

    rd_match = _RD_RE.search(block_text)
    if rd_match:
        info.rd = rd_match.group(1)

    info.has_si_block = bool(re.search(r"\bseamless-integration\b", block_text))

    # Native EVPN RTs live under the top-level `protocols bgp <asn>` of the
    # instance, NOT under seamless-integration. We harvest both forms (export
    # and import) globally on the block -- the SI-vs-native distinction for
    # RT lines is by KEYWORD (l2vpn-evpn vs l2vpn-vpls), not by indentation.
    info.native_evpn_rts = sorted(set(_EXP_EVPN_RT_RE.findall(block_text) +
                                      _IMP_EVPN_RT_RE.findall(block_text)))
    info.has_native_evpn_export_rt = bool(_EXP_EVPN_RT_RE.search(block_text))
    info.has_native_evpn_import_rt = bool(_IMP_EVPN_RT_RE.search(block_text))

    info.si_vpls_rts = sorted(set(_EXP_VPLS_RT_RE.findall(block_text) +
                                  _IMP_VPLS_RT_RE.findall(block_text)))
    info.has_si_vpls_export_rt = bool(_EXP_VPLS_RT_RE.search(block_text))
    info.has_si_vpls_import_rt = bool(_IMP_VPLS_RT_RE.search(block_text))

    return info


def inventory_evpn_instances(evpn_config: str) -> Dict[str, EvpnInstanceInfo]:
    """Parse the full EVPN config and return { name: EvpnInstanceInfo }."""
    raw_blocks = _split_evpn_instances(evpn_config)
    return {name: _parse_instance_block(name, text) for name, text in raw_blocks.items()}


# ---------------------------------------------------------------------------
# Selection logic (REUSE / EXTEND / CREATE)
# ---------------------------------------------------------------------------

def _derive_si_rt_from_native(native_rts: List[str], fallback_asn: str) -> str:
    """Best-effort: if extending an EVPN_ONLY instance with SI VPLS RTs and the
    user did not specify a target RT, mirror the native EVPN RT value so the
    new VPLS RTs match the existing EVPN ones (common SI-coexistence pattern).
    Falls back to `<asn>:9999` if no native RT was found.
    """
    for rt in native_rts:
        if ":" in rt:
            return rt
    return f"{fallback_asn}:9999"


def _build_extend_snippet(
    info: EvpnInstanceInfo,
    missing: List[str],
    asn: str,
) -> str:
    """Build the SURGICAL config snippet that adds ONLY the missing RT lines.

    We do NOT regenerate the full instance. We do NOT touch existing RTs,
    interfaces, or transport config. The orchestrator can feed this directly
    to dnos_atomic_commit.
    """
    blocks: List[str] = []
    name = info.name

    # Decide which RT value to use for each side.
    target_evpn_rt = ""
    target_vpls_rt = ""
    if info.native_evpn_rts:
        target_evpn_rt = info.native_evpn_rts[0]
    if info.si_vpls_rts:
        target_vpls_rt = info.si_vpls_rts[0]

    # If we are adding native EVPN RTs and there is no EVPN RT yet,
    # mirror an existing SI VPLS RT (or fall back).
    if CAP_NATIVE_EVPN_RT in missing and not target_evpn_rt:
        target_evpn_rt = (target_vpls_rt
                          or _derive_si_rt_from_native(info.native_evpn_rts, asn))

    # If we are adding SI VPLS RTs and there is no SI VPLS RT yet,
    # mirror an existing native EVPN RT (or fall back).
    if CAP_SI_VPLS_RT in missing and not target_vpls_rt:
        target_vpls_rt = (target_evpn_rt
                          or _derive_si_rt_from_native(info.si_vpls_rts, asn))

    if CAP_NATIVE_EVPN_RT in missing:
        blocks.append(
            "network-services\n"
            "  evpn\n"
            f"    instance {name}\n"
            "      protocols\n"
            f"        bgp {asn}\n"
            f"          export-l2vpn-evpn route-target {target_evpn_rt}\n"
            f"          import-l2vpn-evpn route-target {target_evpn_rt}\n"
            "        !\n"
            "      !\n"
            "    !\n"
            "  !\n"
            "!"
        )

    if CAP_SI_VPLS_RT in missing:
        # SI VPLS RTs MUST live UNDER the seamless-integration subtree. If the
        # instance has no SI block at all, the snippet also opens the SI block
        # (label-block-size + source-if are reasonable safe defaults; the
        # operator can adjust before commit).
        if info.has_si_block:
            blocks.append(
                "network-services\n"
                "  evpn\n"
                f"    instance {name}\n"
                "      seamless-integration\n"
                "        protocols\n"
                "          bgp\n"
                f"            export-l2vpn-vpls route-target {target_vpls_rt}\n"
                f"            import-l2vpn-vpls route-target {target_vpls_rt}\n"
                "          !\n"
                "        !\n"
                "      !\n"
                "    !\n"
                "  !\n"
                "!"
            )
        else:
            blocks.append(
                "network-services\n"
                "  evpn\n"
                f"    instance {name}\n"
                "      seamless-integration\n"
                "        label-block-size 8\n"
                "        source-if lo0\n"
                "        protocols\n"
                "          bgp\n"
                f"            export-l2vpn-vpls route-target {target_vpls_rt}\n"
                f"            import-l2vpn-vpls route-target {target_vpls_rt}\n"
                "          !\n"
                "        !\n"
                "      !\n"
                "    !\n"
                "  !\n"
                "!"
            )

    if CAP_SI_BLOCK in missing and CAP_SI_VPLS_RT not in missing:
        # SI block missing but caller did not ask for VPLS RTs -- open an
        # empty SI block with safe defaults.
        blocks.append(
            "network-services\n"
            "  evpn\n"
            f"    instance {name}\n"
            "      seamless-integration\n"
            "        label-block-size 8\n"
            "        source-if lo0\n"
            "      !\n"
            "    !\n"
            "  !\n"
            "!"
        )

    return "\n".join(blocks).strip()


def select_service(
    instances: Dict[str, EvpnInstanceInfo],
    required_capabilities: List[str],
    preferred_instance: Optional[str] = None,
    asn: str = "65000",
) -> ServiceDecision:
    """Pick REUSE / EXTEND / CREATE for the given capability requirements.

    Order of preference:
      1. REUSE -- the preferred_instance (if given) already satisfies all caps.
      2. REUSE -- ANY instance already satisfies all caps.
      3. EXTEND -- the preferred_instance exists and is missing only RT lines.
      4. EXTEND -- the BEST partial match (fewest missing capabilities).
      5. CREATE -- no instance is close enough; build new.

    Capabilities not declared at all -> NONE (no decision needed).
    """
    if not required_capabilities:
        return ServiceDecision(action=DECISION_NONE,
                               reason="recipe declares no service_capabilities")

    unknown = [c for c in required_capabilities if c not in ALL_CAPABILITY_TOKENS]
    if unknown:
        return ServiceDecision(
            action=DECISION_NONE,
            reason=f"unknown capability tokens in recipe: {unknown}",
        )

    candidates = list(instances.keys())

    # --- 1+2. REUSE check -------------------------------------------------
    def _is_full_match(info: EvpnInstanceInfo) -> bool:
        return all(info.supports(c) for c in required_capabilities)

    if preferred_instance and preferred_instance in instances:
        if _is_full_match(instances[preferred_instance]):
            return ServiceDecision(
                action=DECISION_REUSE,
                instance_name=preferred_instance,
                reason="preferred instance already provides all required capabilities",
                candidates_considered=candidates,
            )

    for name, info in instances.items():
        if _is_full_match(info):
            return ServiceDecision(
                action=DECISION_REUSE,
                instance_name=name,
                reason=f"existing instance {name} provides all required capabilities "
                       f"({info.classification})",
                candidates_considered=candidates,
            )

    # --- 3+4. EXTEND check ------------------------------------------------
    # Score each instance by (a) how many caps it already has and
    # (b) whether it's the user-preferred one (tie-breaker).
    best: Optional[Tuple[int, bool, str, EvpnInstanceInfo]] = None
    for name, info in instances.items():
        already = sum(1 for c in required_capabilities if info.supports(c))
        if already == 0 and not info.has_si_block:
            # An instance with zero relevant config is essentially "blank";
            # don't favor it over CREATE.
            continue
        is_preferred = (preferred_instance == name)
        # Higher already-present count wins; ties broken by preferred flag.
        key = (already, is_preferred, name, info)
        if best is None or key > best:
            best = key

    if best is not None:
        already, _is_pref, name, info = best
        missing = info.missing_capabilities(required_capabilities)
        snippet = _build_extend_snippet(info, missing, asn=asn)
        return ServiceDecision(
            action=DECISION_EXTEND,
            instance_name=name,
            reason=(f"instance {name} is {info.classification}; "
                    f"missing {missing} -- surgical add only"),
            missing_capabilities=missing,
            fix_snippet=snippet,
            candidates_considered=candidates,
        )

    # --- 5. CREATE --------------------------------------------------------
    return ServiceDecision(
        action=DECISION_CREATE,
        instance_name=None,
        reason="no existing instance is close enough -- new EVPN instance required",
        missing_capabilities=list(required_capabilities),
        fix_snippet="",  # full instance generation is config_knowledge.py's job
        candidates_considered=candidates,
    )


# ---------------------------------------------------------------------------
# High-level entry point used by prerequisite_engine
# ---------------------------------------------------------------------------

def evaluate_evpn_service_for_recipe(
    run_show,
    device: str,
    recipe: Dict[str, Any],
    evpn_name_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """Live-device check that combines inventory + selection in one call.

    Returns dict that the prerequisite engine can render directly:
      {
        "status": "PASS" | "FAIL" | "WARN",
        "detail": "<short human reason>",
        "decision": ServiceDecision.as_dict(),
        "instances": { name: classification, ... },
      }

    Behavior contract:
      * If recipe lacks `service_capabilities`, returns WARN/skip-style row
        with status PASS so legacy recipes are NOT broken (backward compat).
      * If decision == REUSE  -> PASS
      * If decision == EXTEND -> FAIL with surgical fix_snippet attached
      * If decision == CREATE -> FAIL with reason and no fix_snippet
        (caller surfaces an AskQuestion to either pick an existing instance
        or generate a full create-new config via config_knowledge.py).
    """
    caps_block = recipe.get("service_capabilities") or {}
    required = list(caps_block.get("requires") or [])
    preferred = caps_block.get("preferred_instance") or evpn_name_hint

    if not required:
        return {
            "status": "PASS",
            "detail": "recipe declares no service_capabilities (skipped)",
            "decision": ServiceDecision(
                action=DECISION_NONE,
                reason="no service_capabilities in recipe",
            ).as_dict(),
            "instances": {},
        }

    try:
        evpn_cfg = run_show(device, "show config network-services evpn | no-more")
    except Exception as exc:
        return {
            "status": "WARN",
            "detail": f"could not fetch EVPN config: {exc}",
            "decision": ServiceDecision(
                action=DECISION_NONE,
                reason=f"run_show failed: {exc}",
            ).as_dict(),
            "instances": {},
        }

    asn = "65000"
    try:
        bgp_summary = run_show(device, "show bgp summary | no-more")
        m = re.search(r"local AS number\s+(\d+)", bgp_summary)
        if m:
            asn = m.group(1)
    except Exception:
        pass

    instances = inventory_evpn_instances(evpn_cfg)
    decision = select_service(
        instances=instances,
        required_capabilities=required,
        preferred_instance=preferred,
        asn=asn,
    )

    if decision.action == DECISION_REUSE:
        status = "PASS"
        detail = (f"REUSE {decision.instance_name}: "
                  f"{instances[decision.instance_name].classification}")
    elif decision.action == DECISION_EXTEND:
        status = "FAIL"
        detail = (f"EXTEND {decision.instance_name}: missing "
                  f"{decision.missing_capabilities} -- surgical fix snippet attached")
    elif decision.action == DECISION_CREATE:
        status = "FAIL"
        detail = ("CREATE: no existing instance covers required capabilities "
                  f"{required}")
    else:
        status = "WARN"
        detail = decision.reason or "no decision possible"

    return {
        "status": status,
        "detail": detail,
        "decision": decision.as_dict(),
        "instances": {name: info.classification for name, info in instances.items()},
    }
