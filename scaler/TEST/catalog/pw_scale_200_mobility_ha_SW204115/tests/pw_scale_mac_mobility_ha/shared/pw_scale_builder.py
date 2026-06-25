#!/usr/bin/env python3
"""Deterministic service matrix and config builder for the 200 PW scale test.

This module is intentionally pure: it emits service rows and DNOS candidate
configuration text, but never opens SSH sessions and never commits anything.
The /TEST prerequisite gate validates and applies the generated chunks.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Sequence


DEFAULT_SCALE = 200
VLAN_ID_MIN = 1
VLAN_ID_MAX = 4094
DEFAULT_START_INNER = 3101
DEFAULT_ASN = 1234567
DEFAULT_RR_BGP_AS = 123
DEFAULT_LABEL_BLOCK_SIZE = 8
DEFAULT_PE4_SITE_BASE = 10000
DEFAULT_RR_SITE_BASE = 20000
DEFAULT_PE4_DEVICE = "YOR_CL_PE-4"
DEFAULT_RR_DEVICE = "RR-SA-2"
DEFAULT_PE4_LOOPBACK = "4.4.4.4"
DEFAULT_RR_LOOPBACK = "2.2.2.2"
DEFAULT_PE4_AC_PARENT = "ge100-18/0/0"
DEFAULT_RR_AC_PARENT = "bundle-100"
DEFAULT_PE4_OUTER = 219
DEFAULT_RR_SPIRANT_OUTER = 215
DEFAULT_RR_WIRE_OUTER = 4


@dataclass(frozen=True)
class ServiceRow:
    """One EVPN-SI VPLS service shared by PE-4 and RR-SA-2."""

    index: int
    name: str
    inner_vlan: int
    route_target: str
    evi: int
    pe4_device: str
    rr_device: str
    pe4_ac: str
    rr_ac: str
    pe4_outer_vlan: int
    rr_spirent_outer_vlan: int
    rr_wire_outer_vlan: int
    pe4_site_id: int
    rr_site_id: int
    pe4_rd: str
    rr_rd: str
    label_block_size: int
    label_block_ordinal: int
    label_block_budget_start: int
    label_block_budget_end: int
    pe4_src_mac: str
    rr_src_mac: str
    pe4_dst_mac: str
    rr_dst_mac: str
    pe4_stream_name: str
    rr_stream_name: str
    pe4_ownership_tag: str
    rr_ownership_tag: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def _mac(prefix: str, index: int) -> str:
    """Return a stable MAC with the service index encoded in the last two bytes."""

    if index < 1 or index > 4095:
        raise ValueError(f"index out of supported MAC range: {index}")
    return f"{prefix}:{(index >> 8) & 0x0f:02x}:{index & 0xff:02x}".lower()


def _assert_unique(rows: Sequence[ServiceRow], field_name: str) -> None:
    values = [getattr(row, field_name) for row in rows]
    if len(values) != len(set(values)):
        raise ValueError(f"service matrix has overlapping {field_name} values")


def _validate_service_matrix(rows: Sequence[ServiceRow]) -> None:
    """Fail fast if any generated service identity or dataplane key overlaps."""

    if not rows:
        return

    for row in rows:
        if not VLAN_ID_MIN <= row.inner_vlan <= VLAN_ID_MAX:
            raise ValueError(
                f"{row.name} inner VLAN {row.inner_vlan} is outside "
                f"{VLAN_ID_MIN}..{VLAN_ID_MAX}"
            )
        if row.label_block_size < 1:
            raise ValueError(f"{row.name} label_block_size must be positive")
        if row.label_block_budget_end - row.label_block_budget_start + 1 != row.label_block_size:
            raise ValueError(f"{row.name} label-block budget width mismatch")

    for field_name in (
        "index",
        "name",
        "inner_vlan",
        "route_target",
        "evi",
        "pe4_ac",
        "rr_ac",
        "pe4_rd",
        "rr_rd",
        "pe4_site_id",
        "rr_site_id",
        "label_block_ordinal",
        "pe4_stream_name",
        "rr_stream_name",
        "pe4_ownership_tag",
        "rr_ownership_tag",
    ):
        _assert_unique(rows, field_name)

    site_ids = [row.pe4_site_id for row in rows] + [row.rr_site_id for row in rows]
    if len(site_ids) != len(set(site_ids)):
        raise ValueError("PE-4 and RR-SA-2 site-id ranges overlap")

    macs = []
    for row in rows:
        macs.extend([row.pe4_src_mac, row.rr_src_mac, row.pe4_dst_mac, row.rr_dst_mac])
    if len(macs) != len(set(macs)):
        raise ValueError("service matrix has overlapping traffic MACs")

    block_ranges = [
        range(row.label_block_budget_start, row.label_block_budget_end + 1)
        for row in rows
    ]
    seen_slots = set()
    for row, block_range in zip(rows, block_ranges):
        overlap = seen_slots.intersection(block_range)
        if overlap:
            raise ValueError(f"{row.name} label-block budget overlaps slots {sorted(overlap)}")
        seen_slots.update(block_range)


def build_service_matrix(
    *,
    scale: int = DEFAULT_SCALE,
    offset: int = 0,
    asn: int = DEFAULT_ASN,
) -> List[ServiceRow]:
    """Build the deterministic 1:1 PE-4/RR-SA-2 service matrix.

    `offset` advances the inner-VLAN/RT window while preserving service indexes.
    Example: scale=200, offset=200 uses inner VLANs 3301-3500.
    """

    if scale < 1 or scale > DEFAULT_SCALE:
        raise ValueError(f"scale must be 1..{DEFAULT_SCALE}, got {scale}")
    if offset < 0:
        raise ValueError("offset must be >= 0")
    last_inner = DEFAULT_START_INNER + offset + scale - 1
    if last_inner > VLAN_ID_MAX:
        raise ValueError(
            f"inner VLAN window {DEFAULT_START_INNER + offset}..{last_inner} "
            f"exceeds VLAN max {VLAN_ID_MAX}"
        )

    rows: List[ServiceRow] = []
    for i in range(1, scale + 1):
        service_index = offset + i
        inner = DEFAULT_START_INNER + service_index - 1
        service_name = f"EVPN_PW_S{service_index:03d}"
        rt = f"{asn}:{inner}"
        pe4_site_id = DEFAULT_PE4_SITE_BASE + service_index
        rr_site_id = DEFAULT_RR_SITE_BASE + service_index
        label_block_ordinal = service_index - 1
        label_block_start = label_block_ordinal * DEFAULT_LABEL_BLOCK_SIZE
        label_block_end = label_block_start + DEFAULT_LABEL_BLOCK_SIZE - 1
        rows.append(
            ServiceRow(
                index=service_index,
                name=service_name,
                inner_vlan=inner,
                route_target=rt,
                evi=inner,
                pe4_device=DEFAULT_PE4_DEVICE,
                rr_device=DEFAULT_RR_DEVICE,
                pe4_ac=f"{DEFAULT_PE4_AC_PARENT}.{inner}",
                rr_ac=f"{DEFAULT_RR_AC_PARENT}.{inner}",
                pe4_outer_vlan=DEFAULT_PE4_OUTER,
                rr_spirent_outer_vlan=DEFAULT_RR_SPIRANT_OUTER,
                rr_wire_outer_vlan=DEFAULT_RR_WIRE_OUTER,
                pe4_site_id=pe4_site_id,
                rr_site_id=rr_site_id,
                pe4_rd=f"{DEFAULT_PE4_LOOPBACK}:{inner}",
                rr_rd=f"{DEFAULT_RR_LOOPBACK}:{inner}",
                label_block_size=DEFAULT_LABEL_BLOCK_SIZE,
                label_block_ordinal=label_block_ordinal,
                label_block_budget_start=label_block_start,
                label_block_budget_end=label_block_end,
                pe4_src_mac=_mac("00:de:ad:01", service_index),
                rr_src_mac=_mac("00:de:be:01", service_index),
                pe4_dst_mac=_mac("02:aa:ad:01", service_index),
                rr_dst_mac=_mac("02:aa:be:01", service_index),
                pe4_stream_name=f"pw_scale_pe4_s{service_index:03d}_i{inner}",
                rr_stream_name=f"pw_scale_rr_s{service_index:03d}_i{inner}",
                pe4_ownership_tag=f"[STC-PE4-S{service_index:03d}-i{inner}]",
                rr_ownership_tag=f"[STC-RRSA2-S{service_index:03d}-i{inner}]",
            )
        )
    _validate_service_matrix(rows)
    return rows


def rows_as_dicts(rows: Sequence[ServiceRow]) -> List[Dict[str, object]]:
    return [row.to_dict() for row in rows]


def build_expected_traffic(rows: Sequence[ServiceRow]) -> Dict[str, Dict[str, object]]:
    """Create recipe-compatible expected_traffic entries for all service rows."""

    expected: Dict[str, Dict[str, object]] = {}
    for row in rows:
        key = f"S{row.index:03d}_PE4"
        expected[key] = {
            "label": f"PE-4 ingress for {row.name}; RR-SA-2 must learn via PW",
            "via_device": row.pe4_device,
            "via_ac": row.pe4_ac,
            "encapsulation": "double-tagged",
            "outer_vlan": row.pe4_outer_vlan,
            "inner_vlan": row.inner_vlan,
            "src_mac_base": row.pe4_src_mac,
            "dst_mac": row.pe4_dst_mac,
            "dst_mac_role": "unknown unicast destination; must not be learned before the phase starts",
            "ownership_tag": row.pe4_ownership_tag,
            "spirent_flags": ["--vlan", str(row.pe4_outer_vlan), "--inner-vlan", str(row.inner_vlan)],
            "spirent_forbidden_flags": ["--no-qinq"],
            "expected_local": {"device": row.pe4_device, "flag": "L>", "instance": row.name},
            "expected_remote": {"device": row.rr_device, "flag": "v>", "instance": row.name},
            "frame_recipe_source": (
                f"dnos_dnaas_teach_plan(vlan={row.pe4_outer_vlan}, "
                f"dut={row.pe4_device}, inner_vlan={row.inner_vlan})"
            ),
            "verification_commands": {
                "local": f"show evpn mac-table instance {row.name} mac {row.pe4_src_mac} | no-more",
                "remote": f"show evpn mac-table instance {row.name} mac {row.pe4_src_mac} | no-more",
            },
        }

        key = f"S{row.index:03d}_RR"
        expected[key] = {
            "label": f"RR-SA-2 ingress for {row.name}; PE-4 must learn via PW",
            "via_device": row.rr_device,
            "via_ac": row.rr_ac,
            "encapsulation": "double-tagged",
            "outer_vlan": row.rr_wire_outer_vlan,
            "spirent_outer_vlan": row.rr_spirent_outer_vlan,
            "inner_vlan": row.inner_vlan,
            "src_mac_base": row.rr_src_mac,
            "dst_mac": row.rr_dst_mac,
            "dst_mac_role": "unknown unicast destination; must not be learned before the phase starts",
            "ownership_tag": row.rr_ownership_tag,
            "spirent_flags": [
                "--vlan",
                str(row.rr_spirent_outer_vlan),
                "--inner-vlan",
                str(row.inner_vlan),
            ],
            "spirent_forbidden_flags": ["--no-qinq"],
            "expected_local": {"device": row.rr_device, "flag": "L>", "instance": row.name},
            "expected_remote": {"device": row.pe4_device, "flag": "v>", "instance": row.name},
            "frame_recipe_source": (
                f"dnos_dnaas_teach_plan(vlan={row.rr_spirent_outer_vlan}, "
                f"dut={row.rr_device}, inner_vlan={row.inner_vlan})"
            ),
            "verification_commands": {
                "local": f"show evpn mac-table instance {row.name} mac {row.rr_src_mac} | no-more",
                "remote": f"show evpn mac-table instance {row.name} mac {row.rr_src_mac} | no-more",
            },
            "rewrite_note": "B-15 rewrites Spirent outer 215 to DUT wire outer 4; inner tag is preserved.",
        }
    return expected


def chunk_rows(rows: Sequence[ServiceRow], chunk_size: int) -> List[List[ServiceRow]]:
    if chunk_size < 1:
        raise ValueError("chunk_size must be >= 1")
    return [list(rows[i : i + chunk_size]) for i in range(0, len(rows), chunk_size)]


def render_device_config(
    device: str,
    rows: Iterable[ServiceRow],
    *,
    pe4_bgp_as: int = DEFAULT_ASN,
    rr_bgp_as: int = DEFAULT_RR_BGP_AS,
) -> str:
    """Render candidate DNOS config for one DUT.

    MAC teaching for this recipe must be PW-based. Keep route-targets only in
    `seamless-integration > protocols > bgp` as l2vpn-vpls RTs; native
    l2vpn-evpn RTs would advertise learned MACs as EVPN RT-2 instead of PW.
    """

    rows_list = list(rows)
    if not rows_list:
        return ""
    if device not in {DEFAULT_PE4_DEVICE, DEFAULT_RR_DEVICE}:
        raise ValueError(f"unsupported device for this recipe: {device}")
    bgp_as = pe4_bgp_as if device == DEFAULT_PE4_DEVICE else rr_bgp_as

    lines: List[str] = [
        f"! Generated by pw_scale_builder for {device}",
        f"! Services: {rows_list[0].name}..{rows_list[-1].name}",
    ]

    for row in rows_list:
        ac = row.pe4_ac if device == DEFAULT_PE4_DEVICE else row.rr_ac
        outer = row.pe4_outer_vlan if device == DEFAULT_PE4_DEVICE else row.rr_wire_outer_vlan
        lines.extend(
            [
                f"interfaces {ac}",
                " admin-state enabled",
                " l2-service enabled",
                f" vlan-tags outer-tag {outer} inner-tag {row.inner_vlan}",
                "top",
            ]
        )

    for row in rows_list:
        ac = row.pe4_ac if device == DEFAULT_PE4_DEVICE else row.rr_ac
        rd = row.pe4_rd if device == DEFAULT_PE4_DEVICE else row.rr_rd
        site_id = row.pe4_site_id if device == DEFAULT_PE4_DEVICE else row.rr_site_id
        lines.extend(
            [
                f"network-services evpn instance {row.name}",
                " protocols",
                f"  bgp {bgp_as}",
                f"   route-distinguisher {rd}",
                "top",
                f"network-services evpn instance {row.name}",
                " seamless-integration",
                "  protocols",
                "   bgp",
                f"    export-l2vpn-vpls route-target {row.route_target}",
                f"    import-l2vpn-vpls route-target {row.route_target}",
                "top",
                f"network-services evpn instance {row.name}",
                " seamless-integration",
                f"  label-block-size {row.label_block_size}",
                "  source-if lo0",
                f"  site-id {site_id} site-interface {ac}",
                "top",
                f"network-services evpn instance {row.name}",
                f" interface {ac}",
                "top",
            ]
        )

    return "\n".join(lines) + "\n"


def render_delete_config(device: str, rows: Iterable[ServiceRow]) -> str:
    rows_list = list(rows)
    if device not in {DEFAULT_PE4_DEVICE, DEFAULT_RR_DEVICE}:
        raise ValueError(f"unsupported device for this recipe: {device}")

    lines: List[str] = [f"! Cleanup generated by pw_scale_builder for {device}"]
    for row in rows_list:
        lines.append(f"no network-services evpn instance {row.name}")
    for row in rows_list:
        ac = row.pe4_ac if device == DEFAULT_PE4_DEVICE else row.rr_ac
        lines.append(f"no interfaces {ac}")
    return "\n".join(lines) + "\n"


def _self_test() -> None:
    rows = build_service_matrix()
    assert len(rows) == 200
    assert rows[0].inner_vlan == 3101
    assert rows[-1].inner_vlan == 3300
    assert rows[0].route_target == "1234567:3101"
    assert rows[-1].route_target == "1234567:3300"
    assert len({r.inner_vlan for r in rows}) == 200
    assert len({r.route_target for r in rows}) == 200
    assert len({r.pe4_site_id for r in rows} | {r.rr_site_id for r in rows}) == 400
    assert rows[0].label_block_budget_start == 0
    assert rows[-1].label_block_budget_end == 1599
    assert rows[0].pe4_ac == "ge100-18/0/0.3101"
    assert rows[0].rr_ac == "bundle-100.3101"
    expected = build_expected_traffic(rows[:1])
    assert expected["S001_PE4"]["src_mac_base"] != expected["S001_RR"]["src_mac_base"]
    assert expected["S001_PE4"]["dst_mac"] != "ff:ff:ff:ff:ff:ff"
    assert expected["S001_RR"]["dst_mac"] != "ff:ff:ff:ff:ff:ff"
    pe4_cfg = render_device_config(DEFAULT_PE4_DEVICE, rows[:1])
    rr_cfg = render_device_config(DEFAULT_RR_DEVICE, rows[:1])
    assert "vlan-tags outer-tag 219 inner-tag 3101" in pe4_cfg
    assert "vlan-tags outer-tag 4 inner-tag 3101" in rr_cfg
    assert "  bgp 1234567" in pe4_cfg
    assert "  bgp 123" in rr_cfg
    assert "export-l2vpn-evpn" not in pe4_cfg
    assert "import-l2vpn-evpn" not in pe4_cfg
    assert "export-l2vpn-evpn" not in rr_cfg
    assert "import-l2vpn-evpn" not in rr_cfg
    assert "export-l2vpn-vpls route-target 1234567:3101" in pe4_cfg
    assert "export-l2vpn-vpls route-target 1234567:3101" in rr_cfg
    offset_rows = build_service_matrix(scale=2, offset=200)
    assert offset_rows[0].name == "EVPN_PW_S201"
    assert offset_rows[0].inner_vlan == 3301
    assert offset_rows[0].pe4_src_mac != rows[0].pe4_src_mac


if __name__ == "__main__":
    _self_test()
    print("pw_scale_builder self-test passed")
