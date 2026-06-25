#!/usr/bin/env python3
"""Static guards for the Link Telemetry frontend selector contract."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)
    print(f"ok: {msg}")


def test_dynamic_selector_uses_stable_candidate_keys() -> None:
    src = _read("topology-link-telemetry.js")
    _assert("function candidateKey(candidate = {})" in src, "candidateKey helper exists")
    _assert("liveCandidateKey" in src, "candidate select persists stable candidate key")
    _assert("liveAutoCandidateKey" in src, "auto selection is scoped to detected pair key")
    _assert("sameAutoCandidate && savedMatch" in src, "saved auto rows are reused for same pair")
    _assert("Number(link?.linkDetails?.liveCandidateIndex" in src, "index fallback remains for legacy state")
    _assert("!sameAutoCandidate && corrMatch && savedName !== corrSub" in src, "stale manual row is cleared when live candidate changes")


def test_dynamic_selector_accepts_interface_named_rows() -> None:
    src = _read("topology-link-telemetry.js")
    _assert("function rowName(row)" in src, "rowName helper exists")
    _assert("row?.name || row?.interface || row?.ifName" in src, "rowName accepts interface/ifName variants")
    _assert("{ ...row, name }" in src, "selectable rows normalize non-name telemetry rows")
    _assert("_candidateScopedRows(link, result, suffix)" in src, "Dynamic selector is scoped to correlated link candidates")
    _assert("return selectableRows({}, this._candidateScopedRows(link, result, suffix))" in src, "selector no longer offers every interface on the device")
    _assert("addCandidate(corr)" in src and "asRows(corr.candidates).forEach(addCandidate)" in src, "selector options come from detected direct/logical candidates")
    _assert("candidate[`outerVlan${sideKey}`]" in src, "selector fallback rows preserve candidate outer VLAN")
    _assert("candidate[`innerVlan${sideKey}`]" in src, "selector fallback rows preserve candidate inner VLAN")
    _assert("same bundle parent QinQ sub-interface" in src, "selector keeps QinQ subinterfaces under the detected bundle parent")
    _assert("qinqSiblingRows(sideA, mainA)" in src, "selected non-QinQ rows list same-parent QinQ alternatives instead of silently changing interfaces")
    _assert("Dynamic selector QinQ option state" in src and "compactMemberRows" in src, "debug log proves selector QinQ options and compact member mode")
    _assert("if (corrSub) {" in src and "inferredSub" in src, "auto-selection prefers inferred sub-interface candidates")
    _assert("vlan ? `VLAN ${vlan}`" in src, "selected interface detail shows VLAN stack")


def test_telemetry_table_pcap_uses_clicked_row_context() -> None:
    src = _read("topology-link-telemetry.js")
    _assert("parseRowAttr(tr?.dataset?.srcRow)" in src, "PCAP handler parses clicked row capture context")
    _assert("window.XrayPopup?.show" in src and "{ srcRow }" in src, "PCAP opens XRAY with srcRow")
    _assert("forceUserSelection: true" in src, "PCAP click pins the clicked telemetry row")
    _assert("_activate('static')" not in src, "telemetry row clicks do not jump modal tabs")


def test_link_toolbar_pcap_uses_dynamic_selection_context() -> None:
    telemetry_src = _read("topology-link-telemetry.js")
    toolbar_src = _read("topology-link-toolbar.js")
    xray_src = _read("topology-xray-popup.js")
    _assert("getXrayContextForLink(link" in telemetry_src, "LinkTelemetry exports XRAY context from Dynamic selections")
    _assert("srcRows = {" in telemetry_src and "device1: rowA" in telemetry_src and "device2: rowB" in telemetry_src, "XRAY context carries both POV-side rows")
    _assert("getXrayContextForLink?.(" in toolbar_src, "link toolbar asks telemetry for XRAY context")
    _assert("window.XrayPopup.show(editor, link, { x: centerX, y: bottomY, anchor: 'center' }, xrayContext)" in toolbar_src, "link toolbar passes telemetry context to XRAY")
    _assert("Use selected POV interface" in xray_src, "XRAY popup exposes selected-interface toggle")
    _assert("this._state.srcRows" in xray_src and "activeSrcRow" in xray_src, "XRAY switches selected source row with active POV")


def test_telemetry_table_has_pov_suboptions() -> None:
    src = _read("topology-link-telemetry.js")
    css = _read("styles.css")
    _assert("_povControls('A', sideA)" in src, "Side A renders POV sub-option controls")
    _assert("_povControls('B', sideB)" in src, "Side B renders POV sub-option controls")
    _assert("data-lt-pov-filter" in src, "POV filter buttons are wired")
    _assert("data-lt-section-kind" in src, "telemetry sections are filterable by interface kind")
    _assert(".lt-pov-suboptions" in css, "POV sub-option controls have styling")


def test_live_state_updates_link_table_fields() -> None:
    src = _read("topology-link-telemetry.js")
    _assert("persistSideState(link, 'A', stateRowA)" in src, "Side A live state persists to linkDetails")
    _assert("persistSideState(link, 'B', stateRowB)" in src, "Side B live state persists to linkDetails")
    _assert("updateInterfaceStateField(FIELD_MAP.interfaceA, stateRowA)" in src, "Side A interface field updates live state styling")
    _assert("updateInterfaceStateField(FIELD_MAP.interfaceB, stateRowB)" in src, "Side B interface field updates live state styling")


def test_logical_link_labels_and_member_evidence_render() -> None:
    src = _read("topology-link-telemetry.js")
    _assert("previousCorrelation" in src, "refresh sends cached correlation for down-but-expected links")
    _assert("logicalIfA" in src and "logicalIfB" in src, "frontend consumes resolved logical interface labels")
    _assert("_refreshInterfaceLabels(editor, link, logicalIfA, logicalIfB)" in src, "telemetry auto-fill refreshes canvas interface labels")
    _assert("Both POV live state" not in src, "Dynamic table removed duplicate POV live state row")
    _assert("Physical member" not in src and "Member LACP" not in src and "Member evidence" not in src, "Dynamic table omits duplicate member evidence rows")
    _assert("row.admin_state || corr[`state${suffix}`]?.admin" in src, "State row uses backend candidate state when selected row lacks state")
    _assert("function bundleMemberSummary(bundle, side)" in src, "live telemetry member summary joins LACP members with physical state")
    _assert("<th>Members</th>" not in src, "live telemetry table avoids a duplicate Members column")
    _assert("Members per side" not in src and "Members + physical state" not in src and "Members (config)" not in src and "Members (LACP)" not in src, "Dynamic table avoids duplicate bundle member rows")


def test_dynamic_table_renders_mtu_vlan_and_member_tables() -> None:
    src = _read("topology-link-telemetry.js")
    css = _read("styles.css")
    table_src = _read("topology-link-table.js")
    editor_src = _read("topology-link-editor.js")
    _assert("function rowMtu(row)" in src and "max_frame_size" in src, "MTU is normalized from live row and raw fallbacks")
    _assert("fill(FIELD_MAP.vlanModeA, 'vlan-tags'" in src, "live VLAN tags reveal outer/inner tag fields")
    _assert("POV summary" not in src, "Dynamic table no longer renders summary cards")
    _assert("Both POV live state" not in src, "Dynamic table avoids duplicate POV state summary rows")
    _assert("candidateLabel(candidate)" in src, "Detected link menu uses concise candidate labels")
    _assert("Outer VLAN" in src and "Inner VLAN" in src and "TPID" in src and "State / MTU" in src, "Dynamic table keeps VLAN and MTU visible in separate evidence rows")
    _assert("{ label: 'Service attachment', a: attachmentDetail(mainA), b: attachmentDetail(mainB) }" in src, "service attachment is visible in normal view")
    _assert("{ label: 'IP address', a: val(mainA.ip, 'not configured'), b: val(mainB.ip, 'not configured') }" in src, "IP address is visible in normal view")
    _assert("function rowVlanManipulation(row)" in src and "live config" in src, "VLAN manipulation is read from live config when present")
    _assert("qinqSummaryText(qinqSiblingRows(sideA, mainA))" in src and "Ingress manipulation" in src and "Egress manipulation" in src, "Dynamic table renders QinQ and manipulation as separate rows")
    _assert("function bundleMemberTable(bundle, side)" in src, "bundle member table helper exists")
    _assert("parentBundle(a, sideA, mainA)" in src, "sub-bundle selections resolve their parent bundle")
    _assert("lt-member-mini-table" in src, "live telemetry member mini table helper remains available outside Dynamic table")
    _assert("lt-dynamic-readonly-cell" in src and "lt-protocol-details" in src, "Dynamic evidence renders as text with expandable protocols")
    _assert("Service / Attachment" in src and "Members</th>" not in src, "Live telemetry table uses compact columns without a duplicate members column")
    _assert(".lt-protocol-details summary" in css and ".lt-dynamic-readonly-cell" in css, "Dynamic table uses subdued cells and collapsible protocol details")
    _assert("grid-template-columns: 140px" in css and "min-height: 36px" in css and "font-size: 12px" in css, "Dynamic table rows and columns are readable at larger size")
    _assert(".lt-member-mini-table" in css, "bundle member mini table has styling")
    _assert(".link-table-modal[data-width=\"wide\"] .lt-live-pov-grid" in css, "wide modal shows both telemetry POV panes")
    _assert("contentHeight > 380" in table_src and "modalContent.offsetHeight > 560" in table_src, "vertical resizing reveals advanced Link Table rows")
    _assert("contentHeight > 380" in editor_src and "modalContent.offsetHeight > TALL_THRESHOLD" in editor_src, "active modal resize helper also reveals tall-mode rows")
    _assert("max-height: none" in css and "min-height: 0" in css, "Link Table resize uses available modal height without blank stretch")


def test_link_table_reliability_guards() -> None:
    telemetry_src = _read("topology-link-telemetry.js")
    table_src = _read("topology-link-table.js")
    details_src = _read("topology-link-details.js")
    _assert("bindFieldListener(field, type, handler, key)" in table_src, "Link Table field handlers are bound through an idempotent helper")
    _assert("removeEventListener(type, field[storeKey])" in table_src, "repeat modal opens replace old handlers instead of stacking duplicates")
    _assert("ensureDynamicRoot(scroll)" in table_src, "Dynamic table root is recreated if a stale modal render removed it")
    _assert("_refreshSeq: new Map()" in telemetry_src and "_isFreshRefresh(editor, link, requestSignature, requestSeq)" in telemetry_src, "telemetry refreshes ignore stale async responses")
    _assert("_linkSignature(editor, link)" in telemetry_src and "_lastSignatureByLink" in telemetry_src, "cached telemetry is keyed by the current link endpoints")
    _assert("getCachedResult?.(link, editor)" in details_src, "modal open avoids cached rows from another topology with the same link id")
    _assert("renderLoading?.(link)" in details_src, "modal clears stale live rows while a fresh refresh is pending")


if __name__ == "__main__":
    test_dynamic_selector_uses_stable_candidate_keys()
    test_dynamic_selector_accepts_interface_named_rows()
    test_telemetry_table_pcap_uses_clicked_row_context()
    test_link_toolbar_pcap_uses_dynamic_selection_context()
    test_telemetry_table_has_pov_suboptions()
    test_live_state_updates_link_table_fields()
    test_logical_link_labels_and_member_evidence_render()
    test_dynamic_table_renders_mtu_vlan_and_member_tables()
    test_link_table_reliability_guards()
    print("All Link Telemetry frontend selector checks passed.")
