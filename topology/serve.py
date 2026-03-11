#!/usr/bin/env python3
"""Simple threaded HTTP server for serving the topology app."""
import http.server
import socketserver
import os
import json
import glob
import subprocess
import threading
import uuid
import time
import urllib.request
import urllib.error

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
BUG_EVIDENCE_DIR = os.path.expanduser("~/SCALER/FLOWSPEC_VPN/bug_evidence")
DISCOVERY_API = "http://localhost:8765"
SCALER_BRIDGE_API = "http://localhost:8766"
XRAY_CONFIG_PATH = os.path.expanduser("~/.xray_config.json")
XRAY_CAPTURES = {}  # capture_id -> { process, status, output_lines, pcap_path, error }
CUSTOM_SECTIONS_DIR = os.path.expanduser("~/.topology_sections")
CUSTOM_SECTIONS_CONFIG = os.path.join(CUSTOM_SECTIONS_DIR, "_sections.json")

# Shared state for service monitor (updated by monitor thread, read by Handler and __main__)
_child_procs = {"discovery": None, "bridge": None}
_child_start_times = {"discovery": 0.0, "bridge": 0.0}
_discovery_file_mtime = 0.0
_health_fail_count = {"discovery": 0, "bridge": 0}
_restart_timestamps = []  # (timestamp, service_name) for crash-loop detection
_monitor_lock = threading.Lock()

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()
    
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _handle_health(self):
        """Return aggregated status of serve + discovery_api + scaler_bridge."""
        now = time.time()
        result = {
            "serve": {"status": "ok", "port": PORT},
            "discovery_api": {"status": "unknown", "port": 8765},
            "scaler_bridge": {"status": "unknown", "port": 8766},
        }
        proc = _child_procs.get("discovery")
        if proc is not None and proc.poll() is None:
            uptime = now - _child_start_times.get("discovery", now)
            result["discovery_api"] = {
                "status": "ok",
                "port": 8765,
                "pid": proc.pid,
                "uptime_s": int(uptime),
            }
        else:
            try:
                req = urllib.request.Request(DISCOVERY_API + "/api/health", method="HEAD")
                urllib.request.urlopen(req, timeout=2)
                result["discovery_api"] = {"status": "ok", "port": 8765, "managed": proc is not None}
            except Exception:
                result["discovery_api"] = {"status": "down", "port": 8765}
        proc = _child_procs.get("bridge")
        if proc is not None and proc.poll() is None:
            uptime = now - _child_start_times.get("bridge", now)
            result["scaler_bridge"] = {
                "status": "ok",
                "port": 8766,
                "pid": proc.pid,
                "uptime_s": int(uptime),
            }
        else:
            try:
                req = urllib.request.Request(SCALER_BRIDGE_API + "/docs", method="HEAD")
                urllib.request.urlopen(req, timeout=2)
                result["scaler_bridge"] = {"status": "ok", "port": 8766, "managed": proc is not None}
            except Exception:
                result["scaler_bridge"] = {"status": "down", "port": 8766}
        return self._send_json(result)

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()
    
    def _proxy_to_discovery(self, method="GET", body=None):
        """Proxy /api/dnaas/* and /api/network-mapper/* to discovery_api on port 8765."""
        # /api/dnaas/discovery/list -> /api/discovery/list
        # /api/dnaas/multi-bd/start -> /api/multi-bd/start
        # /api/network-mapper/* -> /api/network-mapper/* (pass through as-is)
        if self.path.startswith("/api/network-mapper/"):
            upstream = self.path
        else:
            upstream = self.path.replace("/api/dnaas/", "/api/", 1)
        url = DISCOVERY_API + upstream
        timeout = 30 if method == "GET" else 300
        last_error = None
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, data=body, method=method)
                if body:
                    req.add_header('Content-Type', 'application/json')
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = resp.read()
                    self.send_response(resp.status)
                    self.send_header('Content-Type', resp.headers.get('Content-Type', 'application/json'))
                    self.end_headers()
                    self.wfile.write(data)
                return
            except urllib.error.HTTPError as e:
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                err_body = e.read() if e.fp else b'{"error":"upstream error"}'
                self.wfile.write(err_body)
                return
            except (urllib.error.URLError, OSError, TimeoutError) as e:
                last_error = e
                if attempt == 0:
                    time.sleep(2)
        detail = "Check if discovery_api.py is running on port 8765"
        try:
            hurl = DISCOVERY_API + "/api/health"
            with urllib.request.urlopen(hurl, timeout=3) as hr:
                health = json.loads(hr.read())
                detail = f"API is running (uptime {health.get('uptime_s', '?')}s, MCP: {health.get('mcp_client', '?')}), but request to {upstream} failed"
        except Exception:
            detail = "discovery_api.py is not responding on port 8765 -- may need restart"
        self._send_json({
            "error": f"Discovery API unavailable: {last_error}",
            "endpoint": upstream,
            "detail": detail
        }, 502)

    def _proxy_sse_stream(self):
        """Stream SSE from scaler_bridge to the client without buffering."""
        url = SCALER_BRIDGE_API + self.path
        try:
            req = urllib.request.Request(url, method="GET")
            resp = urllib.request.urlopen(req, timeout=600)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            while True:
                line = resp.readline()
                if not line:
                    break
                self.wfile.write(line)
                self.wfile.flush()
        except Exception as e:
            try:
                self._send_json({"detail": f"SSE proxy error: {e}"}, 502)
            except Exception:
                pass

    def _proxy_to_scaler_bridge(self, method="GET", body=None):
        """Proxy /api/config/* and /api/devices/{id}/context to scaler_bridge on port 8766."""
        url = SCALER_BRIDGE_API + self.path
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, data=body, method=method)
                if body:
                    req.add_header("Content-Type", "application/json")
                with urllib.request.urlopen(req, timeout=120) as resp:
                    data = resp.read()
                    self.send_response(resp.status)
                    self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                    self.end_headers()
                    self.wfile.write(data)
                    return
            except urllib.error.HTTPError as e:
                self.send_response(e.code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                err_body = e.read() if e.fp else b'{"detail":"upstream error"}'
                self.wfile.write(err_body)
                return
            except Exception as e:
                if attempt == 0:
                    proc = _child_procs.get("bridge")
                    bridge_dead = proc is None or proc.poll() is not None
                    if bridge_dead:
                        print("[INFO] Bridge down on request, attempting on-demand start...")
                        new_proc = _start_scaler_bridge()
                        if new_proc:
                            with _monitor_lock:
                                _child_procs["bridge"] = new_proc
                                _child_start_times["bridge"] = time.time()
                            continue
                self._send_json({"detail": f"Scaler bridge unavailable: {e}"}, 503)
                return
    
    def _serve_debug_dnos_list(self):
        """Serve list of .topology.json files from bug_evidence."""
        try:
            pattern = os.path.join(BUG_EVIDENCE_DIR, "*.topology.json")
            files = sorted(glob.glob(pattern))
            items = []
            for f in files:
                name = os.path.basename(f)
                display_name = name.replace(".topology.json", "")
                items.append({"name": display_name, "filename": name})
            self._send_json({"topologies": items})
        except Exception as e:
            self._send_json({"topologies": [], "error": str(e)}, 500)
    
    def _save_debug_dnos_file(self, body):
        """Save a topology as a .topology.json bug evidence file."""
        try:
            data = json.loads(body) if body else {}
            name = data.get("name", "").strip()
            topology = data.get("topology", {})
            if not name:
                return self._send_json({"error": "Name is required"}, 400)
            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
            filename = f"{safe_name}.topology.json"
            os.makedirs(BUG_EVIDENCE_DIR, exist_ok=True)
            path = os.path.join(BUG_EVIDENCE_DIR, filename)
            with open(path, "w") as f:
                json.dump(topology, f, indent=2)
            return self._send_json({"ok": True, "filename": filename, "path": path})
        except Exception as e:
            return self._send_json({"error": str(e)}, 500)

    # --- Custom Topology Sections ---
    def _sections_read(self):
        os.makedirs(CUSTOM_SECTIONS_DIR, exist_ok=True)
        try:
            with open(CUSTOM_SECTIONS_CONFIG, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _sections_write(self, sections):
        os.makedirs(CUSTOM_SECTIONS_DIR, exist_ok=True)
        with open(CUSTOM_SECTIONS_CONFIG, "w") as f:
            json.dump(sections, f, indent=2)

    def _section_dir(self, section_id):
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in section_id)
        return os.path.join(CUSTOM_SECTIONS_DIR, safe)

    def _handle_sections_get(self, path):
        if path == "/api/sections":
            self._send_json({"sections": self._sections_read()})
            return True
        if path.startswith("/api/sections/") and path.endswith("/topologies"):
            sid = path.split("/")[3]
            sdir = self._section_dir(sid)
            topos = []
            if os.path.isdir(sdir):
                for f in sorted(os.listdir(sdir)):
                    if f.endswith(".json"):
                        fpath = os.path.join(sdir, f)
                        mtime = os.path.getmtime(fpath)
                        topos.append({"name": f.replace(".json", ""), "filename": f, "modified": mtime})
            self._send_json({"topologies": topos})
            return True
        if "/topologies/" in path:
            parts = path.split("/")
            sid, fname = parts[3], parts[5]
            fpath = os.path.join(self._section_dir(sid), fname)
            if not os.path.isfile(fpath):
                self._send_json({"error": "Not found"}, 404)
                return True
            with open(fpath, "r") as f:
                self._send_json(json.load(f))
            return True
        return None

    def _handle_sections_post(self, path, body):
        data = json.loads(body) if body else {}
        if path == "/api/sections":
            sections = self._sections_read()
            new_sec = data
            new_name = (new_sec.get("name") or "").strip()
            if new_name.lower() == "dnaas":
                self._send_json({"error": "\"DNAAS\" is a reserved domain name"}, 400)
                return True
            if any((s.get("name") or "").lower() == new_name.lower() for s in sections):
                self._send_json({"error": f"Domain \"{new_name}\" already exists"}, 400)
                return True
            new_sec.setdefault("id", "sec_" + str(int(time.time())))
            sections.append(new_sec)
            self._sections_write(sections)
            self._send_json({"ok": True, "section": new_sec})
            return True
        if path == "/api/sections/reorder":
            self._sections_write(data.get("sections", []))
            self._send_json({"ok": True})
            return True
        if path.startswith("/api/sections/") and path.endswith("/save"):
            sid = path.split("/")[3]
            name = data.get("name", "").strip()
            topo = data.get("topology", {})
            if not name:
                self._send_json({"error": "Name required"}, 400)
                return True
            safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
            sdir = self._section_dir(sid)
            os.makedirs(sdir, exist_ok=True)
            fpath = os.path.join(sdir, safe + ".json")
            with open(fpath, "w") as f:
                json.dump(topo, f, indent=2)
            self._send_json({"ok": True, "filename": safe + ".json"})
            return True
        if path.startswith("/api/sections/") and path.endswith("/delete"):
            sid = path.split("/")[3]
            sections = self._sections_read()
            sections = [s for s in sections if s.get("id") != sid]
            self._sections_write(sections)
            import shutil
            sdir = self._section_dir(sid)
            if os.path.isdir(sdir):
                shutil.rmtree(sdir)
            self._send_json({"ok": True})
            return True
        if path == "/api/sections/update":
            sections = self._sections_read()
            updated = data
            upd_name = (updated.get("name") or "").strip()
            upd_id = updated.get("id")
            old_sec = next((s for s in sections if s.get("id") == upd_id), None)
            old_name = (old_sec.get("name") or "") if old_sec else ""
            if upd_name.lower() == "dnaas" and old_name.lower() != "dnaas":
                self._send_json({"error": "\"DNAAS\" is a reserved domain name"}, 400)
                return True
            if any(s.get("id") != upd_id and (s.get("name") or "").lower() == upd_name.lower() for s in sections):
                self._send_json({"error": f"Domain \"{upd_name}\" already exists"}, 400)
                return True
            sections = [updated if s.get("id") == upd_id else s for s in sections]
            self._sections_write(sections)
            self._send_json({"ok": True})
            return True
        # Rename a topology file within a section
        if "/topologies/" in path and path.endswith("/rename"):
            parts = path.split("/")
            sid, fname = parts[3], parts[5]
            new_name = data.get("name", "").strip()
            if not new_name:
                self._send_json({"error": "Name required"}, 400)
                return True
            safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in new_name)
            sdir = self._section_dir(sid)
            old_path = os.path.join(sdir, fname)
            new_path = os.path.join(sdir, safe + ".json")
            if not os.path.isfile(old_path):
                self._send_json({"error": "Not found"}, 404)
                return True
            if os.path.isfile(new_path) and old_path != new_path:
                self._send_json({"error": "Name already exists"}, 400)
                return True
            os.rename(old_path, new_path)
            self._send_json({"ok": True, "filename": safe + ".json"})
            return True
        # Delete a single topology file within a section
        if "/topologies/" in path and path.endswith("/delete-file"):
            parts = path.split("/")
            sid, fname = parts[3], parts[5]
            fpath = os.path.join(self._section_dir(sid), fname)
            if os.path.isfile(fpath):
                os.remove(fpath)
                self._send_json({"ok": True})
            else:
                self._send_json({"error": "Not found"}, 404)
            return True
        # Move a topology file from one section to another
        if "/topologies/" in path and path.endswith("/move"):
            from urllib.parse import unquote
            import shutil
            parts = path.split("/")
            if len(parts) < 7:
                self._send_json({"error": "Invalid move path"}, 400)
                return True
            src_sid, fname = parts[3], unquote(parts[5])
            dest_sid = data.get("target_section_id", "").strip()
            if not dest_sid:
                self._send_json({"error": "target_section_id required"}, 400)
                return True
            if not fname.endswith(".json"):
                fname = fname + ".json"
            src_dir = self._section_dir(src_sid)
            src_path = os.path.join(src_dir, fname)
            print(f"[MOVE] {fname}: {src_sid} → {dest_sid}")
            if not os.path.isfile(src_path):
                avail = os.listdir(src_dir) if os.path.isdir(src_dir) else []
                print(f"[MOVE] Not found: {src_path}  Available: {avail}")
                self._send_json({"error": f"Source file not found: {fname}"}, 404)
                return True
            dest_dir = self._section_dir(dest_sid)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, fname)
            if os.path.isfile(dest_path):
                base, ext = os.path.splitext(fname)
                dest_path = os.path.join(dest_dir, base + "_moved" + ext)
            try:
                shutil.move(src_path, dest_path)
                print(f"[MOVE] OK: {src_path} → {dest_path}")
                self._send_json({"ok": True, "filename": os.path.basename(dest_path)})
            except Exception as e:
                print(f"[MOVE] Error: {e}")
                self._send_json({"error": str(e)}, 500)
            return True
        return None

    def _serve_debug_dnos_file(self, filename):
        """Serve a single .topology.json file."""
        if ".." in filename or "/" in filename or "\\" in filename:
            self.send_error(400, "Invalid filename")
            return
        path = os.path.join(BUG_EVIDENCE_DIR, filename)
        if not os.path.isfile(path):
            self.send_error(404, "File not found")
            return
        try:
            with open(path, "r") as f:
                data = json.load(f)
            self._send_json(data)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)
    
    def _migrate_bug_topologies(self, body):
        """Migrate bug topology files from old BUG_EVIDENCE_DIR into a sections-API section."""
        data = json.loads(body) if body else {}
        section_id = data.get("section_id", "")
        if not section_id:
            return self._send_json({"error": "section_id required"}, 400)
        sdir = self._section_dir(section_id)
        os.makedirs(sdir, exist_ok=True)
        migrated = 0
        if os.path.isdir(BUG_EVIDENCE_DIR):
            for f in os.listdir(BUG_EVIDENCE_DIR):
                if f.endswith(".topology.json"):
                    src = os.path.join(BUG_EVIDENCE_DIR, f)
                    dest_name = f.replace(".topology.json", ".json")
                    dest = os.path.join(sdir, dest_name)
                    if not os.path.isfile(dest):
                        import shutil
                        shutil.copy2(src, dest)
                        migrated += 1
        return self._send_json({"ok": True, "migrated": migrated})

    def _xray_config_read(self):
        try:
            with open(XRAY_CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _xray_config_write(self, data):
        with open(XRAY_CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=2)

    def _handle_device_sync(self, device_id):
        """Sync (fetch) running config from device. Proxies to scaler_bridge when available."""
        try:
            url = SCALER_BRIDGE_API + f"/api/config/{urllib.parse.quote(device_id)}/sync"
            req = urllib.request.Request(url, method="POST")
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                return self._send_json(data)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode() if e.fp else "{}"
            try:
                err_data = json.loads(err_body)
                return self._send_json({"detail": err_data.get("detail", str(e))}, e.code)
            except Exception:
                return self._send_json({"detail": str(e)}, e.code)
        except Exception as e:
            return self._send_json({"detail": f"Scaler bridge unavailable: {e}"}, 503)

    def _xray_run(self, params):
        cfg = self._xray_config_read()
        script = cfg.get("script_path", os.path.expanduser("~/live_capture.py"))
        creds = cfg.get("credentials", {})
        mac = cfg.get("mac", {})

        cmd = ["python3", script, "-m", params.get("mode", "cp")]
        cmd += ["-s", params.get("interface", "any")]
        cmd += ["-t", str(params.get("duration", 10))]
        cmd += ["-y"]

        # Direction: ingress, egress, both
        direction = params.get("direction", "both")
        if direction in ("ingress", "egress", "both"):
            cmd += ["-d", direction]

        # Capture filter (BPF)
        if params.get("capture_filter"):
            cmd += ["--capture-filter", params["capture_filter"]]

        # Device host — explicit dut_host or resolve via network-mapper
        dut_host = params.get("dut_host", "").strip()
        if dut_host:
            cmd += ["--dut-host", dut_host]
        else:
            device_name = params.get("device", "")
            if device_name:
                try:
                    url = DISCOVERY_API + f"/api/device/{device_name}/management-interfaces"
                    with urllib.request.urlopen(url, timeout=10) as resp:
                        mgmt = json.loads(resp.read())
                        mgmt_ip = None
                        for iface in mgmt.get("interfaces", []):
                            if "mgmt0" in iface.get("name", "").lower():
                                for addr in iface.get("ipv4_addresses", []):
                                    mgmt_ip = addr.split("/")[0]
                                    break
                            if mgmt_ip:
                                break
                        if mgmt_ip:
                            cmd += ["--dut-host", mgmt_ip]
                except Exception:
                    pass

        if creds.get("device_user"):
            cmd += ["--dut-user", creds["device_user"]]
        if creds.get("device_password"):
            cmd += ["--dut-pass", creds["device_password"]]

        out_mode = params.get("output", "mac")
        if out_mode in ("mac", "mac-live"):
            cmd += ["-o", out_mode]
            if mac.get("ip_vpn"):
                cmd += ["--mac-host", mac["ip_vpn"]]
            if mac.get("user"):
                cmd += ["--mac-user", mac["user"]]
            if mac.get("password"):
                cmd += ["--mac-pass", mac["password"]]
            if mac.get("wireshark_path"):
                cmd += ["--wireshark-path", mac["wireshark_path"]]
            if mac.get("pcap_directory"):
                cmd += ["--mac-directory", mac["pcap_directory"]]
        elif out_mode == "pcap":
            cmd += ["-o", "pcap"]
        else:
            cmd += ["-o", "auto"]

        # DP mode extras
        if params.get("mode") == "dp":
            if params.get("arista_host"):
                cmd += ["--arista-host", params["arista_host"]]
            if params.get("arista_src_port"):
                cmd += ["--arista-src-port", params["arista_src_port"]]
            if creds.get("arista_user"):
                cmd += ["--arista-user", creds["arista_user"]]
            if creds.get("arista_password"):
                cmd += ["--arista-pass", creds["arista_password"]]

        # DNAAS-DP mode extras
        if params.get("mode") == "dnaas-dp":
            dnaas_creds = cfg.get("dnaas_credentials", {})
            if params.get("dnaas_leaf_host"):
                cmd += ["--dnaas-leaf-host", params["dnaas_leaf_host"]]
            if params.get("dnaas_leaf_source_port"):
                cmd += ["--dnaas-leaf-source-port", params["dnaas_leaf_source_port"]]
            if params.get("dnaas_mirror_uplink"):
                cmd += ["--dnaas-mirror-uplink", params["dnaas_mirror_uplink"]]
            if params.get("dnaas_spine_host"):
                cmd += ["--dnaas-spine-host", params["dnaas_spine_host"]]
            leaf_user = dnaas_creds.get("user", "sisaev")
            leaf_pass = dnaas_creds.get("password", "Drive1234!")
            cmd += ["--dnaas-leaf-user", leaf_user]
            cmd += ["--dnaas-leaf-pass", leaf_pass]
            cmd += ["--dnaas-spine-user", leaf_user]
            cmd += ["--dnaas-spine-pass", leaf_pass]

        capture_id = str(uuid.uuid4())[:8]
        cleanup_pcap = params.get("cleanup_server_pcap", True) and out_mode == "mac"
        entry = {"status": "running", "output_lines": [], "pcap_path": None, "error": None, "process": None}
        XRAY_CAPTURES[capture_id] = entry

        def run():
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                entry["process"] = proc
                mac_delivered = False
                for line in proc.stdout:
                    entry["output_lines"].append(line.rstrip())
                    if len(entry["output_lines"]) > 200:
                        entry["output_lines"] = entry["output_lines"][-100:]
                    if "pcap saved" in line.lower() or "wrote" in line.lower():
                        for token in line.split():
                            if token.endswith(".pcap"):
                                entry["pcap_path"] = token
                    if "MAC_DELIVERY_FAILED" in line:
                        entry["mac_delivery_failed"] = True
                    if "pcap saved locally:" in line.lower() or "saved locally:" in line.lower():
                        for token in line.split():
                            if token.endswith(".pcap"):
                                entry["local_pcap_path"] = token
                    if "delivered to mac" in line.lower() or "opened in wireshark" in line.lower():
                        mac_delivered = True
                    ll = line.lower()
                    if ("ssh" in ll or "scp" in ll or "sshpass" in ll) and ("refused" in ll or "unreachable" in ll or "timed out" in ll or "no route" in ll or "permission denied" in ll):
                        entry["mac_delivery_failed"] = True
                    if "connection reset" in ll or "broken pipe" in ll:
                        entry.setdefault("mac_delivery_failed", True)
                proc.wait()
                entry["status"] = "completed" if proc.returncode == 0 else "error"
                if proc.returncode != 0:
                    entry["error"] = f"Exit code {proc.returncode}"
                    if not mac_delivered:
                        entry["mac_delivery_failed"] = True
                if cleanup_pcap and mac_delivered and not entry.get("mac_delivery_failed"):
                    for p in [entry.get("pcap_path"), entry.get("local_pcap_path")]:
                        if p and os.path.isfile(p):
                            try:
                                os.remove(p)
                                entry["server_pcap_cleaned"] = True
                            except OSError:
                                pass
            except Exception as e:
                entry["status"] = "error"
                entry["error"] = str(e)
            finally:
                entry["process"] = None

        t = threading.Thread(target=run, daemon=True)
        t.start()
        return capture_id

    def do_GET(self):
        path = self.path.split("?")[0]
        if path.startswith("/api/dnaas/") or path.startswith("/api/network-mapper/"):
            return self._proxy_to_discovery("GET")
        if path.startswith("/api/config/push/progress/"):
            return self._proxy_sse_stream()
        if path.startswith("/api/config/") or path.startswith("/api/operations/") or path.startswith("/api/wizard/"):
            return self._proxy_to_scaler_bridge("GET")
        if path == "/api/health":
            return self._handle_health()
        if path == "/debug-dnos-topologies/list.json":
            self._serve_debug_dnos_list()
            return
        if path.startswith("/debug-dnos-topologies/") and path.endswith(".json"):
            filename = path.split("/")[-1]
            return self._serve_debug_dnos_file(filename)
        if path == "/api/devices/" or path == "/api/devices":
            devices = []
            try:
                url = DISCOVERY_API + "/api/devices/list"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=3) as resp:
                    data = json.loads(resp.read())
                    devices = data.get("devices", [])
            except Exception:
                pass
            try:
                inv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "device_inventory.json")
                if os.path.exists(inv_path):
                    import re
                    dev_map = {(d.get("hostname") or d.get("id") or "").lower(): d for d in devices}
                    with open(inv_path) as f:
                        inv = json.load(f)
                    for key, dev in inv.get("devices", {}).items():
                        hostname = dev.get("hostname", key)
                        ip_from_key = key if re.match(r"^\d+\.\d+\.\d+\.\d+", key) else ""
                        ip = (dev.get("mgmt_ip") or ip_from_key or "").split("/")[0]
                        hkey = hostname.lower()
                        existing = dev_map.get(hkey)
                        if existing:
                            if ip and not existing.get("ip"):
                                existing["ip"] = ip
                                existing["mgmt_ip"] = ip
                            if not existing.get("serial") and dev.get("serial"):
                                existing["serial"] = dev.get("serial")
                            if not existing.get("system_type") and dev.get("system_type"):
                                existing["system_type"] = dev.get("system_type")
                                existing["platform"] = dev.get("system_type")
                        else:
                            entry = {
                                "id": hostname, "name": hostname, "hostname": hostname,
                                "ip": ip, "mgmt_ip": ip,
                                "serial": dev.get("serial", ""),
                                "system_type": dev.get("system_type", ""),
                                "platform": dev.get("system_type", "NCP"),
                                "source": "inventory_cache",
                            }
                            devices.append(entry)
                            dev_map[hkey] = entry
            except Exception:
                pass
            scaler_configs = os.path.join(os.path.expanduser("~"), "SCALER", "db", "configs")
            if os.path.isdir(scaler_configs):
                import re as _re
                dev_by_name = {d.get("hostname", "").lower(): d for d in devices}
                for dirname in os.listdir(scaler_configs):
                    ops = os.path.join(scaler_configs, dirname, "operational.json")
                    if not os.path.isfile(ops):
                        continue
                    try:
                        with open(ops) as f:
                            o = json.load(f)
                        raw_mgmt = (o.get("mgmt_ip") or "").split("/")[0]
                        raw_ssh = o.get("ssh_host") or ""
                        ip = raw_mgmt if raw_mgmt and _re.match(r"^\d+\.\d+\.\d+\.\d+$", raw_mgmt) else (raw_ssh if _re.match(r"^\d+\.\d+\.\d+\.\d+$", raw_ssh) else raw_mgmt or "")
                        serial = o.get("serial_number", "")
                        existing = dev_by_name.get(dirname.lower())
                        if existing and not existing.get("ip") and ip:
                            existing["ip"] = ip
                            existing["mgmt_ip"] = ip
                        if not existing:
                            for d in devices:
                                if serial and d.get("serial", "").lower() == serial.lower() and not d.get("ip") and ip:
                                    d["ip"] = ip
                                    d["mgmt_ip"] = ip
                                    break
                            else:
                                entry = {"id": dirname, "name": dirname, "hostname": dirname,
                                         "ip": ip, "mgmt_ip": ip, "serial": serial, "source": "scaler_cache"}
                                if dirname.lower() not in dev_by_name:
                                    devices.append(entry)
                                    dev_by_name[dirname.lower()] = entry
                    except Exception:
                        continue
            return self._send_json({"devices": devices, "count": len(devices)})
        if path.startswith("/api/devices/") and len(path) > len("/api/devices/"):
            device_id = path.split("/api/devices/")[1].split("/")[0]
            device_id = urllib.parse.unquote(device_id)
            action = path.split(device_id + "/")[1].split("/")[0] if (device_id + "/") in path else None
            if action == "context":
                return self._proxy_to_scaler_bridge("GET")
            if action in ("test", "sync"):
                return self._send_json({"status": "ok", "message": f"{action} not available"})
            try:
                url = DISCOVERY_API + f"/api/device/{urllib.parse.quote(device_id)}/resolve"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read())
                    return self._send_json({
                        "id": device_id,
                        "hostname": data.get("hostname", device_id),
                        "ip": data.get("mgmt_ip", ""),
                        "serial": data.get("serial", ""),
                        "source": data.get("source", ""),
                        "username": "dnroot",
                        "password": "dnroot"
                    })
            except Exception:
                return self._send_json({"error": f"Device not found: {device_id}"}, 404)
        if path.startswith("/api/sections"):
            result = self._handle_sections_get(path)
            if result is not None:
                return
        if path == "/api/xray/config":
            return self._send_json(self._xray_config_read())
        if path.startswith("/api/xray/status/"):
            cid = path.split("/")[-1]
            entry = XRAY_CAPTURES.get(cid)
            if not entry:
                return self._send_json({"error": "Not found"}, 404)
            resp = {
                "status": entry["status"],
                "output_lines": entry["output_lines"][-20:],
                "pcap_path": entry["pcap_path"],
                "error": entry["error"]
            }
            if entry.get("mac_delivery_failed"):
                resp["mac_delivery_failed"] = True
                resp["local_pcap_path"] = entry.get("local_pcap_path", entry["pcap_path"])
            return self._send_json(resp)
        super().do_GET()
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        if "/move" in self.path:
            print(f"[POST /move] path={self.path} content_length={content_length} body={body}")
        path = self.path.split("?")[0]
        if path.startswith("/api/dnaas/") or path.startswith("/api/network-mapper/"):
            return self._proxy_to_discovery("POST", body)
        if path.startswith("/api/config/") or path.startswith("/api/operations/") or path.startswith("/api/wizard/"):
            return self._proxy_to_scaler_bridge("POST", body)
        if path == "/api/devices/discover":
            return self._proxy_to_scaler_bridge("POST", body)
        if path.startswith("/api/devices/") and len(path) > len("/api/devices/"):
            parts = path[len("/api/devices/"):].rstrip("/").split("/")
            device_id = urllib.parse.unquote(parts[0]) if parts else ""
            action = parts[1] if len(parts) > 1 else None
            if device_id and action == "test":
                return self._proxy_to_scaler_bridge("POST", body)
            if device_id and action == "sync":
                return self._handle_device_sync(device_id)
        if path == "/api/devices/" or path == "/api/devices":
            return self._send_json({"status": "ok", "message": "Device registered locally"})
        if path == "/debug-dnos-topologies/save":
            return self._save_debug_dnos_file(body)
        if path == "/debug-dnos-topologies/rename":
            data = json.loads(body) if body else {}
            old_name = data.get("old_filename", "")
            new_name = data.get("name", "").strip()
            if not new_name or not old_name:
                return self._send_json({"error": "Name required"}, 400)
            safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in new_name)
            old_path = os.path.join(BUG_EVIDENCE_DIR, old_name)
            new_path = os.path.join(BUG_EVIDENCE_DIR, safe + ".topology.json")
            if not os.path.isfile(old_path):
                return self._send_json({"error": "Not found"}, 404)
            if os.path.isfile(new_path) and old_path != new_path:
                return self._send_json({"error": "Name already exists"}, 400)
            os.rename(old_path, new_path)
            return self._send_json({"ok": True, "filename": safe + ".topology.json"})
        if path == "/debug-dnos-topologies/delete-file":
            data = json.loads(body) if body else {}
            fname = data.get("filename", "")
            if not fname:
                return self._send_json({"error": "Filename required"}, 400)
            fpath = os.path.join(BUG_EVIDENCE_DIR, fname)
            if os.path.isfile(fpath):
                os.remove(fpath)
                return self._send_json({"ok": True})
            return self._send_json({"error": "Not found"}, 404)
        if path == "/api/migrate-bug-topologies":
            return self._migrate_bug_topologies(body)
        if path.startswith("/api/sections"):
            result = self._handle_sections_post(path, body)
            if result is not None:
                return
        if path == "/api/xray/run":
            try:
                params = json.loads(body) if body else {}
                cid = self._xray_run(params)
                return self._send_json({"capture_id": cid})
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)
        if path == "/api/xray/redeliver":
            try:
                data = json.loads(body) if body else {}
                pcap_path = data.get("pcap_path", "").strip()
                new_mac_ip = data.get("mac_ip", "").strip()
                if not pcap_path or not os.path.isfile(pcap_path):
                    return self._send_json({"error": f"pcap not found: {pcap_path}"}, 400)
                if not new_mac_ip:
                    return self._send_json({"error": "mac_ip required"}, 400)
                cfg = self._xray_config_read()
                if "mac" not in cfg:
                    cfg["mac"] = {}
                cfg["mac"]["ip_vpn"] = new_mac_ip
                self._xray_config_write(cfg)
                mac = cfg["mac"]
                import sys
                sys.path.insert(0, os.path.expanduser("~"))
                from xray.common import _scp_pcap_to_mac
                ok = _scp_pcap_to_mac(
                    pcap_path,
                    mac_user=mac.get("user", os.environ.get("USER", "dn")),
                    mac_pass=mac.get("password", ""),
                    mac_host=new_mac_ip,
                    wireshark_path=mac.get("wireshark_path"),
                    mac_directory=mac.get("pcap_directory"),
                )
                if ok:
                    return self._send_json({"ok": True})
                else:
                    return self._send_json({"error": "Mac delivery failed -- check IP/credentials"}, 500)
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)
        if path.startswith("/api/xray/stop/"):
            cid = path.split("/")[-1]
            entry = XRAY_CAPTURES.get(cid)
            if entry and entry.get("process"):
                try:
                    entry["process"].terminate()
                except Exception:
                    pass
                entry["status"] = "stopped"
            return self._send_json({"ok": True})
        if path == "/api/xray/verify-mac":
            try:
                data = json.loads(body) if body else {}
                cfg = self._xray_config_read()
                mac_ip = data.get("ip") or (cfg.get("mac", {}).get("ip_vpn") or "")
                mac_user = cfg.get("mac", {}).get("user", os.environ.get("USER", "dn"))
                mac_pass = cfg.get("mac", {}).get("password", "")
                if not mac_ip:
                    return self._send_json({"reachable": False, "ip": "", "error": "No Mac IP configured"})
                env = os.environ.copy()
                env["SSHPASS"] = mac_pass
                try:
                    result = subprocess.run(
                        f'sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 '
                        f'-o LogLevel=ERROR {mac_user}@{mac_ip} "echo ok"',
                        shell=True, env=env, capture_output=True, text=True, timeout=10
                    )
                    reachable = result.returncode == 0 and "ok" in result.stdout
                    return self._send_json({
                        "reachable": reachable,
                        "ip": mac_ip,
                        "error": result.stderr.strip() if not reachable else None
                    })
                except subprocess.TimeoutExpired:
                    return self._send_json({"reachable": False, "ip": mac_ip, "error": "SSH timed out"})
            except Exception as e:
                return self._send_json({"reachable": False, "ip": "", "error": str(e)})
        if path == "/api/xray/config":
            try:
                data = json.loads(body) if body else {}
                cfg = self._xray_config_read()
                for k, v in data.items():
                    if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                        cfg[k] = {**cfg[k], **v}
                    else:
                        cfg[k] = v
                self._xray_config_write(cfg)
                return self._send_json({"ok": True})
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)
        if path == "/api/ssh/clear-hostkey":
            try:
                data = json.loads(body) if body else {}
                host = data.get("host", "").strip()
                if not host:
                    return self._send_json({"error": "host required"}, 400)
                if not all(c.isalnum() or c in ".-_:" for c in host):
                    return self._send_json({"error": "Invalid host"}, 400)
                result = subprocess.run(
                    ["ssh-keygen", "-R", host],
                    capture_output=True, text=True, timeout=5
                )
                return self._send_json({
                    "ok": result.returncode == 0,
                    "output": (result.stdout + result.stderr).strip()
                })
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)
        if path == "/api/xray/verify-mac":
            try:
                data = json.loads(body) if body else {}
                ip = data.get("ip", "").strip()
                if not ip:
                    return self._send_json({"reachable": False, "error": "IP required"})
                cfg = self._xray_config_read()
                mac = cfg.get("mac", {})
                user = (data.get("user") or "").strip() or mac.get("user") or os.environ.get("USER", "dn")
                password = (data.get("password") or "").strip() or mac.get("password", "")

                # Step 1: Ping check (network reachability)
                ping_ok = False
                try:
                    ping = subprocess.run(
                        ["ping", "-c", "1", "-W", "3", ip],
                        capture_output=True, text=True, timeout=5
                    )
                    ping_ok = ping.returncode == 0
                except Exception:
                    pass

                # Step 2: SSH auth check (identity verification)
                ssh_ok = False
                ssh_err = ""
                env = os.environ.copy()
                env["SSHPASS"] = password
                try:
                    result = subprocess.run(
                        ["sshpass", "-e", "ssh",
                         "-o", "ConnectTimeout=5",
                         "-o", "StrictHostKeyChecking=no",
                         "-o", "UserKnownHostsFile=/dev/null",
                         "-o", "LogLevel=ERROR",
                         f"{user}@{ip}", "echo ok"],
                        capture_output=True, text=True, timeout=12, env=env
                    )
                    ssh_ok = result.returncode == 0 and "ok" in result.stdout
                    if not ssh_ok:
                        ssh_err = result.stderr.strip() or f"SSH exit code {result.returncode}"
                except subprocess.TimeoutExpired:
                    ssh_err = "SSH timed out (12s)"
                except Exception as e:
                    ssh_err = str(e)

                if ssh_ok:
                    return self._send_json({"reachable": True, "ssh": True, "ping": ping_ok})
                elif ping_ok:
                    return self._send_json({
                        "reachable": False, "ping": True, "ssh": False,
                        "error": f"Mac is reachable (ping OK) but SSH failed: {ssh_err}. "
                                 "Enable 'Remote Login' in System Settings > General > Sharing on the Mac."
                    })
                else:
                    return self._send_json({
                        "reachable": False, "ping": False, "ssh": False,
                        "error": f"Mac not reachable at {ip} (ping + SSH both failed). Check VPN connection and IP."
                    })
            except Exception as e:
                return self._send_json({"reachable": False, "error": str(e)})
        self.send_error(404, "Not found")

    def do_DELETE(self):
        path = self.path.split("?")[0]
        if path.startswith("/api/devices/") and len(path) > len("/api/devices/"):
            parts = path[len("/api/devices/"):].rstrip("/").split("/")
            device_id = urllib.parse.unquote(parts[0]) if parts else ""
            if device_id:
                return self._handle_device_delete(device_id)
        self.send_error(404, "Not found")

    def _handle_device_delete(self, device_id):
        """Delete device from local cache. Stub until scaler_bridge - device list comes from discovery_api."""
        return self._send_json({"detail": "Delete not available - use scaler-wizard"}, 503)

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

