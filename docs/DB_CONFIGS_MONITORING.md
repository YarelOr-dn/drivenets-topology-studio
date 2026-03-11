# How `db/configs/` Works for PE-2 (and Other Devices)

## TL;DR

**PE-2 is not “monitored” by watching the DB.** The DB is **populated by extraction**, then **read** by the monitor and the wizard. The “monitoring” you see is: (1) extraction writing into `db/configs/PE-2/`, and (2) `monitor.py` / scaler reading that directory.

---

## 1. Where PE-2 Data Lives

| Path | Purpose |
|------|---------|
| `db/configs/PE-2/running.txt` | Cached full running config from the device |
| `db/configs/PE-2/operational.json` | Parsed operational data (BGP, interfaces, FXC, VRF, DNOS version, etc.) |
| `db/configs/PE-2/full_output.txt` | Raw SSH output (show config, show system, etc.) — often removed after parsing |
| `db/devices.json` | Device list; PE-2 is one entry (id, hostname, ip, etc.) |

`db/configs/` has **one subdirectory per device** (e.g. `PE-1`, `PE-2`, `PE-4`). The directory name is the **hostname** used in extraction and in the monitor.

---

## 2. Who Writes Into `db/configs/PE-2/`

Two mechanisms can update PE-2’s data:

### A. Bash extraction (`extract_configs.sh`)

- **What it does:** SSHs to the device, runs `show config | no-more` (and other show commands), parses the output, writes:
  - `db/configs/PE-2/running.txt` — extracted running config
  - `db/configs/PE-2/operational.json` — built from parsed output (e.g. from `full_output.txt`)
- **How PE-2 is chosen:** **Hardcoded** in the script. Example from the end of `extract_configs.sh`:

  ```bash
  extract_config "100.64.8.39" "PE-2"
  ```

  So “PE-2” is just the **name** used for the folder and in the monitor; the **IP** `100.64.8.39` is what the script actually connects to.

- **When it runs:** Typically via **cron** (e.g. every 5 minutes), or when you run the script by hand. There is no “DB watcher”; the script runs on a schedule and overwrites/updates the files under `db/configs/PE-2/`.

### B. Python scheduler (`scaler/scheduler.py`)

- **What it does:**  
  - Reads devices from `db/devices.json` (via `DeviceManager`).  
  - For each device (including PE-2 if it’s in `devices.json`), it can:
    - Use **cached** `db/configs/<hostname>/running.txt` if it exists (written by the bash script), or
    - Call `ConfigExtractor` to pull config over SSH and then write/update the same paths.
  - After a run, `extract_configs.sh` can call `ConfigSyncScheduler.trigger_sync_now()` to refresh summaries from those files.

- **When it runs:**  
  - On demand when something calls `trigger_sync_now()`, or  
  - On an interval if a long‑lived process has started the scheduler (e.g. 60‑minute interval).

So for PE-2, the “monitored DB” is really: **cron + extract_configs.sh** (and optionally the Python scheduler) **writing** into `db/configs/PE-2/`. Nothing watches the directory for changes as a primary trigger.

---

## 3. Who Reads From `db/configs/` (“Monitor” for PE-2)

### A. `monitor.py` (scaler monitor)

- **Config path:**  
  `configs_dir = SCALER_DIR / "db" / "configs"` (see around line 558 in `monitor.py`).
- **How PE-2 appears:**  
  It does **not** use `db/devices.json`. It **scans** `db/configs/` and treats **every subdirectory** as a device:
  - For each `device_dir` in `configs_dir.iterdir()` it uses `device_dir.name` as the device name (e.g. `PE-2`).
- **What it uses for PE-2:**
  - `db/configs/PE-2/running.txt` → last modified time, line count, etc.
  - `db/configs/PE-2/operational.json` → DNOS version, BGP, interfaces, FXC/VPWS/EVPN/VRF counts, upgrade state, etc.
- **Modes:**
  - **One‑shot (default):** Read `db/configs/` once, print status, exit.
  - **Watch (`-w`):** Loop, sleep N seconds, clear screen, read `db/configs/` again, re‑print. So “monitoring” = **periodically re-reading** the same directory and showing whatever is currently in `db/configs/PE-2/`.

So **“how db/ is monitored for PE-2”** in the sense of the monitor is: **monitor.py re-reads `db/configs/PE-2/` (and its siblings) on a timer**; it does not watch inotify or file events.

### B. Scaler wizard / interactive scale

- Uses `db/devices.json` for the **list of devices** (including PE-2 if it’s there).
- When it needs config or operational data for a device, it uses the same paths:
  - `db/configs/<hostname>/running.txt`
  - `db/configs/<hostname>/operational.json`
