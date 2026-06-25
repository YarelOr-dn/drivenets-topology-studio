# Execution Log -- TEST_mac_mob_basic_SW205160

**Run started:** 2026-05-01T13:38:53+00:00  |  **Primary DUT:** `PE-4`  |  **Dry run:** False  |  **Verdict:** **FAIL**

## Totals

- Total commands issued: **64**
- DNOS-rejected commands: **5**
- By method: `dnos_config_mcp`=64

## Commands per DUT

| Device | Commands |
|---|---|
| `PE-4` | 64 |

## Phase: `setup`

_64 command(s) in this phase._

### 1. [2026-05-01T13:38:53.629+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms

**Command:**

```dnos
show evpn summary | no-more
```

**Output:**

```
Global EVPN parameters
MAC table limit per EVI : 64000
MAC table aging time    : 320s
Control Word            : enabled
FAT Label               : disabled
E-Tree Leaf Label       : 1032383

Number of EVPN instances       : 4
Total local MAC addresses      : 1
Total local MAC-IPs            : 0
Total remote MAC addresses     : 1
Total remote MAC-IPs           : 1
Total VPLS MAC addresses       : 0
Total MAC addresses            : 2
Total MAC-IPs                  : 1
Total suppressed MAC addresses : 0
Total number of interfaces/up  : 4/4
Total number of EVPN neighbors : 1
Total number of VPLS neighbors : 1
Total Local MH ESIs            : 0
Total Local MH ACs             : 0
Total Local MH VPLS ACs        : 0
```

### 2. [2026-05-01T13:38:53.838+00:00] `PE-4` via `dnos_config_mcp` -- 205 ms

**Command:**

```dnos
show bgp summary | no-more
```

**Output:**

```
IPv4 Unicast
---------------------
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 0
Table route limit: 2000000
Table route count: 0
Routes over limit: 0

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567       4526       4611    0     0       0 3d00h47m                   0
  10.99.101.1     4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.2     4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.3     4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.4     4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.5     4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.6     4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.7     4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.8     4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.9     4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.10    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.11    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.12    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.13    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.14    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.15    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.16    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.17    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.18    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.19    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.20    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.21    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.22    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.23    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.24    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.25    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.26    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.27    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.28    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.29    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.30    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.31    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.32    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.33    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.34    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.35    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.36    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.37    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.38    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.39    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.40    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.41    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.42    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.43    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.44    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.45    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.46    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.47    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.48    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.49    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.50    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.51    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.52    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.53    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.54    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.55    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.56    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.57    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.58    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.59    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.60    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.61    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.62    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.63    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.64    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.65    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.66    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.67    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.68    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.69    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.70    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.71    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.72    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.73    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.74    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.75    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.76    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.77    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.78    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.79    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.80    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.81    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.82    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.83    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.84    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.85    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.86    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.87    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.88    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.89    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.90    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.91    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.92    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.93    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.94    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.95    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.96    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.97    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.98    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.99    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.100   4      65200          0          0    0     0       0 never     Idle (Admin)
  100.64.6.134    4      65200       4542       4662    0     0       0 00:45:44                   0

Total number of established neighbors with IPv4 Unicast 2/102

Total number of NSR capable BGP sessions 0

IPv4 Vpn
-------------------------
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 3

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567       4526       4611    0     0       2 3d00h47m                   3
  100.64.6.134    4      65200       4542       4662    0     0       5 00:45:44                   0

Total number of established neighbors with IPv4 Vpn 2/2

Total number of NSR capable BGP sessions 0

IPv4 Flowspec
----------------
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 0

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567       4526       4611    0     0       0 3d00h47m                   0
  100.64.6.134    4      65200       4542       4662    0     0       0 00:45:44                   0
  100.64.6.135    4      65200          0          0    0     0       0 never      Active          

Total number of established neighbors with IPv4 Flowspec 2/3

Total number of NSR capable BGP sessions 0

IPv4 Route Target Constrains
-----------------------------
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 50

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567       4526       4611    0     0      14 3d00h47m                  12

Total number of established neighbors with IPv4 Route Target Constrains 1/1

Total number of NSR capable BGP sessions 0

IPv4 Flowspec-VPN
----------------
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 3

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567       4526       4611    0     0       0 3d00h47m  (NoNeg)
  100.64.6.134    4      65200       4542       4662    0     0       0 00:45:44                   3

Total number of established neighbors with IPv4 Flowspec-VPN 1/2

Total number of NSR capable BGP sessions 0

IPv6 Unicast
---------------------
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 0
Table route limit: 500000
Table route count: 0
Routes over limit: 0

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567       4526       4611    0     0       0 3d00h47m                   0

Total number of established neighbors with IPv6 Unicast 1/1

Total number of NSR capable BGP sessions 0

IPv6 Vpn
-------------------------
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 2

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567       4526       4611    0     0       2 3d00h47m                   1
  100.64.6.134    4      65200       4542       4662    0     0       0 00:45:44  (NoNeg)

Total number of established neighbors with IPv6 Vpn 1/2

Total number of NSR capable BGP sessions 0

IPv6 Flowspec
----------------
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 0

... [truncated: 26 lines omitted; see execution_log.jsonl for full output] ...

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567       4526       4611    0     0       3 3d00h47m                   5

Total number of established neighbors with L2vpn VPLS 1/1

Total number of NSR capable BGP sessions 0

L2vpn EVPN
----------------
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 4

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567       4526       4611    0     0       3 3d00h47m                   4

Total number of established neighbors with L2vpn EVPN 1/1

Total number of NSR capable BGP sessions 0

Total number of established neighbors 2/103
```