def _start_discovery_api():
    """Auto-launch discovery_api.py on port 8765 if not already running."""
    discovery_script = os.path.join(DIRECTORY, "discovery_api.py")
    if not os.path.isfile(discovery_script):
        print(f"[WARN] discovery_api.py not found at {discovery_script}, skipping auto-start")
        return None

    # Check if already running
    try:
        req = urllib.request.Request(DISCOVERY_API + "/api/health", method="HEAD")
        urllib.request.urlopen(req, timeout=2)
        print("[OK] Discovery API already running on port 8765")
        return None
    except Exception:
        pass

    print("[INFO] Starting discovery_api.py on port 8765...")
    try:
        proc = subprocess.Popen(
            ["python3", "discovery_api.py"],
            cwd=DIRECTORY,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        # Give it a moment to bind
        time.sleep(1.5)
        if proc.poll() is not None:
            err = proc.stderr.read().decode(errors="replace")[:300]
            print(f"[ERROR] discovery_api.py exited immediately: {err}")
            return None
        print(f"[OK] Discovery API started (pid {proc.pid})")
        return proc
    except Exception as e:
        print(f"[ERROR] Failed to start discovery_api.py: {e}")
        return None


def _start_scaler_bridge():
    """Auto-launch scaler_bridge.py on port 8766 if not already running."""
    bridge_script = os.path.join(DIRECTORY, "scaler_bridge.py")
    if not os.path.isfile(bridge_script):
        print(f"[WARN] scaler_bridge.py not found at {bridge_script}, skipping auto-start")
        return None

    # Check if already running
    try:
        req = urllib.request.Request(SCALER_BRIDGE_API + "/docs", method="HEAD")
        urllib.request.urlopen(req, timeout=2)
        print("[OK] Scaler bridge already running on port 8766")
        return None
    except Exception:
        pass

    print("[INFO] Starting scaler_bridge.py on port 8766...")
    try:
        proc = subprocess.Popen(
            ["python3", "-m", "uvicorn", "scaler_bridge:app", "--host", "0.0.0.0", "--port", "8766", "--reload", "--log-level", "warning"],
            cwd=DIRECTORY,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        # Give it a moment to bind
        time.sleep(1.5)
        if proc.poll() is not None:
            err = proc.stderr.read().decode(errors="replace")[:300]
            print(f"[ERROR] scaler_bridge.py exited immediately: {err}")
            return None
        print(f"[OK] Scaler bridge started (pid {proc.pid})")
        return proc
    except Exception as e:
        print(f"[ERROR] Failed to start scaler_bridge.py: {e}")
        return None


def _service_monitor(stop_event):
    """Background thread: health-check children every 15s, restart on crash or file change."""
    global _child_procs, _child_start_times, _discovery_file_mtime, _health_fail_count, _restart_timestamps
    discovery_script = os.path.join(DIRECTORY, "discovery_api.py")
    crash_window = 120  # seconds
    max_restarts_in_window = 5

    def _health_ok(url, timeout=2):
        try:
            req = urllib.request.Request(url, method="HEAD")
            urllib.request.urlopen(req, timeout=timeout)
            return True
        except Exception:
            return False

    def _restart_discovery():
        global _discovery_file_mtime
        with _monitor_lock:
            proc = _child_procs.get("discovery")
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
        new_proc = _start_discovery_api()
        if new_proc:
            with _monitor_lock:
                _child_procs["discovery"] = new_proc
                _child_start_times["discovery"] = time.time()
                if os.path.isfile(discovery_script):
                    _discovery_file_mtime = os.path.getmtime(discovery_script)
                _health_fail_count["discovery"] = 0
                _restart_timestamps.append((time.time(), "discovery"))

    def _restart_bridge():
        with _monitor_lock:
            proc = _child_procs.get("bridge")
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
        new_proc = _start_scaler_bridge()
        if new_proc:
            with _monitor_lock:
                _child_procs["bridge"] = new_proc
                _child_start_times["bridge"] = time.time()
                _health_fail_count["bridge"] = 0
                _restart_timestamps.append((time.time(), "bridge"))

    def _prune_restarts():
        now = time.time()
        with _monitor_lock:
            _restart_timestamps[:] = [(t, s) for t, s in _restart_timestamps if now - t < crash_window]

    def _restart_count(service):
        now = time.time()
        return sum(1 for t, s in _restart_timestamps if s == service and now - t < crash_window)

    while not stop_event.wait(15):
        _prune_restarts()

        # --- Discovery API (always health-check, even without a proc handle) ---
        proc = _child_procs.get("discovery")
        proc_alive = proc is not None and proc.poll() is None

        if proc is not None and proc.poll() is not None:
            print("[WARN] discovery_api died, restarting...")
            if _restart_count("discovery") < max_restarts_in_window:
                _restart_discovery()
            else:
                print("[ERROR] discovery_api crash loop detected, stopping restarts")
        elif not _health_ok(DISCOVERY_API + "/api/health"):
            _health_fail_count["discovery"] = _health_fail_count.get("discovery", 0) + 1
            if _health_fail_count["discovery"] >= 3:
                print("[WARN] discovery_api health check failed 3x, restarting...")
                _health_fail_count["discovery"] = 0
                if _restart_count("discovery") < max_restarts_in_window:
                    _restart_discovery()
        else:
            _health_fail_count["discovery"] = 0

        # File-change detection for discovery_api
        proc = _child_procs.get("discovery")
        if proc is not None and proc.poll() is None and os.path.isfile(discovery_script):
            mtime = os.path.getmtime(discovery_script)
            if mtime > _discovery_file_mtime and _discovery_file_mtime > 0:
                print("[INFO] discovery_api.py changed, restarting...")
                if _restart_count("discovery") < max_restarts_in_window:
                    _restart_discovery()

        # --- Scaler bridge (always health-check, even without a proc handle) ---
        proc = _child_procs.get("bridge")

        if proc is not None and proc.poll() is not None:
            print("[WARN] scaler_bridge died, restarting...")
            if _restart_count("bridge") < max_restarts_in_window:
                _restart_bridge()
            else:
                print("[ERROR] scaler_bridge crash loop detected, stopping restarts")
        elif not _health_ok(SCALER_BRIDGE_API + "/docs"):
            _health_fail_count["bridge"] = _health_fail_count.get("bridge", 0) + 1
            if _health_fail_count["bridge"] >= 3:
                print("[WARN] scaler_bridge health check failed 3x, restarting...")
                _health_fail_count["bridge"] = 0
                if _restart_count("bridge") < max_restarts_in_window:
                    _restart_bridge()
        else:
            _health_fail_count["bridge"] = 0


if __name__ == "__main__":
    discovery_proc = _start_discovery_api()
    bridge_proc = _start_scaler_bridge()
    if discovery_proc is not None:
        _child_procs["discovery"] = discovery_proc
        _child_start_times["discovery"] = time.time()
        discovery_script = os.path.join(DIRECTORY, "discovery_api.py")
        if os.path.isfile(discovery_script):
            _discovery_file_mtime = os.path.getmtime(discovery_script)
    if bridge_proc is not None:
        _child_procs["bridge"] = bridge_proc
        _child_start_times["bridge"] = time.time()

    monitor_stop = threading.Event()
    monitor_thread = threading.Thread(target=_service_monitor, args=(monitor_stop,), daemon=True)
    monitor_thread.start()

    try:
        with ThreadedHTTPServer(("0.0.0.0", PORT), Handler) as httpd:
            print(f"Serving at http://0.0.0.0:{PORT}")
            httpd.serve_forever()
    finally:
        monitor_stop.set()
        for name, proc in [("discovery_api", _child_procs.get("discovery")), ("scaler_bridge", _child_procs.get("bridge"))]:
            if proc is not None and proc.poll() is None:
                print(f"[INFO] Stopping {name}...")
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass






