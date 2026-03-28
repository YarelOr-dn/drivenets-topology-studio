#!/usr/bin/env python3
"""Split scaler-gui.js.bak into modular files (see DEVELOPMENT_GUIDELINES.md)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "scaler-gui.js.bak"


def sl(lines, start, end):
    """1-based inclusive line slice."""
    return "".join(lines[start - 1 : end])


def wrap_module(filename, description, body_text, tail_after_assign=""):
    """body_text = property lines (4-space indent as in original object)."""
    return f"""/**
 * {description}
 * Source: split from scaler-gui.js.bak
 * @requires scaler-api.js
 * @requires scaler-gui.js (core)
 */
(function (G) {{
    'use strict';
    if (!G) {{
        console.error('[{filename}] ScalerGUI core not loaded');
        return;
    }}
    Object.assign(G, {{
{body_text}
    }});
{tail_after_assign}}})(window.ScalerGUI);
"""


def main():
    if not SRC.exists():
        raise SystemExit(f"Missing {SRC} -- copy scaler-gui.js to scaler-gui.js.bak first")
    lines = SRC.read_text(encoding="utf-8").splitlines(keepends=True)

    # Backup lines 1-14: banner + docblock; line 15 opens const ScalerGUI = {
    # Use lines 16-401 for object body (STATE through end of WizardController).
    core_parts = [
        sl(lines, 16, 401),
        sl(lines, 403, 1494),
        sl(lines, 1496, 1508),
        sl(lines, 1764, 1792),
        sl(lines, 1902, 2635),
        sl(lines, 11041, 11055),
    ]
    core_body = "".join(core_parts)
    core_file = f"""console.log('%c[ScalerGUI] core module loaded', 'color:#ff9800;font-weight:bold;font-size:12px');
/**
 * SCALER GUI -- core (state, WizardController, shared builders, panels, menu, notifications)
 * @requires scaler-api.js
 * @version 2.1.0-modular
 */
const ScalerGUI = {{
{core_body}}};
window.ScalerGUI = ScalerGUI;
"""
    (ROOT / "scaler-gui.js").write_text(core_file, encoding="utf-8")

    modules = [
        (
            "scaler-gui-history.js",
            "ScalerGUI: wizard history panel + commits panel",
            sl(lines, 9881, 10196),
            "",
        ),
        (
            "scaler-gui-devices.js",
            "ScalerGUI: canvas device list helpers, device manager, sync, quick-load, compare/ops",
            sl(lines, 1794, 1901)
            + sl(lines, 9583, 9879)
            + sl(lines, 11161, 11495)
            + sl(lines, 12635, 12808),
            "",
        ),
        (
            "scaler-gui-wizards-network.js",
            "ScalerGUI: interface, service, VRF, bridge-domain, multihoming wizards",
            sl(lines, 2748, 5468) + sl(lines, 6307, 6525),
            "",
        ),
        (
            "scaler-gui-wizards-security.js",
            "ScalerGUI: XRAY, FlowSpec, FlowSpec VPN, system, mirror",
            sl(lines, 2637, 2746)
            + sl(lines, 5470, 6052)
            + sl(lines, 12135, 12633),
            "",
        ),
        (
            "scaler-gui-wizards-routing.js",
            "ScalerGUI: routing policy, BGP, IGP",
            sl(lines, 6053, 12133),
            "",
        ),
        (
            "scaler-gui-progress.js",
            "ScalerGUI: showProgress (WebSocket) + _analyzeCommitError",
            sl(lines, 10198, 11039) + sl(lines, 11057, 11159),
            "",
        ),
        (
            "scaler-gui-upgrade.js",
            "ScalerGUI: upgrade banners, upgrade/scale/stag wizards, ScalerAPI.operation patches",
            sl(lines, 1510, 1762) + sl(lines, 6531, 9577),
            """
    if (typeof ScalerAPI !== 'undefined') {
        ScalerAPI.imageUpgrade = async function(params) {
            const response = await fetch(ScalerAPI._api('/api/operations/image-upgrade'), {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(params)
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(ScalerAPI._formatError(error.detail, 'Image upgrade failed'));
            }
            return response.json();
        };

        ScalerAPI.stagCheck = async function(params) {
            const response = await fetch(ScalerAPI._api('/api/operations/stag-check'), {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(params)
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(ScalerAPI._formatError(error.detail, 'Stag check failed'));
            }
            return response.json();
        };

        ScalerAPI.scaleUpDown = async function(params) {
            const response = await fetch(ScalerAPI._api('/api/operations/scale-updown'), {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(params)
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(ScalerAPI._formatError(error.detail, 'Scale operation failed'));
            }
            return response.json();
        };
    }
""",
        ),
    ]

    for fname, title, body, tail in modules:
        # indent body: original has 4 spaces; inside Object.assign we need 8 spaces for content
        indented = []
        for line in body.splitlines(keepends=True):
            if line.strip() == "":
                indented.append("        \n")
            elif line.startswith("    "):
                indented.append("    " + line)
            else:
                indented.append("        " + line)
        out = wrap_module(fname, title, "".join(indented), tail)
        (ROOT / fname).write_text(out, encoding="utf-8")

    (ROOT / "scaler-gui-init.js").write_text(
        """document.addEventListener('DOMContentLoaded', () => ScalerGUI.init());
console.log('[ScalerGUI] modular bundles loaded');
""",
        encoding="utf-8",
    )

    print("OK: wrote scaler-gui.js + 6 modules + scaler-gui-init.js")


if __name__ == "__main__":
    main()