### 3. [2026-05-01T13:38:53.889+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms

**Command:**

```dnos
show mpls label-allocation tables | no-more
```

**Output:**

```
In use:

| Protocols                  | Total labels   | Label ranges            |
|----------------------------+----------------+-------------------------|
| bgp-vpls                   | 130            | 1032253-1032382         |
| bgp-evpn-bum               | 8001           | 1032383-1040383         |
| bgp-vrf                    | 8192           | 1040384-1048575         |
| srgb                       | 8000           | 16000-23999             |
| ldp, rsvp, dynamic-sr, bgp | 1015997        | 256-7999, 24000-1032252 |
| srlb                       | 8000           | 8000-15999              |

Configured:

| Protocols   | Total labels   | Label ranges   |
|-------------+----------------+----------------|
| srgb        | 8000           | 16000-23999    |
| srlb        | 8000           | 8000-15999     |
| bgp-vpls    | 130            | N/A            |
```

### 4. [2026-05-01T13:38:54.099+00:00] `PE-4` via `dnos_config_mcp` -- 205 ms

**Command:**

```dnos
show bgp summary | no-more
```

**Output:**

```
IPv4 Unicast
---------------------
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 0
Table route limit: 2000000
Table route count: 0
Routes over limit: 0

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567       4526       4611    0     0       0 3d00h47m                   0
  10.99.101.1     4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.2     4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.3     4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.4     4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.5     4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.6     4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.7     4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.8     4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.9     4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.10    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.11    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.12    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.13    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.14    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.15    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.16    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.17    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.18    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.19    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.20    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.21    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.22    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.23    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.24    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.25    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.26    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.27    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.28    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.29    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.30    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.31    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.32    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.33    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.34    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.35    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.36    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.37    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.38    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.39    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.40    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.41    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.42    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.43    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.44    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.45    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.46    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.47    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.48    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.49    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.50    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.51    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.52    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.53    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.54    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.55    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.56    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.57    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.58    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.59    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.60    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.61    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.62    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.63    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.64    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.65    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.66    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.67    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.68    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.69    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.70    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.71    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.72    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.73    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.74    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.75    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.76    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.77    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.78    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.79    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.80    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.81    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.82    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.83    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.84    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.85    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.86    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.87    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.88    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.89    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.90    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.91    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.92    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.93    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.94    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.95    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.96    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.97    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.98    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.99    4      65200          0          0    0     0       0 never     Idle (Admin)
  10.99.101.100   4      65200          0          0    0     0       0 never     Idle (Admin)
  100.64.6.134    4      65200       4542       4662    0     0       0 00:45:45                   0

Total number of established neighbors with IPv4 Unicast 2/102

Total number of NSR capable BGP sessions 0

IPv4 Vpn
-------------------------
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 3

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567       4526       4611    0     0       2 3d00h47m                   3
  100.64.6.134    4      65200       4542       4662    0     0       5 00:45:45                   0

Total number of established neighbors with IPv4 Vpn 2/2

Total number of NSR capable BGP sessions 0

IPv4 Flowspec
----------------
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 0

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567       4526       4611    0     0       0 3d00h47m                   0
  100.64.6.134    4      65200       4542       4662    0     0       0 00:45:45                   0
  100.64.6.135    4      65200          0          0    0     0       0 never      Active          

Total number of established neighbors with IPv4 Flowspec 2/3

Total number of NSR capable BGP sessions 0

IPv4 Route Target Constrains
-----------------------------
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 50

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567       4526       4611    0     0      14 3d00h47m                  12

Total number of established neighbors with IPv4 Route Target Constrains 1/1

Total number of NSR capable BGP sessions 0

IPv4 Flowspec-VPN
----------------
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 3

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567       4526       4611    0     0       0 3d00h47m  (NoNeg)
  100.64.6.134    4      65200       4542       4662    0     0       0 00:45:45                   3

Total number of established neighbors with IPv4 Flowspec-VPN 1/2

Total number of NSR capable BGP sessions 0

IPv6 Unicast
---------------------
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 0
Table route limit: 500000
Table route count: 0
Routes over limit: 0

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567       4526       4611    0     0       0 3d00h47m                   0

Total number of established neighbors with IPv6 Unicast 1/1

Total number of NSR capable BGP sessions 0

IPv6 Vpn
-------------------------
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 2

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567       4526       4611    0     0       2 3d00h47m                   1
  100.64.6.134    4      65200       4542       4662    0     0       0 00:45:45  (NoNeg)

Total number of established neighbors with IPv6 Vpn 1/2

Total number of NSR capable BGP sessions 0

IPv6 Flowspec
----------------
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 0

... [truncated: 26 lines omitted; see execution_log.jsonl for full output] ...

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567       4526       4611    0     0       3 3d00h47m                   5

Total number of established neighbors with L2vpn VPLS 1/1

Total number of NSR capable BGP sessions 0

L2vpn EVPN
----------------
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 4

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567       4526       4611    0     0       3 3d00h47m                   4

Total number of established neighbors with L2vpn EVPN 1/1

Total number of NSR capable BGP sessions 0

Total number of established neighbors 2/103
```

### 5. [2026-05-01T13:38:54.150+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms

**Command:**

```dnos
show config protocols isis | flatten | include area-id | no-more
```

**Output:**

```
(empty)
```

