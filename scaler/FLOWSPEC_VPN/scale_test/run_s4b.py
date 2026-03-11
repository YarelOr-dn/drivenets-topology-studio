#!/usr/bin/env python3
import sys, time, re, json
sys.stdout = open(sys.stdout.fileno(), "w", buffering=1)
sys.path.insert(0, "/home/dn/SCALER/FLOWSPEC_VPN/scale_test")
from apply_config import apply_config, delete_flowspec_local, run_show
ANSI = re.compile(r'\x1b\[[0-9;]*m')
def gen(count, action, pol):
    L = ["routing-policy", "  flowspec-local-policies", "    ipv4"]
    for i in range(1, count+1):
        p = "tcp(0x06)" if i%2==1 else "udp(0x11)"
        L += [f"      match-class MC4-{i:04d}", f"        dest-ip 10.4.0.{i}/32", f"        protocol {p}", f"        dest-ports {3000+i}", "      !"]
    L += [f"      policy {pol}", "        description test"]
    for i in range(1, count+1):
        L += [f"        match-class MC4-{i:04d}", f"          action {action}", "        !"]
    L += ["      !", "    !", "  !", "!", "forwarding-options", "  flowspec-local", "    ipv4", f"      apply-policy-to-flowspec {pol}", "    !", "  !", "!"]
    return "\n".join(L)
def gen_mixed(dn, rn, pol):
    t = dn + rn
    L = ["routing-policy", "  flowspec-local-policies", "    ipv4"]
    for i in range(1, t+1):
        p = "tcp(0x06)" if i%2==1 else "udp(0x11)"
        L += [f"      match-class MC4-MIX-{i:04d}", f"        dest-ip 10.4.0.{i}/32", f"        protocol {p}", f"        dest-ports {4000+i}", "      !"]
    L += [f"      policy {pol}", "        description mix"]
    for i in range(1, t+1):
        a = "rate-limit 0" if i <= dn else "rate-limit 1000"
        L += [f"        match-class MC4-MIX-{i:04d}", f"          action {a}", "        !"]
    L += ["      !", "    !", "  !", "!", "forwarding-options", "  flowspec-local", "    ipv4", f"      apply-policy-to-flowspec {pol}", "    !", "  !", "!"]
    return "\n".join(L)
def npu():
    o = run_show("show system npu-resources resource-type flowspec")
    c = ANSI.sub("", o)
    m = re.search(r'\|\s*6\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)/12000', c)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else (0,0,0)
R = {}
for tid, act, pol in [("4b","rate-limit 64","POL4B"),("4c","rate-limit 1000","POL4C"),("4d","redirect-to-vrf ZULU","POL4D")]:
    print(f"\n=== {tid}: {act} ===", flush=True)
    delete_flowspec_local(commit=True); time.sleep(10)
    cfg = gen(100, act, pol)
    apply_config(cfg, commit=True); time.sleep(10)
    r,i,h = npu(); loc = i - 13
    print(f"  rcv={r} inst={i} hw={h} local={loc}/100", flush=True)
    R[tid] = {"a":act, "l":loc, "h":h}
print(f"\n=== 4f: mixed ===", flush=True)
delete_flowspec_local(commit=True); time.sleep(10)
cfg = gen_mixed(50, 50, "POL4MIX")
apply_config(cfg, commit=True); time.sleep(10)
r,i,h = npu(); loc = i - 13
print(f"  rcv={r} inst={i} hw={h} local={loc}/100", flush=True)
R["4f"] = {"a":"50drop+50rl1k", "l":loc, "h":h}
json.dump(R, open("/home/dn/SCALER/FLOWSPEC_VPN/scale_test/s4_results.json","w"), indent=2)
print("\nDONE:", R)
