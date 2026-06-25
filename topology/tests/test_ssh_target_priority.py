"""Static regression checks for SSH target precedence.

Run:
    python3 topology/tests/test_ssh_target_priority.py
"""
from __future__ import annotations

import os
import re


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOPO = os.path.join(REPO_ROOT, "topology")


def _read(rel: str) -> str:
    with open(os.path.join(TOPO, rel), "r", encoding="utf-8") as f:
        return f.read()


def _assert(cond: object, label: str) -> None:
    if cond:
        print(f"  ok: {label}")
        return
    print(f"  FAIL: {label}")
    raise SystemExit(1)


def test_stack_dialog_prefers_ip_fallbacks() -> None:
    print("\n=== Stack dialog SSH target priority")
    helper = _read("topology-ssh-target.js")
    index = _read("index.html")
    _assert("window.TopologySshTarget" in helper, "shared target helper exists")
    _assert("topology-ssh-target.js" in index, "shared target helper is loaded by index.html")
    _assert("cfg.hostBackup" in helper and "cfg.host" in helper, "shared helper includes hostBackup and host")
    preferred = re.search(r"const preferredIp = \[(?P<body>[\s\S]*?)\]\.map", helper)
    _assert(preferred is not None, "located shared preferred IP candidates")
    preferred_lines = [line.strip().rstrip(",") for line in preferred.group("body").splitlines() if line.strip()]
    _assert(
        preferred_lines.index("cfg.hostBackup") < preferred_lines.index("cfg.host"),
        "hostBackup IP is considered before host",
    )
    _assert("isDisplayName" in helper, "display hostnames are filtered from non-IP fallback")
    src = _read("topology-stack-dialog.js")
    _assert("_pickSshTarget(device, serial)" in src, "stack dialog has target picker")
    _assert("window.TopologySshTarget.pick(device, { serial }).host" in src, "stack dialog uses shared helper")


def test_git_commit_prefers_shared_picker() -> None:
    print("\n=== Git Commit SSH target priority")
    src = _read("topology-selection-popups.js")
    _assert("_pickSshTarget(device, serial, sshConfig)" in src, "selection popup has target picker")
    _assert("window.TopologySshTarget.pick(device, { serial, sshConfig }).host" in src, "Git Commit picker delegates to shared helper")
    _assert(
        "const host = SelectionPopups._pickSshTarget(device, serial, sshConfig);" in src,
        "Git Commit uses shared picker instead of sshConfig.host || serial",
    )
    _assert("const host = sshConfig?.host || serial;" not in src, "old hostname-first Git Commit path removed")


def test_terminal_prefers_shared_picker() -> None:
    print("\n=== Terminal SSH target priority")
    src = _read("topology-object-detection.js")
    _assert("_pickSshTarget(device)" in src, "terminal path has target picker")
    _assert("window.TopologySshTarget.pick(device)" in src, "terminal picker delegates to shared helper")
    _assert("const pickedTarget = this._pickSshTarget(device);" in src, "terminal launch uses target picker")
    _assert("let host = sshConfig._userSavedHost || sshConfig.host || '';" not in src, "old hostname-first terminal path removed")


def test_any_cluster_active_ncc_wins() -> None:
    print("\n=== Any cluster active NCC target priority")
    helper = _read("topology-ssh-target.js")
    _assert("looksLikeNccTarget" in helper, "shared helper can identify active NCC hostnames")
    active_block = re.search(
        r"const activeNccHost = \[(?P<body>[\s\S]*?)\]\.map",
        helper,
    )
    _assert(active_block is not None, "active NCC candidate block exists")
    active_body = active_block.group("body")
    _assert("cfg._activeNccHost" in active_body, "_activeNccHost is an active NCC candidate")
    _assert("cfg._virshInfo?.activeNcc" in active_body, "virshInfo.activeNcc is an active NCC candidate")
    _assert("device?._monitorContext?.active_ncc_vm" in active_body, "monitor active_ncc_vm is an active NCC candidate")
    cluster_return = helper.index("if (isCluster && activeNccHost)")
    preferred_ip = helper.index("const preferredIp = [")
    host_fallback = helper.index("const host = preferredIp || [")
    _assert(cluster_return < preferred_ip < host_fallback, "cluster returns active NCC before IP and host/serial fallbacks")
    _assert("source: 'active-ncc-host'" in helper, "active NCC target has explicit source tag")
    _assert("isCluster ? '' : cfg._activeNccIp" in helper, "cluster skips cached active NCC IP in preferred IP candidates")
    _assert("isCluster ? '' : cfg._nccMgmtIp" in helper, "cluster skips cached NCC mgmt IP in preferred IP candidates")
    _assert("const lockedSnHost = [userSavedHost, snHost]" in helper, "cluster lock excludes chassis deviceSerial")
    _assert("YOR_CL_PE-4" not in helper, "shared picker is not PE-4-specific")
    _assert("WDY19C7M00013-P3" not in helper, "shared picker is not tied to one chassis serial")


def test_git_commit_fallback_reads_absolute_file_first() -> None:
    print("\n=== Git Commit backend fallback")
    src = _read("discovery_api.py")
    _assert("('/.gitcommit', '.gitcommit')" in src, "fallback tries absolute /.gitcommit before relative path")
    _assert("cat {git_path}" in src, "fallback iterates git commit paths")


if __name__ == "__main__":
    test_stack_dialog_prefers_ip_fallbacks()
    test_git_commit_prefers_shared_picker()
    test_terminal_prefers_shared_picker()
    test_any_cluster_active_ncc_wins()
    test_git_commit_fallback_reads_absolute_file_first()
    print("\nAll SSH target precedence regression checks passed")
