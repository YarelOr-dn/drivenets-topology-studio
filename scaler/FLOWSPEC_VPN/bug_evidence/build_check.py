#!/usr/bin/env python3
"""
Build-vs-Fix Checker Tool

Checks whether a device's running build includes the fix for a given bug by:
1. Getting the device's exact build commit from /.gitcommit
2. Finding the fix commit from VERIFY_RECIPES.md, git log, or Jira
3. Running git merge-base --is-ancestor to determine ancestry

Usage:
    python3 build_check.py --device PE-1 --bug SW-238966
    python3 build_check.py --device PE-1 --all-recipes
    python3 build_check.py --commit abc123-branch --bug SW-238966

Returns: FIX IN BUILD | FIX NOT IN BUILD | LIKELY IN BUILD | UNKNOWN | SKIP
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time

import paramiko

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RECIPES_PATH = os.path.join(SCRIPT_DIR, "VERIFY_RECIPES.md")
CHEETAH_REPO = os.path.expanduser("~/cheetah_26_1")
DEVICES_JSON = os.path.expanduser("~/SCALER/db/devices.json")

# Regex for fix commit SHAs (full 40-char or short 7-12 char)
SHA_FULL_RE = re.compile(r"[0-9a-fA-F]{40}")
SHA_SHORT_RE = re.compile(r"\b([0-9a-fA-F]{7,12})\b")
SKIP_PATTERNS = ("not yet fixed", "open bug", "no fix")
VERSION_RE = re.compile(r"DNOS\s+\[([\d.]+)\].*build\s+\[([^\]]+)\]")


def resolve_device_ip(device_name: str) -> str:
    """Resolve device name to IP. Returns device_name if it looks like an IP."""
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", device_name):
        return device_name
    try:
        with open(DEVICES_JSON) as f:
            data = json.load(f)
        for d in data.get("devices", []):
            host = d.get("hostname", "")
            if device_name.upper() in host.upper() or host.upper() in device_name.upper():
                return d.get("ip", device_name)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return device_name


def get_device_credentials(device_ip: str) -> tuple:
    """Get username/password for device. Default dnroot/dnroot."""
    try:
        with open(DEVICES_JSON) as f:
            data = json.load(f)
        for d in data.get("devices", []):
            if d.get("ip") == device_ip:
                user = d.get("username", "dnroot")
                pw = d.get("password", "dnroot")
                if pw:
                    try:
                        decoded = base64.b64decode(pw).decode(errors="replace")
                        if decoded.isprintable() and len(decoded) < 50:
                            pw = decoded
                    except Exception:
                        pass
                return user, pw or "dnroot"
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return "dnroot", "dnroot"


def get_device_commit(device: str, use_commit_arg: str = None) -> dict:
    """
    Get device build commit and version.
    Returns: {"commit": "sha", "branch": "branch_name", "version": "26.2.0", "build": "101_dev", "raw": "..."}
    """
    if use_commit_arg:
        parts = use_commit_arg.strip().split("-", 1)
        commit = parts[0] if parts else ""
        branch = parts[1] if len(parts) > 1 else ""
        return {"commit": commit, "branch": branch, "version": "", "build": "", "raw": use_commit_arg}

    ip = resolve_device_ip(device)
    user, pw = get_device_credentials(ip)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ip, port=22, username=user, password=pw, timeout=10)
    except Exception as e:
        return {"error": str(e), "commit": "", "branch": "", "version": "", "build": ""}

    result = {"commit": "", "branch": "", "version": "", "build": "", "raw": ""}

    # Get show system version
    stdin, stdout, stderr = ssh.exec_command("show system version | no-more")
    time.sleep(2)
    version_out = stdout.read().decode(errors="replace")
    vm = VERSION_RE.search(version_out)
    if vm:
        result["version"] = vm.group(1)
        result["build"] = vm.group(2)

    # Try port 2222 first for direct shell (cat /.gitcommit)
    try:
        shell_ssh = paramiko.SSHClient()
        shell_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        shell_ssh.connect(ip, port=2222, username=user, password=pw, timeout=5)
        stdin, stdout, stderr = shell_ssh.exec_command("cat /.gitcommit")
        time.sleep(1)
        raw = stdout.read().decode(errors="replace").strip()
        shell_ssh.close()
        if raw and len(raw) > 20:
            result["raw"] = raw
            parts = raw.split("-", 1)
            result["commit"] = parts[0].strip()
            result["branch"] = parts[1].strip() if len(parts) > 1 else ""
            ssh.close()
            return result
    except Exception:
        pass

    # Fallback: DNOS CLI -> run start shell -> password -> cat /.gitcommit
    # Same pattern as bgp_tool._ssh_shell_commands: consume prompt, handle Password, recv after each step
    try:
        shell = ssh.invoke_shell(width=200, height=50)
        shell.settimeout(15)
        time.sleep(1)
        shell.recv(65535)  # consume initial prompt

        shell.send("run start shell\n")
        time.sleep(2)
        out = shell.recv(65535).decode(errors="replace")
        if "Password:" in out or "password:" in out:
            shell.send(pw + "\n")
            time.sleep(1)
            shell.recv(65535)

        shell.send("cat /.gitcommit\n")
        time.sleep(2)
        output = shell.recv(65535).decode(errors="replace")
        shell.send("exit\n")
        time.sleep(0.5)
        shell.send("exit\n")
        time.sleep(0.5)
        output += shell.recv(65535).decode(errors="replace")
        shell.close()
    except Exception as e:
        result["error"] = str(e)
        output = ""
    ssh.close()

    for line in (output or "").splitlines():
        line = line.strip()
        if len(line) >= 40 and "-" in line and re.match(r"^[0-9a-fA-F]{7,40}-", line):
            result["raw"] = line
            parts = line.split("-", 1)
            result["commit"] = parts[0].strip()
            result["branch"] = parts[1].strip() if len(parts) > 1 else ""
            break

    return result


def parse_recipes() -> list:
    """Parse VERIFY_RECIPES.md and return list of recipe dicts."""
    recipes = []
    if not os.path.exists(RECIPES_PATH):
        return recipes

    with open(RECIPES_PATH) as f:
        content = f.read()

    # Split by ## SW- or ## BUG- or ## SW-REDIRECT style headers
    sections = re.split(r"\n## (?=SW-|BUG-|SW-[A-Z])", content)
    for section in sections:
        if not section.strip():
            continue
        lines = section.split("\n")
        header = lines[0] if lines else ""
        # Extract bug ID and title: "SW-211921: IRB Flap..." or "SW-REDIRECT-IP-UNREACHABLE: ..."
        m = re.match(r"^(SW-[A-Za-z0-9-]+|BUG-\d+)\s*:\s*(.+)", header)
        if not m:
            continue
        bug_id = m.group(1).strip()
        title = m.group(2).strip() if m.group(2) else ""

        rec = {"bug_id": bug_id, "title": title, "fix_commit": "", "fix_commits": [], "fix_branch": "", "fix_versions": "", "excluded_branches": "", "status": "unknown"}

        for line in lines[1:80]:
            line_stripped = line.strip()
            if "- **Fix commit" in line_stripped and ":**" in line_stripped:
                val = re.sub(r"^-\s*\*\*Fix commit[^:]*:\*\*\s*", "", line_stripped).strip()
                rec["fix_commit"] = val
                if any(s in val.lower() for s in SKIP_PATTERNS):
                    rec["status"] = "skip"
                elif "do not use" in val.lower() or "unknown" in val.lower():
                    # Recipe explicitly says fix commit unknown or wrong (e.g. SW-238966: ffa5846 is SW-230334)
                    rec["fix_commits"] = []
                else:
                    # Extract SHAs (prefer full 40-char, then short)
                    for m in SHA_FULL_RE.finditer(val):
                        rec["fix_commits"].append(m.group(0))
                    for m in SHA_SHORT_RE.finditer(val):
                        s = m.group(1)
                        if len(s) >= 7 and s not in rec["fix_commits"]:
                            rec["fix_commits"].append(s)
            if line_stripped.startswith("- **Fix branch"):
                rec["fix_branch"] = re.sub(r"^-\s*\*\*Fix branch:\*\*\s*", "", line_stripped).strip()
            if line_stripped.startswith("- **Fix versions"):
                rec["fix_versions"] = re.sub(r"^-\s*\*\*Fix versions[^:]*:\*\*\s*", "", line_stripped).strip()
            if line_stripped.startswith("- **Excluded branches"):
                rec["excluded_branches"] = re.sub(r"^-\s*\*\*Excluded branches[^:]*:\*\*\s*", "", line_stripped).strip()
            if line_stripped.startswith("- **Status:**"):
                rec["status"] = "skip" if "no fix" in line_stripped.lower() or "open" in line_stripped.lower() else rec["status"]

        recipes.append(rec)
    return recipes


def find_fix_commit(bug_id: str) -> dict:
    """
    Find fix commit for bug from recipes, git log, then Jira.
    Returns: {"commit": "sha", "branch": "", "fix_versions": "", "source": "recipes|git|jira", "status": "ok|skip|unknown"}
    """
    # Source 1: VERIFY_RECIPES.md
    recipes = parse_recipes()
    for r in recipes:
        rid = r["bug_id"].upper()
        bid = bug_id.upper()
        if rid == bid or rid.replace("-", "") == bid.replace("-", ""):
            if r["status"] == "skip":
                return {"commit": "", "branch": r["fix_branch"], "fix_versions": r["fix_versions"], "excluded_branches": r.get("excluded_branches", ""), "source": "recipes", "status": "skip"}
            if r["fix_commits"]:
                return {"commit": r["fix_commits"][0], "branch": r["fix_branch"], "fix_versions": r["fix_versions"], "excluded_branches": r.get("excluded_branches", ""), "source": "recipes", "status": "ok"}
            return {"commit": "", "branch": r["fix_branch"], "fix_versions": r["fix_versions"], "excluded_branches": r.get("excluded_branches", ""), "source": "recipes", "status": "unknown"}

    # Source 2: git log
    if os.path.exists(os.path.join(CHEETAH_REPO, ".git")):
        try:
            out = subprocess.run(
                ["git", "log", "--all", "--oneline", "--grep=" + bug_id],
                cwd=CHEETAH_REPO,
                capture_output=True,
                text=True,
                timeout=15,
            )
            if out.returncode == 0 and out.stdout:
                first = out.stdout.split("\n")[0]
                m = re.match(r"^([0-9a-fA-F]{7,40})", first)
                if m:
                    return {"commit": m.group(1), "branch": "", "fix_versions": "", "excluded_branches": "", "source": "git", "status": "ok"}
        except Exception:
            pass

    # Source 3: Jira (optional - would need MCP/API, skip for standalone script)
    return {"commit": "", "branch": "", "fix_versions": "", "excluded_branches": "", "source": "none", "status": "unknown"}


def resolve_short_sha(short_sha: str) -> str:
    """Resolve short SHA to full 40-char SHA."""
    if len(short_sha) >= 40:
        return short_sha
    try:
        out = subprocess.run(
            ["git", "rev-parse", short_sha],
            cwd=CHEETAH_REPO,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode == 0 and out.stdout:
            return out.stdout.strip()
    except Exception:
        pass
    return short_sha


def check_ancestry(fix_commit: str, build_commit: str, fix_branch: str = "") -> bool:
    """
    Run git merge-base --is-ancestor.
    Returns True if fix is ancestor of build (fix is in build).
    """
    if not fix_commit or not build_commit:
        return False
    fix_full = resolve_short_sha(fix_commit)
    build_full = resolve_short_sha(build_commit[:40] if len(build_commit) >= 40 else build_commit)
    try:
        # Fetch fix branch if provided (fix may be on different branch than build)
        if fix_branch:
            subprocess.run(
                ["git", "fetch", "origin", fix_branch, "--quiet"],
                cwd=CHEETAH_REPO,
                capture_output=True,
                timeout=30,
            )
        out = subprocess.run(
            ["git", "merge-base", "--is-ancestor", fix_full, build_full],
            cwd=CHEETAH_REPO,
            capture_output=True,
            timeout=10,
        )
        return out.returncode == 0
    except Exception:
        return False


def version_in_fix_range(device_version: str, fix_versions: str) -> bool:
    """Check if device version is >= any fix version. E.g. 26.2.0 >= 26.1."""
    if not device_version or not fix_versions:
        return False
    # Parse fix versions: "v25.4.13, v26.1 (and all later releases: v26.2+)"
    for part in re.findall(r"v?(\d+)\.(\d+)(?:\.(\d+))?", fix_versions):
        major = int(part[0])
        minor = int(part[1]) if len(part) > 1 else 0
        patch = int(part[2]) if len(part) > 2 else 0
        try:
            dv = [int(x) for x in re.findall(r"\d+", device_version)[:3]]
            if len(dv) >= 2:
                if dv[0] > major:
                    return True
                if dv[0] == major and dv[1] > minor:
                    return True
                if dv[0] == major and dv[1] == minor and (len(dv) < 3 or dv[2] >= patch):
                    return True
        except (ValueError, IndexError):
            continue
    return False


def check_fix_in_build(device: str, bug_id: str, commit_override: str = None, build_info: dict = None) -> tuple:
    """
    Main check: is the fix for bug_id in the device's build?
    Returns: (result_str, build_info, fix_info)
    result_str: "FIX IN BUILD" | "FIX NOT IN BUILD" | "LIKELY IN BUILD" | "UNKNOWN" | "SKIP"
    """
    if build_info is None:
        build_info = get_device_commit(device, commit_override)
    if build_info.get("error"):
        return "UNKNOWN", build_info, {}
    build_commit = build_info.get("commit", "")
    if not build_commit and not commit_override:
        return "UNKNOWN", build_info, {}

    fix_info = find_fix_commit(bug_id)
    if fix_info["status"] == "skip":
        return "SKIP", build_info, fix_info

    # Check excluded branches (e.g. SW-238966: dev_v26_2 does NOT have the fix)
    build_branch = (build_info.get("branch") or "").lower()
    excluded = (fix_info.get("excluded_branches") or "").lower()
    if build_branch and excluded:
        for part in re.split(r"[\s,;]+", excluded):
            part = part.strip()
            if part and part in build_branch:
                return "FIX NOT IN BUILD", build_info, {**fix_info, "reason": f"build branch {build_branch!r} is excluded ({part})"}

    if fix_info["commit"]:
        in_build = check_ancestry(fix_info["commit"], build_commit, fix_info.get("branch", ""))
        return ("FIX IN BUILD" if in_build else "FIX NOT IN BUILD"), build_info, fix_info

    if fix_info["fix_versions"] and build_info.get("version"):
        if version_in_fix_range(build_info["version"], fix_info["fix_versions"]):
            return "LIKELY IN BUILD", build_info, fix_info
        return "LIKELY NOT IN BUILD", build_info, fix_info

    return "UNKNOWN", build_info, fix_info


def main():
    parser = argparse.ArgumentParser(description="Build-vs-Fix Checker: check if device build includes bug fix")
    parser.add_argument("--device", help="Device name (e.g. PE-1) or IP")
    parser.add_argument("--bug", help="Bug ID (e.g. SW-238966)")
    parser.add_argument("--commit", help="Override: use this commit-branch instead of fetching from device")
    parser.add_argument("--all-recipes", action="store_true", help="Check all recipes against device")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    if not args.device and not args.commit:
        parser.error("--device or --commit required")
    if not args.bug and not args.all_recipes:
        parser.error("--bug or --all-recipes required")

    device = args.device or "unknown"
    commit_override = args.commit

    if args.all_recipes:
        build_info = get_device_commit(device, commit_override)
        if build_info.get("error"):
            print(f"Error: {build_info['error']}", file=sys.stderr)
            sys.exit(2)
        recipes = parse_recipes()
        results = []
        for rec in recipes:
            if rec["status"] == "skip":
                results.append({"bug_id": rec["bug_id"], "title": rec["title"][:40], "fix_commit": "(open)", "in_build": "SKIP"})
                continue
            fix_info = find_fix_commit(rec["bug_id"])
            if fix_info["commit"]:
                in_build = check_ancestry(fix_info["commit"], build_info.get("commit", ""), fix_info.get("branch", ""))
                results.append({"bug_id": rec["bug_id"], "title": rec["title"][:40], "fix_commit": fix_info["commit"][:12], "in_build": "YES" if in_build else "NO"})
            elif fix_info["fix_versions"] and build_info.get("version"):
                in_build = version_in_fix_range(build_info["version"], fix_info["fix_versions"])
                results.append({"bug_id": rec["bug_id"], "title": rec["title"][:40], "fix_commit": "(version)", "in_build": "LIKELY" if in_build else "LIKELY_NOT"})
            else:
                results.append({"bug_id": rec["bug_id"], "title": rec["title"][:40], "fix_commit": "(unknown)", "in_build": "UNKNOWN"})

        if args.json:
            print(json.dumps({"device": device, "build": build_info.get("commit", "")[:12], "version": build_info.get("version"), "results": results}, indent=2))
        else:
            print(f"Device: {device} | Build: {build_info.get('commit', '')[:12]}... ({build_info.get('version', '')} build {build_info.get('build', '')})")
            print()
            print(f"| {'Bug':<20} | {'Title':<42} | {'Fix Commit':<12} | {'In Build?':<10} |")
            print("|" + "-" * 22 + "|" + "-" * 44 + "|" + "-" * 14 + "|" + "-" * 12 + "|")
            for r in results:
                print(f"| {r['bug_id']:<20} | {r['title']:<42} | {r['fix_commit']:<12} | {r['in_build']:<10} |")
        sys.exit(0)

    result, build_info, fix_info = check_fix_in_build(device, args.bug, commit_override)

    if args.json:
        out = {
            "device": device,
            "bug": args.bug,
            "result": result,
            "build": build_info.get("commit", "")[:12],
            "build_branch": build_info.get("branch", ""),
            "fix_commit": fix_info.get("commit", "")[:12],
            "fix_branch": fix_info.get("branch", ""),
            "excluded_branches": fix_info.get("excluded_branches", ""),
            "fix_versions": fix_info.get("fix_versions", ""),
        }
        print(json.dumps(out))
    else:
        if not build_info.get("error"):
            print(f"=== Build Check: {device} vs {args.bug} ===")
            print()
            print(f"Device:     {device}")
            print(f"Version:    DNOS [{build_info.get('version', '')}] build [{build_info.get('build', '')}]")
            print(f"Build:      {build_info.get('commit', '')[:12]}...  (branch: {build_info.get('branch', '')})")
            print()
            print(f"Bug:        {args.bug}")
            print(f"Fix commit: {fix_info.get('commit', '')[:12]}...  (source: {fix_info.get('source', '')})")
            print(f"Fix branch: {fix_info.get('branch', '')}")
            print(f"Fix versions: {fix_info.get('fix_versions', '')}")
            print()
        print(f"Result:     {result}")
    sys.exit(0 if result in ("FIX IN BUILD", "LIKELY IN BUILD") else 1)


if __name__ == "__main__":
    main()
