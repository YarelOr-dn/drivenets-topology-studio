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
XRAY_CONFIG_PATH = os.path.expanduser("~/.xray_config.json")
XRAY_CAPTURES = {}  # capture_id -> { process, status, output_lines, pcap_path, error }
CUSTOM_SECTIONS_DIR = os.path.expanduser("~/.topology_sections")
CUSTOM_SECTIONS_CONFIG = os.path.join(CUSTOM_SECTIONS_DIR, "_sections.json")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
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
                    self.send_header('Access-Control-Allow-Origin', '*')
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
        self._send_json({
            "error": f"Discovery API unavailable: {last_error}",
            "endpoint": upstream,
            "detail": "Check if discovery_api.py is running on port 8765"
        }, 502)
    
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
            sections = [updated if s.get("id") == updated.get("id") else s for s in sections]
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

    def _xray_run(self, params):
        cfg = self._xray_config_read()
        script = cfg.get("script_path", os.path.expanduser("~/live_capture.py"))
        creds = cfg.get("credentials", {})
        mac = cfg.get("mac", {})

        cmd = ["python3", script, "-m", params.get("mode", "cp")]
        cmd += ["-s", params.get("interface", "any")]
        cmd += ["-t", str(params.get("duration", 10))]
        cmd += ["-y"]

        # Device host — resolve via network-mapper proxy
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
        if out_mode == "mac":
            cmd += ["-o", "mac"]
            if mac.get("ip_vpn"):
                cmd += ["--mac-ip", mac["ip_vpn"]]
            if mac.get("user"):
                cmd += ["--mac-user", mac["user"]]
            if mac.get("password"):
                cmd += ["--mac-pass", mac["password"]]
        elif out_mode == "pcap":
            cmd += ["-o", "pcap"]
        else:
            cmd += ["-o", "auto"]

        # DP mode extras
        if params.get("mode") == "dp":
            if creds.get("arista_user"):
                cmd += ["--arista-user", creds["arista_user"]]
            if creds.get("arista_password"):
                cmd += ["--arista-pass", creds["arista_password"]]

        capture_id = str(uuid.uuid4())[:8]
        entry = {"status": "running", "output_lines": [], "pcap_path": None, "error": None, "process": None}
        XRAY_CAPTURES[capture_id] = entry

        def run():
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                entry["process"] = proc
                for line in proc.stdout:
                    entry["output_lines"].append(line.rstrip())
                    if len(entry["output_lines"]) > 200:
                        entry["output_lines"] = entry["output_lines"][-100:]
                    if "pcap saved" in line.lower() or "wrote" in line.lower():
                        for token in line.split():
                            if token.endswith(".pcap"):
                                entry["pcap_path"] = token
                proc.wait()
                entry["status"] = "completed" if proc.returncode == 0 else "error"
                if proc.returncode != 0:
                    entry["error"] = f"Exit code {proc.returncode}"
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
        if path == "/debug-dnos-topologies/list.json":
            self._serve_debug_dnos_list()
            return
        if path.startswith("/debug-dnos-topologies/") and path.endswith(".json"):
            filename = path.split("/")[-1]
            return self._serve_debug_dnos_file(filename)
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
            return self._send_json({
                "status": entry["status"],
                "output_lines": entry["output_lines"][-20:],
                "pcap_path": entry["pcap_path"],
                "error": entry["error"]
            })
        super().do_GET()
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        if "/move" in self.path:
            print(f"[POST /move] path={self.path} content_length={content_length} body={body}")
        path = self.path.split("?")[0]
        if path.startswith("/api/dnaas/") or path.startswith("/api/network-mapper/"):
            return self._proxy_to_discovery("POST", body)
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
        if path == "/api/xray/config":
            try:
                data = json.loads(body) if body else {}
                cfg = self._xray_config_read()
                cfg.update(data)
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
                ip = data.get("ip", "")
                user = data.get("user", "")
                result = subprocess.run(
                    ["ssh", "-o", "ConnectTimeout=3", "-o", "StrictHostKeyChecking=no",
                     f"{user}@{ip}", "echo ok"],
                    capture_output=True, text=True, timeout=8
                )
                ok = result.returncode == 0 and "ok" in result.stdout
                return self._send_json({"reachable": ok, "output": result.stdout.strip()})
            except Exception as e:
                return self._send_json({"reachable": False, "error": str(e)})
        self.send_error(404, "Not found")

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == "__main__":
    with ThreadedHTTPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"Serving at http://0.0.0.0:{PORT}")
        httpd.serve_forever()






