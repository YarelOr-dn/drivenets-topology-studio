#!/usr/bin/env python3
"""Static guards for Labels toggle control of link interface TBs."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)
    print(f"ok: {msg}")


def test_labels_button_controls_interface_tbs() -> None:
    toolbar = _read("topology-toolbar-setup.js")
    draw = _read("topology-draw.js")
    link_drawing = _read("topology-link-drawing.js")
    file_ops = _read("topology-file-ops.js")
    core = _read("topology.js")
    html = _read("index.html")

    _assert("window.syncLinkLabelsToolbarButton" in toolbar, "Labels toolbar state has a reusable sync helper")
    _assert("aria-pressed" in toolbar, "Labels button publishes toggle state")
    _assert("obj._interfaceLabel === true && !editor.showLinkTypeLabels" in draw, "main draw hides interface TBs when Labels is off")
    _assert("obj._interfaceLabel === true && !editor.showLinkTypeLabels" in file_ops, "PNG export follows Labels visibility for interface TBs")
    _assert("!(obj._interfaceLabel === true && !editor.showLinkTypeLabels)" in link_drawing, "hidden interface TBs do not leave link gaps")
    _assert("window.syncLinkLabelsToolbarButton(this)" in core, "topology load refreshes Labels button state")
    _assert("Show/hide canvas labels and interface TBs on links" in html, "topbar tooltip documents interface TB behavior")


def test_clearing_text_preserves_tb_object() -> None:
    text_editor = _read("topology-text-editor.js")
    drawing = _read("topology-canvas-drawing.js")

    _assert("_setTextValue: function(textObj, value)" in text_editor, "text edits use a preservation helper")
    _assert("textObj.text = nextValue" in text_editor, "empty text is stored on the existing TB")
    _assert("nextValue === ''" in text_editor, "empty TB state is tracked without deletion")
    _assert("objects.splice" not in text_editor, "text editor never removes topology objects")
    _assert("text.text == null ? 'Text' : String(text.text)" in drawing, "empty string does not fall back to placeholder text")


def test_dnaas_topologies_delete_through_normal_section_flow() -> None:
    serve = _read("serve.py")
    dnaas = _read("topology-dnaas-helpers.js")
    file_ops = _read("topology-file-ops.js")

    _assert('"id": "__dnaas"' in serve, "backend injects a per-user DNAAS section")
    _assert('"name": "DNAAS"' in serve, "DNAAS section keeps the expected UI name")
    _assert('"inside it can still be deleted normally."' in serve, "DNAAS builtin documents topology deletion")
    _assert("s.id === '__dnaas' || s.name === 'DNAAS'" in dnaas, "DNAAS helper resolves the built-in section")
    _assert("method: 'POST'" in file_ops and "/delete-file" in file_ops, "topology rows keep the normal delete endpoint")
    _assert("Delete \"${nameTxt}\"?" in file_ops, "delete flow keeps confirmation")


if __name__ == "__main__":
    test_labels_button_controls_interface_tbs()
    test_clearing_text_preserves_tb_object()
    test_dnaas_topologies_delete_through_normal_section_flow()
    print("All Labels/interface TB checks passed.")