### 6. [2026-05-01T13:38:54.251+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms

**Command:**

```dnos
show interfaces lo0 | no-more
```

**Output:**

```
Interface lo0
	SNMP ifindex: 8193, Network-Service: VRF (default)
	Admin state: enabled, Operational state: up, Uptime: 4 days, 4:58:38
	Description: 
	MAC Address: N/A
	Speed: N/A, Duplex: N/A, Bundle-id: N/A
	MPLS: disabled, MTU: 1514
	IPv4 Address: 4.4.4.4/32
	Secondary IPv4 addresses: N/A
	IPv6 Admin state: enabled, IPv6 link-local address: N/A, Status: N/A
	IPv6 global unicast address(es): N/A
	NDP Router-advertisement
		Prefix-advertisement: disabled
	Encapsulation: ethernet
	L2 originated VLAN tags: N/A
	Access-list IPv4: In: N/A, Out: N/A
	Access-list IPv6: In: N/A, Out: N/A
	Access-list Eth: In: N/A, Out: N/A
```

### 7. [2026-05-01T13:38:54.405+00:00] `PE-4` via `dnos_config_mcp` -- 152 ms

**Command:**

```dnos
show interfaces management | no-more
```

**Output:**

```
Legend: p - primary IP address (has secondaries), d - obtained via DHCP


| Interface            |       Admin        | Operational     | IPv4 Address           | IPv6 Address                                | MTU  |
+----------------------+--------------------+-----------------+------------------------+---------------------------------------------+------+
| console-ncc-0/0      |      enabled       | up              |                        |                                             | N/A  |
| console-ncc-1/0      |      enabled       | up              |                        |                                             | N/A  |
| console-ncf-0/0      |      enabled       | up              |                        |                                             | N/A  |
| console-ncf-1/0      |      enabled       | up              |                        |                                             | N/A  |
| console-ncf-2/0      |      enabled       | up              |                        |                                             | N/A  |
| console-ncf-3/0      |      enabled       | up              |                        |                                             | N/A  |
| console-ncf-4/0      |      enabled       | up              |                        |                                             | N/A  |
| console-ncf-5/0      |      enabled       | up              |                        |                                             | N/A  |
| console-ncp-6/0      |      enabled       | up              |                        |                                             | N/A  |
| console-ncp-18/0     |      enabled       | up              |                        |                                             | N/A  |
| ipmi-ncc-0/0         |      enabled       | not-present     |                        |                                             | N/A  |
| ipmi-ncc-1/0         |      enabled       | not-present     |                        |                                             | N/A  |
| ipmi-ncf-0/0         |      enabled       | up              | 100.64.2.111 (d)       |                                             | 1514 |
| ipmi-ncf-1/0         |      enabled       | not-present     |                        |                                             | N/A  |
| ipmi-ncf-2/0         |      enabled       | not-present     |                        |                                             | N/A  |
| ipmi-ncf-3/0         |      enabled       | not-present     |                        |                                             | N/A  |
| ipmi-ncf-4/0         |      enabled       | not-present     |                        |                                             | N/A  |
| ipmi-ncf-5/0         |      enabled       | not-present     |                        |                                             | N/A  |
| ipmi-ncp-6/0         |      enabled       | not-present     |                        |                                             | N/A  |
| ipmi-ncp-18/0        |      enabled       | up              | 100.64.5.7 (d)         |                                             | 1514 |
| mgmt0                |      enabled       | up              | 100.64.10.22/20 (d)    |                                             | 1514 |
| mgmt-ncc-0           |      enabled       | up              | 100.64.11.96/20 (d)    |                                             | 9000 |
| mgmt-ncc-0/0         |      enabled       | up              |                        |                                             | 9300 |
| mgmt-ncc-0/1         |     not-exists     |                 |                        |                                             |      |
| mgmt-ncc-1           |      enabled       | up              | 100.64.4.122/20 (d)    |                                             | 9000 |
| mgmt-ncc-1/0         |      enabled       | up              |                        |                                             | 9300 |
| mgmt-ncc-1/1         |     not-exists     |                 |                        |                                             |      |
```

### 8. [2026-05-01T13:38:54.457+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms

**Command:**

```dnos
show mpls label-allocation tables | no-more
```

**Output:**

```
In use:

| Protocols                  | Total labels   | Label ranges            |
|----------------------------+----------------+-------------------------|
| bgp-vpls                   | 130            | 1032253-1032382         |
| bgp-evpn-bum               | 8001           | 1032383-1040383         |
| bgp-vrf                    | 8192           | 1040384-1048575         |
| srgb                       | 8000           | 16000-23999             |
| ldp, rsvp, dynamic-sr, bgp | 1015997        | 256-7999, 24000-1032252 |
| srlb                       | 8000           | 8000-15999              |

Configured:

| Protocols   | Total labels   | Label ranges   |
|-------------+----------------+----------------|
| srgb        | 8000           | 16000-23999    |
| srlb        | 8000           | 8000-15999     |
| bgp-vpls    | 130            | N/A            |
```

### 9. [2026-05-01T13:38:54.558+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms

**Command:**

```dnos
show config protocols bgp 1234567 | flatten | include l2vpn-vpls | no-more
```

**Output:**

```
protocols bgp 1234567 neighbor 2.2.2.2 address-family l2vpn-vpls send-community community-type both
protocols bgp 1234567 neighbor 2.2.2.2 address-family l2vpn-vpls soft-reconfiguration inbound
```

