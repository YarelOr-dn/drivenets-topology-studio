"""Daemon CLI subcommand implementation for spirent_tool.py."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def cmd_daemon(args: Any, *, session_dir: str, tool_file: str) -> int:
    """Control / use the long-running ``spirent_daemon.py`` process."""
    here = Path(tool_file).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    try:
        import spirent_daemon
    except Exception as exc:  # pragma: no cover - operator-facing guard
        print(f"[ERROR] Could not import spirent_daemon: {exc}")
        raise SystemExit(1)

    action = args.action

    if action == "status":
        if spirent_daemon.daemon_is_alive():
            print(f"[OK] daemon alive on {spirent_daemon.SOCKET_PATH}")
            try:
                with open(spirent_daemon.PID_PATH) as f:
                    print(f"     pid={f.read().strip()}")
            except Exception:
                pass
            return 0
        print(f"[INFO] no daemon running (socket absent or unresponsive: {spirent_daemon.SOCKET_PATH})")
        return 1

    if action == "start":
        if spirent_daemon.daemon_is_alive():
            print("[INFO] daemon already running; leaving it in place")
            return 0
        for path in (spirent_daemon.SOCKET_PATH, spirent_daemon.PID_PATH):
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass
            except OSError:
                pass
        log_path = os.path.join(session_dir, "daemon.log")
        os.makedirs(session_dir, exist_ok=True)
        cmd = [sys.executable, str(here / "spirent_daemon.py")]
        if getattr(args, "no_warm", False):
            cmd.append("--no-warm")
        with open(log_path, "ab") as logf:
            proc = subprocess.Popen(
                cmd,
                stdout=logf,
                stderr=logf,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
            )
        for _ in range(40):
            time.sleep(0.25)
            if spirent_daemon.daemon_is_alive():
                print(f"[OK] daemon started pid={proc.pid}, log={log_path}")
                return 0
        print(f"[ERROR] daemon did not come up within ~10s.  See {log_path}.")
        return 1

    if action == "stop":
        if not spirent_daemon.daemon_is_alive():
            print("[INFO] no running daemon to stop")
            return 0
        ok = spirent_daemon.stop_daemon()
        if ok:
            for _ in range(20):
                if not spirent_daemon.daemon_is_alive(timeout=0.5):
                    print("[OK] daemon stopped")
                    return 0
                time.sleep(0.1)
        print("[WARN] daemon did not confirm shutdown; may need SIGKILL via pid file")
        return 1

    if action == "run":
        run_argv = list(getattr(args, "run_argv", []) or [])
        if run_argv and run_argv[0] == "--":
            run_argv = run_argv[1:]
        if not run_argv:
            print("[ERROR] daemon run needs a subcommand (e.g. daemon run -- status)")
            raise SystemExit(2)
        if not spirent_daemon.daemon_is_alive():
            print("[ERROR] no daemon running; start with 'spirent_tool.py daemon start'")
            raise SystemExit(1)
        rc, out, err, elapsed = spirent_daemon.run_via_daemon(run_argv, timeout=args.timeout)
        if out:
            sys.stdout.write(out)
            sys.stdout.flush()
        if err:
            sys.stderr.write(err)
            sys.stderr.flush()
        print(f"[daemon] rc={rc} elapsed={elapsed}ms", file=sys.stderr)
        return rc

    print(f"[ERROR] unknown daemon action: {action}")
    raise SystemExit(2)