- So for PE-2 it reads `db/configs/PE-2/running.txt` and `db/configs/PE-2/operational.json`. No separate “DB monitor” — it just opens those files when needed.

---

## 4. End‑to‑End Flow for PE-2

1. **Cron runs** `extract_configs.sh` (or you run it manually).
2. Script calls `extract_config "100.64.8.39" "PE-2"`:
   - SSH to `100.64.8.39`,
   - Parse output,
   - Write `db/configs/PE-2/running.txt` and `db/configs/PE-2/operational.json`.
3. Optionally, script runs Python sync (`ConfigSyncScheduler.trigger_sync_now()`), which may refresh/consistentize data under `db/configs/` from `devices.json`.
4. **monitor.py** (one-shot or watch):
   - Lists `db/configs/` → sees folder `PE-2`,
   - Reads `db/configs/PE-2/running.txt` and `db/configs/PE-2/operational.json`,
   - Prints status for “PE-2” in the device table.
5. **Scaler wizard** loads PE-2 from `devices.json` and, when it needs config/ops, reads from `db/configs/PE-2/`.

So **“the DB for PE-2”** is just **`db/configs/PE-2/`**. It is “monitored” only in the sense that:
- **Extraction** (cron + script, and optionally scheduler) **writes** into it,
- **monitor.py** **re-reads** it on each run (and in watch mode, on each refresh),
- **Wizard** **reads** it when handling that device.

There is no separate daemon or file‑watcher that “monitors” the DB; the monitor is “read whatever is in `db/configs/` right now.”

---

## 5. How to Get PE-2 Into the “Monitored” DB

- **Ensure extraction runs for PE-2:**
  - In `extract_configs.sh`, keep (or add) a line:
    ```bash
    extract_config "100.64.8.39" "PE-2"
    ```
  - Ensure cron (or your run) executes that script so that `db/configs/PE-2/` is created/updated.
- **Ensure monitor sees it:**
  - No extra config: once `db/configs/PE-2/` exists, `monitor.py` will list it and show PE-2 in the device table.
- **Ensure wizard can use it:**
  - Add PE-2 to `db/devices.json` (hostname `"PE-2"`, correct IP, etc.) so the wizard lists it and then reads from `db/configs/PE-2/` when you use that device.

---

## 6. Code References

| What | Where |
|------|--------|
| Monitor’s config dir | `monitor.py` → `configs_dir = SCALER_DIR / "db" / "configs"` |
| “Discover” devices | `monitor.py` → `get_device_status(configs_dir)` → `for device_dir in configs_dir.iterdir()` |
| PE-2 extraction | `extract_configs.sh` → `extract_config "100.64.8.39" "PE-2"` |
| Device config dir | `scaler/utils.py` → `CONFIGS_DIR = DB_DIR / "configs"`; `get_device_config_dir(hostname)` → `CONFIGS_DIR / hostname` |
| Scheduler reading/writing | `scaler/scheduler.py` → uses `get_device_config_dir(device.hostname)`, `running.txt`, `operational.json` |

If you want “monitoring” to mean “only show devices from `devices.json`”, that would require changing `monitor.py` to build the list from `db/devices.json` and then still read status from `db/configs/<hostname>/` for each of those devices.

---

## 7. PE-2 recovery check via console

When PE-2 is in the device list, `monitor.py` can optionally connect to a **console server** (e.g. SSH to `console-b15`, port access option 3, port 13 for PE-2) to read the serial console and detect if PE-2 is in **recovery mode**. This is **detection only**; it does not change the device.

**Important:** The console-based recovery check runs **only when the normal connection via SSH/IP does not work**. If extraction to PE-2 via SSH is succeeding, the monitor does **not** open the console or show a recovery alert.

“Normal connection doesn’t work” is determined by `pe2_normal_connection_failed(stats, devices)` in `monitor.py`:

- PE-2 is in the device list (from `db/configs/`), and **at least one** of:
  - **Last extraction failed:** `extraction.log` shows PE-2’s last extraction as failed (`stats['devices']['PE-2']['last_status'] == 'failed'`).
  - **No config ever received:** PE-2 has no `running.txt` (`has_config` is false).
  - **Config very stale:** `running.txt` last modified more than 15 minutes ago, or more than 2× the extraction period (e.g. extraction every 5 min → stale if older than 10 min in that sense, but floor is 15 min).

Only when that condition is true does the monitor call `check_pe2_recovery_via_console()`. If the console output contains “recovery”, it prints: **USER ALERT: PE-2 is in RECOVERY MODE**.