### 10. [2026-05-01T13:38:54.609+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms

**Command:**

```dnos
show config network-services evpn instance EVPN_SI_VPLS_1 | no-more
```

**Output:**

```
# YOR_CL_PE-4 config-start [01-May-2026 16:38:54 UTC+03:00 (Israel)]

network-services
  evpn
    instance EVPN_SI_VPLS_1
      description "VPLS-SI-PW1 RD=4.4.4.4:1001 RT=1234567:2001 site=4001 PW-PW-mobility-3rd-site"
      protocols
        bgp 1234567
          export-l2vpn-evpn route-target 1234567:2001
          import-l2vpn-evpn route-target 1234567:2001
          route-distinguisher 4.4.4.4:1001
        !
      !
      transport-protocol
        mpls
          control-word enabled
          fat-label disabled
        !
      !
      seamless-integration
        protocols
          bgp
            export-l2vpn-vpls route-target 1234567:2001
            import-l2vpn-vpls route-target 1234567:2001
          !
        !
        label-block-size 8
        source-if lo0
        site-id 4001
          site-interface ge100-18/0/1
        !
      !
      interface ge100-18/0/1
      !
    !
  !
!

# YOR_CL_PE-4 config-end
```

### 11. [2026-05-01T13:38:54.760+00:00] `PE-4` via `dnos_config_mcp` -- 150 ms

**Command:**

```dnos
show config interfaces ge100-18/0/1 | no-more
```

**Output:**

```
# YOR_CL_PE-4 config-start [01-May-2026 16:38:54 UTC+03:00 (Israel)]

interfaces
  ge100-18/0/1
    admin-state enabled
    description "EVPN_SI_VPLS_1 PW-source AC port-mode (Spirent->B14.211->fab211->B10.4->PE4)"
    fec none
    ipv6-admin-state disabled
    l2-service enabled
  !
!

# YOR_CL_PE-4 config-end
```

### 12. [2026-05-01T13:38:54.861+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms

**Command:**

```dnos
show config protocols bgp 1234567 | flatten | include 17.17.17.2 | no-more
```

**Output:**

```
(empty)
```

### 13. [2026-05-01T13:38:54.962+00:00] `PE-4` via `dnos_config_mcp` -- 101 ms

**Command:**

```dnos
show evpn vpls-pw | no-more
```

**Output:**

```
EVPN: EVPN_SI_AC_PW_test
    EVI ID : 3
    Seamless-integration: enabled
    Control-word: enabled
    Fat-label: disabled
  
    VPLS PW table is empty
  

   EVPN: EVPN_SI_VPLS_1
    EVI ID : 2
    Seamless-integration: enabled
    Control-word: enabled
    Fat-label: disabled
  
    VPLS PWs:
  
    | IP Address        | Remote Site Id   | Ingress-label   | Local site-id   | Egress-label   | Status        |
    +-------------------+------------------+-----------------+-----------------+----------------+---------------+
    | 2.2.2.2           | 2001             | 1032269         | 4001            | 1032335        | Installed     |
  

   EVPN: EVPN_SI_VPLS_2
    EVI ID : 4
    Seamless-integration: disabled
  
    VPLS PW table is empty
  

   EVPN: VPLS_SI-1
    EVI ID : 1
    Seamless-integration: enabled
    Control-word: enabled
    Fat-label: disabled
  
    VPLS PW table is empty
```

### 14. [2026-05-01T13:38:55.013+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms

**Command:**

```dnos
show config protocols bgp 1234567 | flatten | include 18.18.18.2 | no-more
```

**Output:**

```
(empty)
```

### 15. [2026-05-01T13:38:55.064+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms

**Command:**

```dnos
show mpls label-allocation tables | no-more
```

**Output:**

```
In use:

| Protocols                  | Total labels   | Label ranges            |
|----------------------------+----------------+-------------------------|
| bgp-vpls                   | 130            | 1032253-1032382         |
| bgp-evpn-bum               | 8001           | 1032383-1040383         |
| bgp-vrf                    | 8192           | 1040384-1048575         |
| srgb                       | 8000           | 16000-23999             |
| ldp, rsvp, dynamic-sr, bgp | 1015997        | 256-7999, 24000-1032252 |
| srlb                       | 8000           | 8000-15999              |

Configured:

| Protocols   | Total labels   | Label ranges   |
|-------------+----------------+----------------|
| srgb        | 8000           | 16000-23999    |
| srlb        | 8000           | 8000-15999     |
| bgp-vpls    | 130            | N/A            |
```

### 16. [2026-05-01T13:38:55.165+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms

**Command:**

```dnos
show config protocols bgp 1234567 | flatten | include l2vpn-vpls | no-more
```

**Output:**

```
protocols bgp 1234567 neighbor 2.2.2.2 address-family l2vpn-vpls send-community community-type both
protocols bgp 1234567 neighbor 2.2.2.2 address-family l2vpn-vpls soft-reconfiguration inbound
```

### 17. [2026-05-01T13:38:55.317+00:00] `PE-4` via `dnos_config_mcp` -- 150 ms

**Command:**

```dnos
show config interfaces ge100-18/0/1 | no-more
```

**Output:**

```
# YOR_CL_PE-4 config-start [01-May-2026 16:38:55 UTC+03:00 (Israel)]

interfaces
  ge100-18/0/1
    admin-state enabled
    description "EVPN_SI_VPLS_1 PW-source AC port-mode (Spirent->B14.211->fab211->B10.4->PE4)"
    fec none
    ipv6-admin-state disabled
    l2-service enabled
  !
!

# YOR_CL_PE-4 config-end
```

