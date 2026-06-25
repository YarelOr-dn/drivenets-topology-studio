#!/usr/bin/env python3
"""Static guards for the New Topology + Create Domain wizard.

Pins regressions from 2026-05-05 (initial picker fixes) AND the
2026-05-12 inline-create-domain wizard:

1.  `_showNewTopologyDomainPicker` MUST follow the *app* theme (editor.darkMode
    or `body.dark-mode`), not the Topologies-menu inverted convention -- the
    picker is a modal overlay over the canvas, not a dropdown menu.

2.  The picker MUST expose a name input pre-populated with `Untitled` so the
    user has a save-friendly suggestion before the canvas opens.

3.  Picking a domain MUST flow that name (or a unique `Untitled N` derived
    from `/api/sections/<id>/topologies`) into `updateTopologyIndicator(...)`
    instead of the hard-coded `'untitled'` string.

4.  The wizard MUST host the create-domain step INLINE (no separate dialog,
    no jump to the full Manage Topology Domains panel). After successful
    create, the wizard MUST transition to a name-your-topology step with
    the new domain pre-selected. Cancelling after creating a new domain
    MUST keep the domain (already persisted) and surface a toast.

Also pins the `requestAnimationFrame(() => saveTip.style.opacity)` null-deref
crash that fired when the user moved the mouse out of the Quick Save button
during the same frame as the show-tooltip rAF.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)
    print(f"ok: {msg}")


def _picker_body() -> str:
    """Slice from the picker function header to the Save-to-domain comment."""
    src = _read("topology-file-ops.js")
    start = src.find("_showNewTopologyDomainPicker(editor)")
    assert start != -1, "picker function exists"
    end = src.find("// Save-to-domain picker", start)
    assert end != -1, "picker block end found"
    return src[start:end]


def test_quick_save_tooltip_does_not_crash_on_fast_mouseleave() -> None:
    src = _read("topology-file-ops.js")
    _assert(
        "const tipRef = saveTip;" in src,
        "Quick Save tooltip captures a local before scheduling the fade-in rAF",
    )
    _assert(
        "if (tipRef && tipRef.isConnected) tipRef.style.opacity = '1';" in src,
        "Quick Save tooltip fade-in is null-safe and DOM-attachment-safe",
    )


def test_new_topology_picker_follows_app_theme_not_menu_inverted() -> None:
    body = _picker_body()
    _assert(
        "FileOps._menuDark(editor)" not in body,
        "picker no longer uses inverted menu-dark convention for theming",
    )
    _assert(
        "editor.darkMode === 'boolean'" in body
        and "!!editor.darkMode" in body
        and "document.body.classList.contains('dark-mode')" in body,
        "picker reads the actual app theme (editor.darkMode / body.dark-mode)",
    )


def test_new_topology_picker_has_name_input_with_default_suggestion() -> None:
    body = _picker_body()
    _assert(
        'class="nt-name"' in body
        and 'placeholder="Untitled"' in body,
        "picker exposes a topology-name input with a sensible placeholder",
    )
    _assert(
        "const SUGGEST_BASE = 'Untitled';" in body
        and "nameInput.value = SUGGEST_BASE;" in body,
        "picker pre-fills the name input with the Untitled suggestion",
    )
    _assert(
        "nameInput.focus(); nameInput.select();" in body,
        "picker auto-focuses and selects the suggestion so users can type over it",
    )
    _assert(
        "if (e.key === 'Enter')" in body
        and "firstBtn.click();" in body,
        "Enter on the name input commits via the first domain row",
    )


def test_new_topology_picker_flows_name_into_indicator() -> None:
    body = _picker_body()
    _assert(
        "_resolveSuggestedName" in body
        and "/api/sections/${encodeURIComponent(sectionId)}/topologies" in body,
        "picker derives a unique Untitled N against the chosen domain's topologies",
    )
    _assert(
        "updateTopologyIndicator(suggested, sec.name, sec.color, sec.id)" in body,
        "domain click flows the suggested name (not 'untitled') into the indicator",
    )
    _assert(
        "updateTopologyIndicator('untitled', sec.name, sec.color, sec.id)" not in body,
        "no leftover hard-coded 'untitled' label on domain click",
    )
    _assert(
        "FileOps.updateTopologyIndicator(typed, '', null, null, null, { isGeneral: true });" in body,
        "No-domain skip path also seeds the user's typed name (General mode)",
    )


def test_new_topology_wizard_has_three_panes_with_breadcrumb() -> None:
    """The seamless flow lives in ONE overlay with three inline panes."""
    body = _picker_body()
    _assert(
        'class="nt-pane nt-pane-domain"' in body
        and 'class="nt-pane nt-pane-create-domain"' in body
        and 'class="nt-pane nt-pane-topology"' in body,
        "wizard renders all three panes inside the picker card",
    )
    _assert(
        'class="nt-breadcrumb"' in body
        and 'nt-crumb-domain' in body
        and 'nt-crumb-topology' in body,
        "wizard surfaces a Domain -> Topology breadcrumb",
    )
    _assert(
        "var(--dn-cyan, #00B4D8)" in body,
        "breadcrumb uses --dn-cyan brand variable for the active step",
    )
    _assert(
        "showPane('create-domain')" in body
        and "showPane('topology')" in body
        and "showPane('domain')" in body,
        "showPane() switches between the three wizard panes",
    )


def test_create_domain_button_no_longer_opens_manage_panel() -> None:
    """The 2026-05-12 fix swaps showManageSections() for inline pane swap."""
    body = _picker_body()
    _assert(
        "editor.showManageSections()" not in body,
        "Create new domain button does NOT pop the Manage panel anymore",
    )
    _assert(
        "newDomainBtn.onclick = () => showPane('create-domain');" in body,
        "Create new domain button switches to the inline create-domain pane",
    )
    _assert(
        "MutationObserver" not in body,
        "wizard no longer needs to observe an external panel's lifecycle",
    )


def test_create_domain_pane_posts_to_sections_via_authfetch() -> None:
    body = _picker_body()
    _assert(
        "FileOps._authFetch('/api/sections'," in body,
        "create-domain POST uses authFetch (multi-user JWT contract)",
    )
    _assert(
        "method: 'POST'" in body
        and "wizardState.selectedIcon" in body
        and "wizardState.selectedColor" in body,
        "create-domain POST sends name + selected icon + selected color",
    )
    _assert(
        "topology-domains:changed" in body
        and "domain-created" in body,
        "successful create-domain dispatches topology-domains:changed so the rest of the app rerenders",
    )


def test_topology_pane_pre_fills_and_commits_to_created_domain() -> None:
    body = _picker_body()
    _assert(
        "_enterTopologyPane(created)" in body,
        "successful domain create transitions into the topology-naming pane",
    )
    _assert(
        "wizardState.typedTopologyName" in body
        and "topologyNameInput.value = carry || SUGGEST_BASE" in body,
        "topology pane pre-fills with the user's earlier typed value (or Untitled)",
    )
    _assert(
        "_commitTopologyToCreatedDomain" in body
        and "FileOps.updateTopologyIndicator(suggested, sec.name, sec.color, sec.id)"
        in body,
        "topology pane Create button commits via updateTopologyIndicator on the new domain",
    )


def test_cancel_after_domain_create_keeps_domain_with_toast() -> None:
    body = _picker_body()
    _assert(
        "wizardState.createdDomain" in body
        and "wizardState.topologyCommitted" in body,
        "wizardState tracks both 'domain created' and 'topology committed' flags",
    )
    _assert(
        "Add a topology when you're ready" in body,
        "cancel-mid-flow toast tells the user the new domain persists",
    )


def test_zero_section_onboarding_starts_in_create_domain_pane() -> None:
    body = _picker_body()
    _assert(
        "_ownedSections" in body and "!s.builtin" in body,
        "owned-sections helper filters out built-in / shared-with-me domains",
    )
    _assert(
        "if (_ownedSections().length === 0) {" in body
        and "showPane('create-domain');" in body,
        "first-time users with no owned domains open straight into the create-domain pane",
    )


def test_keyboard_polish_enter_on_each_input() -> None:
    body = _picker_body()
    _assert(
        "domainNameInput.addEventListener('keydown'" in body
        and "cdCreateBtn.click()" in body,
        "Enter on the domain-name input triggers Create domain",
    )
    _assert(
        "topologyNameInput.addEventListener('keydown'" in body
        and "tpCreateBtn.click()" in body,
        "Enter on the topology-name input triggers Create topology",
    )


def test_index_html_topology_file_ops_cache_buster_bumped() -> None:
    src = _read("index.html")
    _assert(
        'topology-file-ops.js?v=20260512e-new-topo-flow' in src,
        "index.html bumps topology-file-ops.js cache-buster for the seamless wizard",
    )


def main() -> int:
    test_quick_save_tooltip_does_not_crash_on_fast_mouseleave()
    test_new_topology_picker_follows_app_theme_not_menu_inverted()
    test_new_topology_picker_has_name_input_with_default_suggestion()
    test_new_topology_picker_flows_name_into_indicator()
    test_new_topology_wizard_has_three_panes_with_breadcrumb()
    test_create_domain_button_no_longer_opens_manage_panel()
    test_create_domain_pane_posts_to_sections_via_authfetch()
    test_topology_pane_pre_fills_and_commits_to_created_domain()
    test_cancel_after_domain_create_keeps_domain_with_toast()
    test_zero_section_onboarding_starts_in_create_domain_pane()
    test_keyboard_polish_enter_on_each_input()
    test_index_html_topology_file_ops_cache_buster_bumped()
    print("All New Topology + Create Domain wizard unit checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
