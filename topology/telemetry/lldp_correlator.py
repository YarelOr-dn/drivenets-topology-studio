"""LLDP correlation helpers shared by Generate Topology and Link Telemetry."""
from __future__ import annotations

import json
import sqlite3
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .config_parser import same_link_subnet
from .provider_base import DeviceTelemetry


# region agent log
def _agent_debug_log(hypothesis_id: str, message: str, data: dict) -> None:
    try:
        payload = {
            "sessionId": "92c7a8",
            "runId": "linktable-inner-vlan-pre",
            "hypothesisId": hypothesis_id,
            "location": "telemetry/lldp_correlator.py",
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with open("/home/dn/drivenets-topology-studio/.cursor/debug-92c7a8.log", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, separators=(",", ":")) + "\n")
    except Exception:
        pass
# endregion


def collect_lldp_edges_from_db(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Return LLDP edges from the topology-generator correlation DB."""
    cur = conn.cursor()
    out: List[Dict[str, Any]] = []
    cur.execute(
        "SELECT l.device_id, l.peer_hostname, l.local_interface, l.peer_interface, d2.id "
        "FROM lldp_rows l JOIN devices d2 ON lower(d2.hostname) = lower(l.peer_hostname) "
        "WHERE l.device_id != d2.id"
    )
    for dev_a, peer_h, lif, pif, dev_b in cur.fetchall():
        out.append(
            {
                "from": dev_a,
                "to": dev_b,
                "peer_hostname": peer_h,
                "local_interface": lif,
                "peer_interface": pif,
                "evidence": f"LLDP {peer_h}",
                "confidence": "verified",
            }
        )
    return out


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def correlate_link(
    link: Dict[str, Any],
    side_a: DeviceTelemetry,
    side_b: DeviceTelemetry,
    *,
    device_a: str = "",
    device_b: str = "",
) -> Dict[str, Any]:
    """Find the best LLDP interface match for one canvas link."""
    names_b = {_norm(device_b), _norm((link.get("deviceB") or {}).get("label")), _norm((link.get("deviceB") or {}).get("device_id"))}
    names_a = {_norm(device_a), _norm((link.get("deviceA") or {}).get("label")), _norm((link.get("deviceA") or {}).get("device_id"))}
    names_a.discard("")
    names_b.discard("")
    for edge in side_a.lldp:
        if _norm(edge.peer_hostname) in names_b:
            return {
                "ifA": edge.local_interface,
                "ifB": edge.peer_interface,
                "confidence": "verified",
                "evidence": edge.evidence or f"LLDP {edge.peer_hostname}",
                "source": "sideA",
            }
    for edge in side_b.lldp:
        if _norm(edge.peer_hostname) in names_a:
            return {
                "ifA": edge.peer_interface,
                "ifB": edge.local_interface,
                "confidence": "verified",
                "evidence": edge.evidence or f"LLDP {edge.peer_hostname}",
                "source": "sideB",
            }
    return {"ifA": "", "ifB": "", "confidence": "none", "evidence": "no LLDP match"}


def _row_name(row: Any) -> str:
    return str(getattr(row, "name", "") or "").strip()


def _parent(name: str) -> str:
    return name.split(".", 1)[0] if "." in name else name


def _kind_for(if_a: str, if_b: str, sub_a: str = "", sub_b: str = "") -> str:
    name = sub_a or sub_b or if_a or if_b
    parent = _parent(name)
    if parent.startswith("bundle-") and "." in name:
        return "sub-bundle"
    if parent.startswith("bundle-"):
        return "bundle"
    if "." in name:
        return "sub-interface"
    return "physical" if name else "none"


def _row_ip(row: Any) -> str:
    return str(getattr(row, "ip", "") or "").strip()


def _row_parent(row: Any) -> str:
    return str(getattr(row, "parent", "") or _parent(_row_name(row))).strip()


def _row_state(row: Any) -> Dict[str, str]:
    if not row:
        return {"admin": "", "oper": ""}
    return {
        "admin": str(getattr(row, "admin_state", "") or "").strip(),
        "oper": str(getattr(row, "oper_state", "") or "").strip(),
    }


def _row_outer_vlan(row: Any) -> str:
    return str(getattr(row, "outer_vlan", "") or "").strip()


def _row_inner_vlan(row: Any) -> str:
    return str(getattr(row, "inner_vlan", "") or "").strip()


def _subif_name(parent: str, outer_vlan: str, inner_vlan: str = "") -> str:
    if not parent or not outer_vlan:
        return ""
    return f"{parent}.{outer_vlan}{'.' + inner_vlan if inner_vlan else ''}"


def _logical_suffix(row: Any) -> str:
    name = _row_name(row)
    return name.split(".", 1)[1] if "." in name else ""


def _candidate_vlan_extra(row_a: Any = None, row_b: Any = None) -> Dict[str, str]:
    return {
        "outerVlanA": _row_outer_vlan(row_a),
        "innerVlanA": _row_inner_vlan(row_a),
        "outerVlanB": _row_outer_vlan(row_b),
        "innerVlanB": _row_inner_vlan(row_b),
    }


def _state_is_up(row: Any) -> bool:
    state = _row_state(row)
    return _norm(state.get("oper")) == "up"


def _correlation_status(row_a: Any, row_b: Any, *, identity_evidence: bool = False) -> str:
    if _state_is_up(row_a) and _state_is_up(row_b):
        return "verified-up"
    state_a = _row_state(row_a)
    state_b = _row_state(row_b)
    has_state = bool(state_a.get("admin") or state_a.get("oper") or state_b.get("admin") or state_b.get("oper"))
    if identity_evidence and has_state:
        return "expected-down"
    if identity_evidence:
        return "configured-only"
    return "inferred"


def _is_up(value: Any) -> bool:
    text = _norm(value)
    return bool(text and text not in {"down", "disabled", "idle", "inactive", "none", "not configured"})


def _protocol_evidence(row_a: Any, row_b: Any) -> Tuple[int, List[str]]:
    proto_a = getattr(row_a, "protocols", None)
    proto_b = getattr(row_b, "protocols", None)
    if not proto_a or not proto_b:
        return 0, []
    score = 0
    evidence: List[str] = []
    for name, weight in (("isis", 24), ("ospf", 24), ("ldp", 18)):
        state_a = getattr(proto_a, name, "")
        state_b = getattr(proto_b, name, "")
        if _is_up(state_a) and _is_up(state_b):
            score += weight
            evidence.append(f"{name.upper()} {state_a}/{state_b}")
    bgp_a = getattr(proto_a, "bgp_neighbors", []) or []
    bgp_b = getattr(proto_b, "bgp_neighbors", []) or []
    if bgp_a and bgp_b:
        score += 18
        states_a = ",".join(str(getattr(n, "state", "") or "configured") for n in bgp_a[:2])
        states_b = ",".join(str(getattr(n, "state", "") or "configured") for n in bgp_b[:2])
        evidence.append(f"BGP {states_a}/{states_b}")
    return score, evidence


def _service_key(row: Any) -> str:
    attachment = getattr(row, "attachment", None)
    identifiers = [
        getattr(attachment, "service_name", "") if attachment else "",
        getattr(attachment, "bridge_domain", "") if attachment else "",
        getattr(attachment, "vrf", "") if attachment else "",
        getattr(attachment, "evi", "") if attachment else "",
        getattr(row, "bridge_domain", ""),
    ]
    if not any(str(part or "").strip() for part in identifiers):
        return ""
    parts = [
        getattr(attachment, "kind", "") if attachment else "",
        *identifiers,
    ]
    return "|".join(str(part or "").strip().lower() for part in parts if str(part or "").strip())


def _has_direct_identity_evidence(row_a: Any, row_b: Any) -> bool:
    outer_a = str(getattr(row_a, "outer_vlan", "") or "")
    outer_b = str(getattr(row_b, "outer_vlan", "") or "")
    inner_a = str(getattr(row_a, "inner_vlan", "") or "")
    inner_b = str(getattr(row_b, "inner_vlan", "") or "")
    if outer_a and outer_a == outer_b and ((inner_a == inner_b) if (inner_a or inner_b) else True):
        return True
    if _logical_suffix(row_a) and _logical_suffix(row_a) == _logical_suffix(row_b):
        return True
    if _row_ip(row_a) and _row_ip(row_b) and same_link_subnet(_row_ip(row_a), _row_ip(row_b)):
        return True
    proto_a = getattr(row_a, "protocols", None)
    proto_b = getattr(row_b, "protocols", None)
    for name in ("isis", "ospf", "ldp"):
        if proto_a and proto_b and _is_up(getattr(proto_a, name, "")) and _is_up(getattr(proto_b, name, "")):
            return True
    service_a = _service_key(row_a)
    service_b = _service_key(row_b)
    return bool(service_a and service_a == service_b)


def _candidate(
    *,
    if_a: str,
    if_b: str,
    score: int,
    evidence: List[str],
    source: str,
    sub_a: str = "",
    sub_b: str = "",
    confidence: str = "inferred",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    logical_a = sub_a or if_a
    logical_b = sub_b or if_b
    out = {
        "ifA": if_a,
        "ifB": if_b,
        "logicalIfA": logical_a,
        "logicalIfB": logical_b,
        "parentA": _parent(if_a),
        "parentB": _parent(if_b),
        "subA": sub_a,
        "subB": sub_b,
        "kind": _kind_for(if_a, if_b, sub_a, sub_b),
        "confidence": confidence,
        "evidence": " + ".join([item for item in evidence if item]) or source,
        "source": source,
        "score": score,
    }
    if extra:
        out.update(extra)
    return out


def _dedupe_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    best: Dict[str, Dict[str, Any]] = {}
    for cand in candidates:
        key = (cand.get("ifA", ""), cand.get("ifB", ""), cand.get("subA", ""), cand.get("subB", ""))
        current = best.get(str(key))
        if not current or int(cand.get("score", 0)) > int(current.get("score", 0)):
            best[str(key)] = cand
    return sorted(best.values(), key=lambda item: int(item.get("score", 0)), reverse=True)


def _find_row(rows: List[Any], name: str = "") -> Optional[Any]:
    clean = str(name or "").strip()
    if not clean:
        return None
    for row in rows or []:
        if _row_name(row) == clean:
            return row
    return None


def _bundle_for_member(side: DeviceTelemetry, member_if: str) -> Tuple[Optional[Any], Optional[Any], str]:
    clean = str(member_if or "").strip()
    if not clean:
        return None, None, ""
    for source, attr in (("live LACP", "members"), ("configured LACP", "members_config")):
        for bundle in side.bundles or []:
            for member in getattr(bundle, attr, []) or []:
                if str(getattr(member, "interface", "") or "").strip() == clean:
                    return bundle, member, source
    return None, None, ""


def _member_state(member: Any, physical: Any) -> Dict[str, str]:
    state = _row_state(physical)
    if member:
        state.update({
            "role": str(getattr(member, "role", "") or "").strip(),
            "port": str(getattr(member, "port_state", "") or "").strip(),
            "protocol": str(getattr(member, "protocol_state", "") or "").strip(),
            "flags": str(getattr(member, "flags", "") or "").strip(),
        })
    return state


def _attachment_evidence(row_a: Any, row_b: Any) -> Tuple[int, List[str]]:
    evidence: List[str] = []
    score = 0
    for row, side in ((row_a, "A"), (row_b, "B")):
        if not row:
            continue
        attachment = getattr(row, "attachment", None)
        kind = str(getattr(attachment, "kind", "") or "").strip()
        service = str(
            getattr(attachment, "service_name", "")
            or getattr(attachment, "bridge_domain", "")
            or getattr(row, "bridge_domain", "")
            or ""
        ).strip()
        if kind and kind != "none":
            score += 10
            evidence.append(f"Side {side} service {kind}{' ' + service if service else ''}")
        elif service:
            score += 8
            evidence.append(f"Side {side} service {service}")
    return score, evidence


def _pair_score(row_a: Any, row_b: Any) -> Tuple[int, List[str]]:
    score = 0
    evidence: List[str] = []
    outer_a = str(getattr(row_a, "outer_vlan", "") or "")
    outer_b = str(getattr(row_b, "outer_vlan", "") or "")
    inner_a = str(getattr(row_a, "inner_vlan", "") or "")
    inner_b = str(getattr(row_b, "inner_vlan", "") or "")
    if outer_a and outer_a == outer_b and ((inner_a == inner_b) if (inner_a or inner_b) else True):
        score += 28
        evidence.append(f"VLAN {outer_a}{'/' + inner_a if inner_a else ''}")
    if inner_a and inner_b and inner_a == inner_b:
        score += 16
        evidence.append(f"inner VLAN {inner_a}")
    suffix_a = _logical_suffix(row_a)
    suffix_b = _logical_suffix(row_b)
    if suffix_a and suffix_a == suffix_b:
        score += 18
        evidence.append(f"logical unit {suffix_a}")
    if _row_ip(row_a) and _row_ip(row_b) and same_link_subnet(_row_ip(row_a), _row_ip(row_b)):
        score += 36
        evidence.append("same subnet")
    proto_score, proto_evidence = _protocol_evidence(row_a, row_b)
    if proto_score:
        score += proto_score
        evidence.extend(proto_evidence)
    attachment_score, attachment_evidence = _attachment_evidence(row_a, row_b)
    if attachment_score:
        score += attachment_score
        evidence.extend(attachment_evidence)
    return score, evidence


def _best_subif_pair_for_bundles(
    side_a: DeviceTelemetry,
    side_b: DeviceTelemetry,
    bundle_a: str,
    bundle_b: str,
) -> Tuple[Optional[Any], Optional[Any], int, List[str]]:
    best: Tuple[Optional[Any], Optional[Any], int, List[str]] = (None, None, 0, [])
    rows_a = [row for row in side_a.subifs or [] if _row_parent(row) == bundle_a]
    rows_b = [row for row in side_b.subifs or [] if _row_parent(row) == bundle_b]
    for row_a in rows_a:
        for row_b in rows_b:
            if not _has_direct_identity_evidence(row_a, row_b):
                continue
            score, evidence = _pair_score(row_a, row_b)
            if score > best[2]:
                best = (row_a, row_b, score, evidence)
    return best


def _best_subif_pair_for_parents(
    side_a: DeviceTelemetry,
    side_b: DeviceTelemetry,
    parent_a: str,
    parent_b: str,
) -> Tuple[Optional[Any], Optional[Any], int, List[str]]:
    """Return the VLAN-aware service pair under an LLDP physical pair."""
    best: Tuple[Optional[Any], Optional[Any], int, List[str]] = (None, None, 0, [])
    rows_a = [row for row in side_a.subifs or [] if _row_parent(row) == parent_a]
    rows_b = [row for row in side_b.subifs or [] if _row_parent(row) == parent_b]
    for row_a in rows_a:
        for row_b in rows_b:
            if not _has_direct_identity_evidence(row_a, row_b):
                continue
            score, evidence = _pair_score(row_a, row_b)
            if score > best[2]:
                best = (row_a, row_b, score, evidence)
    if best[2] > 0:
        return best

    # LLDP proves the physical pair. If only one side has service config, infer
    # the peer sub-interface name so the GUI fills VLAN-aware fields instead of
    # reverting to the bare physical row.
    for row_a in rows_a:
        outer = _row_outer_vlan(row_a)
        if outer:
            inferred_b = type(row_a)(
                name=_subif_name(parent_b, outer, _row_inner_vlan(row_a)),
                parent=parent_b,
                outer_vlan=outer,
                inner_vlan=_row_inner_vlan(row_a),
                description="inferred from LLDP physical pair and Side A VLAN",
            )
            return row_a, inferred_b, 42, [f"LLDP parent + VLAN {outer}{'/' + _row_inner_vlan(row_a) if _row_inner_vlan(row_a) else ''}"]
    for row_b in rows_b:
        outer = _row_outer_vlan(row_b)
        if outer:
            inferred_a = type(row_b)(
                name=_subif_name(parent_a, outer, _row_inner_vlan(row_b)),
                parent=parent_a,
                outer_vlan=outer,
                inner_vlan=_row_inner_vlan(row_b),
                description="inferred from LLDP physical pair and Side B VLAN",
            )
            return inferred_a, row_b, 42, [f"LLDP parent + VLAN {outer}{'/' + _row_inner_vlan(row_b) if _row_inner_vlan(row_b) else ''}"]
    return best


def _historical_lldp(link: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    previous = link.get("previousCorrelation") if isinstance(link.get("previousCorrelation"), dict) else {}
    if previous:
        link = {"linkDetails": {"live": {"correlation": previous}}}
    details = link.get("linkDetails") if isinstance(link.get("linkDetails"), dict) else {}
    live = details.get("live") if isinstance(details.get("live"), dict) else {}
    corr = live.get("correlation") or live.get("lldp") or {}
    if not isinstance(corr, dict):
        return None
    if corr.get("memberA") or corr.get("memberB"):
        return {
            "ifA": corr.get("memberA") or corr.get("ifA") or "",
            "ifB": corr.get("memberB") or corr.get("ifB") or "",
            "confidence": "inferred",
            "evidence": f"cached LLDP {corr.get('memberA') or corr.get('ifA') or ''}<->{corr.get('memberB') or corr.get('ifB') or ''}",
            "source": "cached-lldp",
        }
    if corr.get("source") in {"sideA", "sideB", "cached-lldp"} and (corr.get("ifA") or corr.get("ifB")):
        return {
            "ifA": corr.get("ifA") or "",
            "ifB": corr.get("ifB") or "",
            "confidence": "inferred",
            "evidence": f"cached LLDP {corr.get('ifA') or ''}<->{corr.get('ifB') or ''}",
            "source": "cached-lldp",
        }
    return None


def _lldp_candidates(
    lldp: Dict[str, Any],
    side_a: DeviceTelemetry,
    side_b: DeviceTelemetry,
) -> List[Dict[str, Any]]:
    if_a = lldp.get("ifA", "")
    if_b = lldp.get("ifB", "")
    physical_a = _find_row(side_a.physical, if_a)
    physical_b = _find_row(side_b.physical, if_b)
    base = {
        **_candidate(
            if_a=if_a,
            if_b=if_b,
            score=90,
            evidence=[lldp.get("evidence") or "LLDP"],
            source=lldp.get("source") or "lldp",
            confidence="verified",
            extra={
                "stateA": _row_state(physical_a),
                "stateB": _row_state(physical_b),
                "correlationStatus": _correlation_status(physical_a, physical_b, identity_evidence=True),
            },
        ),
        **lldp,
    }
    candidates = [base]

    best_a, best_b, sub_score, sub_evidence = _best_subif_pair_for_parents(side_a, side_b, if_a, if_b)
    if best_a and best_b and sub_score >= 18:
        candidates.append(_candidate(
            if_a=if_a,
            if_b=if_b,
            sub_a=_row_name(best_a),
            sub_b=_row_name(best_b),
            score=125 + sub_score,
            evidence=[lldp.get("evidence") or "LLDP"] + sub_evidence,
            source="lldp-physical-subif",
            confidence="verified" if lldp.get("source") != "cached-lldp" else "inferred",
            extra={
                "stateA": _row_state(best_a),
                "stateB": _row_state(best_b),
                "logicalReason": "LLDP physical pair promoted to VLAN sub-interface",
                "correlationStatus": _correlation_status(best_a, best_b, identity_evidence=True),
                **_candidate_vlan_extra(best_a, best_b),
            },
        ))

    bundle_a, member_a, source_a = _bundle_for_member(side_a, if_a)
    bundle_b, member_b, source_b = _bundle_for_member(side_b, if_b)
    # region agent log
    def _row_debug(row: Any) -> Dict[str, str]:
        return {
            "name": _row_name(row),
            "parent": _row_parent(row),
            "outer": _row_outer_vlan(row),
            "inner": _row_inner_vlan(row),
            "ip": _row_ip(row),
            "admin": _row_state(row).get("admin", ""),
            "oper": _row_state(row).get("oper", ""),
        }

    _agent_debug_log("H1,H2", "LLDP candidate promotion inputs", {
        "lldp": {"ifA": if_a, "ifB": if_b, "source": lldp.get("source", ""), "evidence": lldp.get("evidence", "")},
        "physicalA": _row_debug(physical_a),
        "physicalB": _row_debug(physical_b),
        "parentSubifsA": [_row_debug(row) for row in (side_a.subifs or []) if _row_parent(row) == if_a][:40],
        "parentSubifsB": [_row_debug(row) for row in (side_b.subifs or []) if _row_parent(row) == if_b][:40],
        "bestPhysicalSubifPair": {"score": sub_score, "evidence": sub_evidence, "a": _row_debug(best_a), "b": _row_debug(best_b)},
        "preBundleCandidates": candidates,
        "bundleA": _row_name(bundle_a),
        "bundleB": _row_name(bundle_b),
        "bundleSourceA": source_a,
        "bundleSourceB": source_b,
    })
    # endregion
    if not bundle_a and not bundle_b:
        return candidates

    logical_if_a = _row_name(bundle_a) if bundle_a else if_a
    logical_if_b = _row_name(bundle_b) if bundle_b else if_b
    promoted_evidence = [
        lldp.get("evidence") or "LLDP",
        f"member {if_a}->{logical_if_a} via {source_a}" if bundle_a else "",
        f"member {if_b}->{logical_if_b} via {source_b}" if bundle_b else "",
    ]
    status_row_a = bundle_a or physical_a
    status_row_b = bundle_b or physical_b
    promoted_extra = {
        "memberA": if_a,
        "memberB": if_b,
        "memberStateA": _member_state(member_a, physical_a),
        "memberStateB": _member_state(member_b, physical_b),
        "stateA": _row_state(status_row_a),
        "stateB": _row_state(status_row_b),
        "memberEvidence": " + ".join(item for item in promoted_evidence if item),
        "logicalReason": "LLDP physical member promoted to LACP bundle",
        "correlationStatus": _correlation_status(status_row_a, status_row_b, identity_evidence=True),
    }
    candidates.append(_candidate(
        if_a=logical_if_a,
        if_b=logical_if_b,
        score=140 if bundle_a and bundle_b else 122,
        evidence=promoted_evidence,
        source="lldp-lacp",
        confidence="verified" if lldp.get("source") != "cached-lldp" else "inferred",
        extra=promoted_extra,
    ))

    if bundle_a and bundle_b:
        best_a, best_b, sub_score, sub_evidence = _best_subif_pair_for_bundles(side_a, side_b, logical_if_a, logical_if_b)
        if best_a and best_b and sub_score >= 18:
            candidates.append(_candidate(
                if_a=logical_if_a,
                if_b=logical_if_b,
                sub_a=_row_name(best_a),
                sub_b=_row_name(best_b),
                score=150 + sub_score,
                evidence=promoted_evidence + sub_evidence,
                source="lldp-lacp-subbundle",
                confidence="verified" if lldp.get("source") != "cached-lldp" else "inferred",
                extra={
                    **promoted_extra,
                    "stateA": _row_state(best_a),
                    "stateB": _row_state(best_b),
                    "logicalReason": "LLDP member promoted to LACP sub-bundle by service/protocol evidence",
                    "correlationStatus": _correlation_status(best_a, best_b, identity_evidence=True),
                },
            ))
    # region agent log
    _agent_debug_log("H2", "LLDP final logical candidates", {
        "lldp": {"ifA": if_a, "ifB": if_b},
        "logicalIfA": logical_if_a,
        "logicalIfB": logical_if_b,
        "bundleSubifsA": [_row_debug(row) for row in (side_a.subifs or []) if _row_parent(row) == logical_if_a][:40],
        "bundleSubifsB": [_row_debug(row) for row in (side_b.subifs or []) if _row_parent(row) == logical_if_b][:40],
        "finalCandidates": candidates[:12],
    })
    # endregion
    return candidates


def _candidate_rows(side: DeviceTelemetry) -> List[Any]:
    return list(side.subifs or []) + list(side.bundles or []) + list(side.physical or [])


def _build_candidates(
    link: Dict[str, Any],
    side_a: DeviceTelemetry,
    side_b: DeviceTelemetry,
    *,
    device_a: str = "",
    device_b: str = "",
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    lldp = correlate_link(link, side_a, side_b, device_a=device_a, device_b=device_b)
    if lldp.get("confidence") != "none":
        candidates.extend(_lldp_candidates(lldp, side_a, side_b))
    else:
        cached_lldp = _historical_lldp(link)
        if cached_lldp:
            candidates.extend(_lldp_candidates(cached_lldp, side_a, side_b))

    for row_a in _candidate_rows(side_a):
        for row_b in _candidate_rows(side_b):
            name_a = _row_name(row_a)
            name_b = _row_name(row_b)
            sub_a = name_a if "." in name_a else ""
            sub_b = name_b if "." in name_b else ""
            if_a = _row_parent(row_a) if sub_a else name_a
            if_b = _row_parent(row_b) if sub_b else name_b
            if not _has_direct_identity_evidence(row_a, row_b):
                continue
            score, evidence = _pair_score(row_a, row_b)

            if score >= 18:
                candidates.append(_candidate(
                    if_a=if_a,
                    if_b=if_b,
                    sub_a=sub_a,
                    sub_b=sub_b,
                    score=score,
                    evidence=evidence,
                    source="scored",
                    extra={
                        "stateA": _row_state(row_a),
                        "stateB": _row_state(row_b),
                        "correlationStatus": _correlation_status(row_a, row_b, identity_evidence=True),
                    },
                ))

    hinted = _match_by_hints(link, side_a, side_b)
    if hinted:
        candidates.append({**hinted, "score": 12, "evidence": hinted.get("evidence") or "canvas hint"})

    return _dedupe_candidates(candidates)


def _find_subif(rows: List[Any], name: str = "", parent: str = "", outer_vlan: str = "", inner_vlan: str = "") -> Optional[Any]:
    for row in rows or []:
        if name and _row_name(row) == name:
            return row
    for row in rows or []:
        if parent and getattr(row, "parent", "") != parent:
            continue
        if outer_vlan and getattr(row, "outer_vlan", "") != outer_vlan:
            continue
        if inner_vlan and getattr(row, "inner_vlan", "") != inner_vlan:
            continue
        return row
    return None


def _match_by_vlan_ip(side_a: DeviceTelemetry, side_b: DeviceTelemetry) -> Optional[Dict[str, Any]]:
    for sub_a in side_a.subifs:
        for sub_b in side_b.subifs:
            vlan_match = bool(
                sub_a.outer_vlan
                and sub_a.outer_vlan == sub_b.outer_vlan
                and (
                    sub_a.inner_vlan == sub_b.inner_vlan
                    if (sub_a.inner_vlan or sub_b.inner_vlan)
                    else True
                )
            )
            ip_match = bool(sub_a.ip and sub_b.ip and same_link_subnet(sub_a.ip, sub_b.ip))
            if vlan_match or ip_match:
                return {
                    "ifA": sub_a.parent,
                    "ifB": sub_b.parent,
                    "parentA": sub_a.parent,
                    "parentB": sub_b.parent,
                    "subA": sub_a.name,
                    "subB": sub_b.name,
                    "kind": _kind_for(sub_a.parent, sub_b.parent, sub_a.name, sub_b.name),
                    "confidence": "inferred",
                    "evidence": "VLAN+IP" if vlan_match and ip_match else ("IP" if ip_match else "VLAN"),
                    "source": "config",
                }
    return None


def _match_by_hints(link: Dict[str, Any], side_a: DeviceTelemetry, side_b: DeviceTelemetry) -> Optional[Dict[str, Any]]:
    hint_a = str(link.get("hintIfA") or link.get("interfaceA") or link.get("device1Interface") or "").strip()
    hint_b = str(link.get("hintIfB") or link.get("interfaceB") or link.get("device2Interface") or "").strip()
    if not hint_a and not hint_b:
        return None
    sub_a = _find_subif(side_a.subifs, name=hint_a)
    sub_b = _find_subif(side_b.subifs, name=hint_b)
    if_a = sub_a.parent if sub_a else hint_a
    if_b = sub_b.parent if sub_b else hint_b
    return {
        "ifA": if_a,
        "ifB": if_b,
        "parentA": _parent(if_a),
        "parentB": _parent(if_b),
        "subA": _row_name(sub_a) if sub_a else "",
        "subB": _row_name(sub_b) if sub_b else "",
        "kind": _kind_for(if_a, if_b, _row_name(sub_a) if sub_a else "", _row_name(sub_b) if sub_b else ""),
        "confidence": "inferred",
        "evidence": "canvas hint",
        "source": "hint",
    }


def correlate_link_full(
    link: Dict[str, Any],
    side_a: DeviceTelemetry,
    side_b: DeviceTelemetry,
    *,
    device_a: str = "",
    device_b: str = "",
) -> Dict[str, Any]:
    """Correlate a canvas link and classify the actual live interface type."""
    candidates = _build_candidates(link, side_a, side_b, device_a=device_a, device_b=device_b)
    if candidates:
        best = dict(candidates[0])
        best["candidates"] = candidates[:10]
        return best
    return {
        "ifA": "",
        "ifB": "",
        "parentA": "",
        "parentB": "",
        "subA": "",
        "subB": "",
        "kind": "none",
        "confidence": "none",
        "evidence": "none",
        "source": "none",
        "score": 0,
        "candidates": [],
        "reason": "No live logical or physical link was detected between the selected devices",
    }


def correlate_canvas_edges(devices: Iterable[Dict[str, Any]], telemetry_by_device: Dict[str, DeviceTelemetry]) -> List[Dict[str, Any]]:
    """Return symmetric LLDP edges across a live canvas device set."""
    aliases: Dict[str, str] = {}
    for dev in devices:
        did = str(dev.get("device_id") or dev.get("id") or dev.get("label") or "").strip()
        if not did:
            continue
        for key in (did, dev.get("label"), dev.get("name"), dev.get("hostname")):
            if key:
                aliases[_norm(key)] = did
    edges: List[Dict[str, Any]] = []
    for dev_id, telemetry in telemetry_by_device.items():
        for edge in telemetry.lldp:
            peer_id = aliases.get(_norm(edge.peer_hostname))
            if not peer_id or peer_id == dev_id:
                continue
            edges.append({
                "from": dev_id,
                "to": peer_id,
                "local_interface": edge.local_interface,
                "peer_interface": edge.peer_interface,
                "peer_hostname": edge.peer_hostname,
                "evidence": edge.evidence,
                "confidence": edge.confidence,
            })
    return edges