### 18. [2026-05-01T13:38:55.417+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms

**Command:**

```dnos
config
```

**Output:**

```
(empty)
```

### 19. [2026-05-01T13:38:55.519+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms

**Command:**

```dnos
interfaces ge100-18/0/1
```

**Output:**

```
(empty)
```

### 20. [2026-05-01T13:38:55.569+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms

**Command:**

```dnos
admin-state enabled
```

**Output:**

```
(empty)
```

### 21. [2026-05-01T13:38:55.620+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms

**Command:**

```dnos
l2-service enabled
```

**Output:**

```
(empty)
```

### 22. [2026-05-01T13:38:55.671+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms **REJECTED**

**Command:**

```dnos
vlan-tags outer-tag 214 inner-tag 1010
```

**Output:**

```
ERROR: Unknown word: 'vlan-tags'.
```

### 23. [2026-05-01T13:38:55.722+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms

**Command:**

```dnos
top
```

**Output:**

```
(empty)
```

### 24. [2026-05-01T13:38:55.822+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms

**Command:**

```dnos
commit check
```

**Output:**

```
NOTICE: commit action is not applicable. no configuration changes were made
```

### 25. [2026-05-01T13:38:55.923+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms

**Command:**

```dnos
commit
```

**Output:**

```
(empty)
```

### 26. [2026-05-01T13:38:56.024+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms

**Command:**

```dnos
end
```

**Output:**

```
(empty)
```

### 27. [2026-05-01T13:38:56.075+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms

**Command:**

```dnos
show config network-services evpn instance EVPN_SI_VPLS_1 | no-more
```

**Output:**

```
# YOR_CL_PE-4 config-start [01-May-2026 16:38:56 UTC+03:00 (Israel)]

network-services
  evpn
    instance EVPN_SI_VPLS_1
      description "VPLS-SI-PW1 RD=4.4.4.4:1001 RT=1234567:2001 site=4001 PW-PW-mobility-3rd-site"
      protocols
        bgp 1234567
          export-l2vpn-evpn route-target 1234567:2001
          import-l2vpn-evpn route-target 1234567:2001
          route-distinguisher 4.4.4.4:1001
        !
      !
      transport-protocol
        mpls
          control-word enabled
          fat-label disabled
        !
      !
      seamless-integration
        protocols
          bgp
            export-l2vpn-vpls route-target 1234567:2001
            import-l2vpn-vpls route-target 1234567:2001
          !
        !
        label-block-size 8
        source-if lo0
        site-id 4001
          site-interface ge100-18/0/1
        !
      !
      interface ge100-18/0/1
      !
    !
  !
!

# YOR_CL_PE-4 config-end
```

### 28. [2026-05-01T13:38:56.126+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms

**Command:**

```dnos
show config network-services evpn instance EVPN_SI_VPLS_1 seamless-integration | flatten | no-more
```

**Output:**

```
# YOR_CL_PE-4 config-start [01-May-2026 16:38:56 UTC+03:00 (Israel)]

network-services evpn instance EVPN_SI_VPLS_1 seamless-integration protocols bgp export-l2vpn-vpls route-target 1234567:2001
network-services evpn instance EVPN_SI_VPLS_1 seamless-integration protocols bgp import-l2vpn-vpls route-target 1234567:2001
network-services evpn instance EVPN_SI_VPLS_1 seamless-integration label-block-size 8
network-services evpn instance EVPN_SI_VPLS_1 seamless-integration source-if lo0
network-services evpn instance EVPN_SI_VPLS_1 seamless-integration site-id 4001 site-interface ge100-18/0/1

# YOR_CL_PE-4 config-end
```

### 29. [2026-05-01T13:38:56.177+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms

**Command:**

```dnos
show config protocols bgp 1234567 | flatten | include 17.17.17.2 | no-more
```

**Output:**

```
(empty)
```

### 30. [2026-05-01T13:38:56.228+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms

**Command:**

```dnos
show config protocols bgp 1234567 | flatten | include 6.6.6.6 | no-more
```

**Output:**

```
(empty)
```

### 31. [2026-05-01T13:38:56.329+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms

**Command:**

```dnos
config
```

**Output:**

```
(empty)
```

### 32. [2026-05-01T13:38:56.429+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms

**Command:**

```dnos
protocols bgp 1234567 neighbor 17.17.17.2
```

**Output:**

```
(empty)
```

### 33. [2026-05-01T13:38:56.480+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms

**Command:**

```dnos
admin-state enabled
```

**Output:**

```
(empty)
```

### 34. [2026-05-01T13:38:56.581+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms

**Command:**

```dnos
remote-as 1234567
```

**Output:**

```
(empty)
```

### 35. [2026-05-01T13:38:56.631+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms

**Command:**

```dnos
update-source ge400-0/0/5.3
```

**Output:**

```
(empty)
```

### 36. [2026-05-01T13:38:56.682+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms

**Command:**

```dnos
top
```

**Output:**

```
(empty)
```

### 37. [2026-05-01T13:38:56.733+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms **REJECTED**

**Command:**

```dnos
config
```

**Output:**

```
ERROR: Unknown word.
```

### 38. [2026-05-01T13:38:56.834+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms

**Command:**

```dnos
protocols bgp 1234567 neighbor 17.17.17.2
```

**Output:**

```
(empty)
```

### 39. [2026-05-01T13:38:56.934+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms

**Command:**

```dnos
address-family l2vpn-vpls
```

**Output:**

```
(empty)
```

### 40. [2026-05-01T13:38:56.985+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms

**Command:**

```dnos
send-community community-type both
```

**Output:**

```
(empty)
```

### 41. [2026-05-01T13:38:57.086+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms

**Command:**

```dnos
soft-reconfiguration inbound
```

**Output:**

```
(empty)
```

### 42. [2026-05-01T13:38:57.136+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms

**Command:**

```dnos
top
```

**Output:**

```
(empty)
```

### 43. [2026-05-01T13:38:57.287+00:00] `PE-4` via `dnos_config_mcp` -- 150 ms

**Command:**

```dnos
commit check
```

**Output:**

```
ERROR: Can't configure update-source ge400-0/0/5.3. Interface must exist.
```

### 44. [2026-05-01T13:38:57.338+00:00] `PE-4` via `dnos_config_mcp` -- 50 ms

**Command:**

```dnos
rollback 0
```

**Output:**

```
(empty)
```

### 45. [2026-05-01T13:38:57.439+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms

**Command:**

```dnos
end
```

**Output:**

```
(empty)
```

### 46. [2026-05-01T13:38:57.542+00:00] `PE-4` via `dnos_config_mcp` -- 102 ms

**Command:**

```dnos
show evpn instance EVPN_SI_VPLS_1 detail | no-more
```

**Output:**

```
EVPN: EVPN_SI_VPLS_1
  EVI ID : 2
  Description : VPLS-SI-PW1 RD=4.4.4.4:1001 RT=1234567:2001 site=4001 PW-PW-mobility-3rd-site
  Route Distinguisher            : 4.4.4.4:1001
  Transport protocol             : mpls
  Fat label                      : disabled
  Control word                   : enabled
  MAC learning                   : enabled
  Allocated unicast label        : 265
  Allocated IM label             : 1032385
  E-Tree Configuration           : Root

  MAC Table
  =========
  MAC table limit                : 64000
  MAC table aging time           : 320s
  Number of local entries        : 1
  Number of VPLS PW entries      : 0
  Number of remote entries       : 1
  Number of moved events         : 0
  Total entries                  : 2

  MAC IP Table
  ============
  MAC IP table limit             : 8192
  MAC IP table aging time        : 20 min
  Number of local entries        : 0
  Number of remote entries       : 1
  Total entries                  : 1

  MAC Mobility
  ============
  Loop Prevention                : enabled
  Loop Prevention Action         : suppress
  Loop Detection Threshold       : 5
  Loop Detection Window          : 180s
  IP Loop Detection Threshold    : 5
  IP Loop Detection Window       : 180s
  Mac Restore Timer              : 300s
  Mac Restore Max Cycles         : infinite
  Mac Restore Reset Interval     : 24h
  Number of suppressed entries   : 0

  Traffic counters
  ================
  RX Octets                      : 0
  RX Packets                     : 0
  RX Rate                        : 0 Mbps
  RX Known Unicast Packets       : 0
  RX BUM Packets                 : 0
  TX Octets                      : 0
  TX Packets                     : 0
  TX Rate                        : 0 Mbps
  TX Known Unicast Packets       : 0
  TX BUM Packets                 : 0

  Number of EVPN neighbors : 1
  | IP Address                        | IM Type-3   | MAC Type-2   | MAC/IP Type-2   | AD Type-1 EVI/ESI   | IM Label   | Leaf Label   |
  +-----------------------------------+-------------+--------------+-----------------+---------------------+------------+--------------+
  | 1.1.1.1                           | 1           | 1            | 1               | 0/0                 | 1032384    |              |

  Number of EVPN interfaces : 1
  | Associated interfaces   | State   / Forwarding State                                   | Uptime              | Actual Local Homing Type    | ESI                             | Learned MACs   |
  +-------------------------+--------------------------------------------------------------+---------------------+-----------------------------+---------------------------------+----------------+
  | ge100-18/0/1            | up / forwarding-all                                          | 2 days, 0:14:48     | single-homed                |                                 | 1              |

  (I) - DF Election Highest Preference, Invert Preference is enabled for this interface.

  (L) - Leaf Interface.

  Seamless-integration:
  =====================
  Label Block Size       : 8
  Control Word           : enabled
  FAT Label              : disabled
  L2 MTU                 : 0
  Source Interface       : lo0

  | Local Site-ID (VE-ID)  | Homing-type   | Preference  | Role    | DF IP            |
  +------------------------+---------------+-------------+---------+------------------+
  | 4001                   | single-homed  | 100         | DF      | 4.4.4.4          |

  BGP-VPLS neighbors (Seamless-integration):
  Flags codes: F - FAT-label, Fs - FAT-label-Send, Fr - FAT-label-Receive,
               C - control-word, d - designated-forwarder, s - stale, D - down

  | VE-ID   | Offset  | Nexthop                  | Preference   | Label-Base   | Control-Flags   | L2 MTU   | Failed reason              |
  +---------+---------+--------------------------+--------------+--------------+-----------------+----------+----------------------------+
  | 2001    | 4001    | 2.2.2.2                  | 100          | 1032335      | C               | 0        |                            |
  | 4001    | 2001    | 4.4.4.4 (self)           | 100          | 1032269      | C               | 0        |                            |
  |         | 4001    | 4.4.4.4 (self)           | 100          | 1032261      | C/d             | 0        |                            |

  VPLS PWs:

  | IP Address        | Remote Site Id   | Ingress-label   | Local site-id   | Egress-label   | Status        |
  +-------------------+------------------+-----------------+-----------------+----------------+---------------+
  | 2.2.2.2           | 2001             | 1032269         | 4001            | 1032335        | Installed     |

  Number of local multihomed ACs (ethernet segments): 0
```

### 47. [2026-05-01T13:38:57.648+00:00] `PE-4` via `dnos_config_mcp` -- 102 ms

**Command:**

```dnos
show evpn instance EVPN_SI_VPLS_1 detail | no-more
```

**Output:**

```
EVPN: EVPN_SI_VPLS_1
  EVI ID : 2
  Description : VPLS-SI-PW1 RD=4.4.4.4:1001 RT=1234567:2001 site=4001 PW-PW-mobility-3rd-site
  Route Distinguisher            : 4.4.4.4:1001
  Transport protocol             : mpls
  Fat label                      : disabled
  Control word                   : enabled
  MAC learning                   : enabled
  Allocated unicast label        : 265
  Allocated IM label             : 1032385
  E-Tree Configuration           : Root

  MAC Table
  =========
  MAC table limit                : 64000
  MAC table aging time           : 320s
  Number of local entries        : 1
  Number of VPLS PW entries      : 0
  Number of remote entries       : 1
  Number of moved events         : 0
  Total entries                  : 2

  MAC IP Table
  ============
  MAC IP table limit             : 8192
  MAC IP table aging time        : 20 min
  Number of local entries        : 0
  Number of remote entries       : 1
  Total entries                  : 1

  MAC Mobility
  ============
  Loop Prevention                : enabled
  Loop Prevention Action         : suppress
  Loop Detection Threshold       : 5
  Loop Detection Window          : 180s
  IP Loop Detection Threshold    : 5
  IP Loop Detection Window       : 180s
  Mac Restore Timer              : 300s
  Mac Restore Max Cycles         : infinite
  Mac Restore Reset Interval     : 24h
  Number of suppressed entries   : 0

  Traffic counters
  ================
  RX Octets                      : 0
  RX Packets                     : 0
  RX Rate                        : 0 Mbps
  RX Known Unicast Packets       : 0
  RX BUM Packets                 : 0
  TX Octets                      : 0
  TX Packets                     : 0
  TX Rate                        : 0 Mbps
  TX Known Unicast Packets       : 0
  TX BUM Packets                 : 0

  Number of EVPN neighbors : 1
  | IP Address                        | IM Type-3   | MAC Type-2   | MAC/IP Type-2   | AD Type-1 EVI/ESI   | IM Label   | Leaf Label   |
  +-----------------------------------+-------------+--------------+-----------------+---------------------+------------+--------------+
  | 1.1.1.1                           | 1           | 1            | 1               | 0/0                 | 1032384    |              |

  Number of EVPN interfaces : 1
  | Associated interfaces   | State   / Forwarding State                                   | Uptime              | Actual Local Homing Type    | ESI                             | Learned MACs   |
  +-------------------------+--------------------------------------------------------------+---------------------+-----------------------------+---------------------------------+----------------+
  | ge100-18/0/1            | up / forwarding-all                                          | 2 days, 0:14:48     | single-homed                |                                 | 1              |

  (I) - DF Election Highest Preference, Invert Preference is enabled for this interface.

  (L) - Leaf Interface.

  Seamless-integration:
  =====================
  Label Block Size       : 8
  Control Word           : enabled
  FAT Label              : disabled
  L2 MTU                 : 0
  Source Interface       : lo0

  | Local Site-ID (VE-ID)  | Homing-type   | Preference  | Role    | DF IP            |
  +------------------------+---------------+-------------+---------+------------------+
  | 4001                   | single-homed  | 100         | DF      | 4.4.4.4          |

  BGP-VPLS neighbors (Seamless-integration):
  Flags codes: F - FAT-label, Fs - FAT-label-Send, Fr - FAT-label-Receive,
               C - control-word, d - designated-forwarder, s - stale, D - down

  | VE-ID   | Offset  | Nexthop                  | Preference   | Label-Base   | Control-Flags   | L2 MTU   | Failed reason              |
  +---------+---------+--------------------------+--------------+--------------+-----------------+----------+----------------------------+
  | 2001    | 4001    | 2.2.2.2                  | 100          | 1032335      | C               | 0        |                            |
  | 4001    | 2001    | 4.4.4.4 (self)           | 100          | 1032269      | C               | 0        |                            |
  |         | 4001    | 4.4.4.4 (self)           | 100          | 1032261      | C/d             | 0        |                            |

  VPLS PWs:

  | IP Address        | Remote Site Id   | Ingress-label   | Local site-id   | Egress-label   | Status        |
  +-------------------+------------------+-----------------+-----------------+----------------+---------------+
  | 2.2.2.2           | 2001             | 1032269         | 4001            | 1032335        | Installed     |

  Number of local multihomed ACs (ethernet segments): 0
```

### 48. [2026-05-01T13:38:57.849+00:00] `PE-4` via `dnos_config_mcp` -- 200 ms

**Command:**

```dnos
show bgp l2vpn evpn summary | no-more
```

**Output:**

```
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 4

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567       4526       4611    0     0       3 3d00h47m                   4

Total number of established neighbors with L2vpn EVPN 1/1

Total number of NSR capable BGP sessions 0
```

### 49. [2026-05-01T13:38:57.950+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms

**Command:**

```dnos
show evpn instance EVPN_SI_VPLS_1 vpls-pw | no-more
```

**Output:**

```
EVPN: EVPN_SI_VPLS_1
    EVI ID : 2
    Seamless-integration: enabled
    Control-word: enabled
    Fat-label: disabled
  
    VPLS PWs:
  
    | IP Address        | Remote Site Id   | Ingress-label   | Local site-id   | Egress-label   | Status        |
    +-------------------+------------------+-----------------+-----------------+----------------+---------------+
    | 2.2.2.2           | 2001             | 1032269         | 4001            | 1032335        | Installed     |
```

### 50. [2026-05-01T13:39:07.325+00:00] `PE-4` via `dnos_config_mcp` -- 201 ms

**Command:**

```dnos
show bgp l2vpn evpn summary | no-more
```

**Output:**

```
BGP router identifier 4.4.4.4, local AS number 1234567
BGP table node count 4

  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567       4527       4612    0     0       3 3d00h48m                   4

Total number of established neighbors with L2vpn EVPN 1/1

Total number of NSR capable BGP sessions 0
```

### 51. [2026-05-01T13:39:15.136+00:00] `PE-4` via `dnos_config_mcp` -- 201 ms

**Command:**

```dnos
show evpn mac-table instance EVPN_SI_VPLS_1 mac 00:DE:AD:FF:FF:01 | no-more
```

**Output:**

```
(empty)
```

### 52. [2026-05-01T13:39:16.338+00:00] `PE-4` via `dnos_config_mcp` -- 201 ms

**Command:**

```dnos
show evpn mac-table instance EVPN_SI_VPLS_1 mac 00:DE:AD:FF:FF:01 | no-more
```

**Output:**

```
(empty)
```

### 53. [2026-05-01T13:39:17.540+00:00] `PE-4` via `dnos_config_mcp` -- 200 ms

**Command:**

```dnos
show evpn mac-table instance EVPN_SI_VPLS_1 mac 00:DE:AD:FF:FF:01 | no-more
```

**Output:**

```
(empty)
```

### 54. [2026-05-01T13:39:18.742+00:00] `PE-4` via `dnos_config_mcp` -- 200 ms

**Command:**

```dnos
show evpn mac-table instance EVPN_SI_VPLS_1 mac 00:DE:AD:FF:FF:01 | no-more
```

**Output:**

```
(empty)
```

### 55. [2026-05-01T13:39:19.944+00:00] `PE-4` via `dnos_config_mcp` -- 200 ms

**Command:**

```dnos
show evpn mac-table instance EVPN_SI_VPLS_1 mac 00:DE:AD:FF:FF:01 | no-more
```

**Output:**

```
(empty)
```

### 56. [2026-05-01T13:39:21.146+00:00] `PE-4` via `dnos_config_mcp` -- 200 ms

**Command:**

```dnos
show evpn mac-table instance EVPN_SI_VPLS_1 mac 00:DE:AD:FF:FF:01 | no-more
```

**Output:**

```
(empty)
```

### 57. [2026-05-01T13:39:22.348+00:00] `PE-4` via `dnos_config_mcp` -- 200 ms

**Command:**

```dnos
show evpn mac-table instance EVPN_SI_VPLS_1 mac 00:DE:AD:FF:FF:01 | no-more
```

**Output:**

```
(empty)
```

### 58. [2026-05-01T13:39:23.550+00:00] `PE-4` via `dnos_config_mcp` -- 200 ms

**Command:**

```dnos
show evpn mac-table instance EVPN_SI_VPLS_1 mac 00:DE:AD:FF:FF:01 | no-more
```

**Output:**

```
(empty)
```

### 59. [2026-05-01T13:39:24.752+00:00] `PE-4` via `dnos_config_mcp` -- 200 ms

**Command:**

```dnos
show evpn mac-table instance EVPN_SI_VPLS_1 mac 00:DE:AD:FF:FF:01 | no-more
```

**Output:**

```
(empty)
```

### 60. [2026-05-01T13:39:25.136+00:00] `PE-4` via `dnos_config_mcp` -- 200 ms

**Command:**

```dnos
show evpn mac-table instance EVPN_SI_VPLS_1 mac 00:DE:AD:FF:FF:01 | no-more
```

**Output:**

```
(empty)
```

### 61. [2026-05-01T13:39:29.206+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms

**Command:**

```dnos
clear evpn mac-table
```

**Output:**

```
(empty)
```

### 62. [2026-05-01T13:39:29.309+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms **REJECTED**

**Command:**

```dnos
show file traces routing_engine/bgpd_traces | include  | no-more
```

**Output:**

```
ERROR: Incomplete command.
```

### 63. [2026-05-01T13:39:29.410+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms **REJECTED**

**Command:**

```dnos
show file traces routing_engine/fibmgrd_traces | include  | no-more
```

**Output:**

```
ERROR: Incomplete command.
```

### 64. [2026-05-01T13:39:29.510+00:00] `PE-4` via `dnos_config_mcp` -- 100 ms **REJECTED**

**Command:**

```dnos
show file traces routing_engine/rib-manager_traces | include  | no-more
```

**Output:**

```
ERROR: Incomplete command.
```

---

_Full untrimmed outputs are in `execution_log.jsonl` (one JSON record per command). Quick stats are in `execution_log_stats.json`._
