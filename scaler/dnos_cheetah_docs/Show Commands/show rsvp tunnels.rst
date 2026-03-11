show rsvp tunnels
-----------------

**Minimum user role:** viewer

To display the RSVP tunnel information:

**Command syntax: show rsvp tunnels** {name [tunnel-name] \| destination [destination] \| state [state] \|auto-mesh [template-name]} detail

**Command mode:** operational



.. 
	**Internal Note**

	- set name to display detailed information for tunnels matching the name

	- set destination to display detailed information for tunnels matching the destination

	- set state to display brief information for tunnel matching the state

	- set auto-mesh to display only tunnels created due to auto-mesh

	- set auto-mesh [template] to display only tunnels created due to auto-mesh from a specific template

	- set detail to display tunnel detailed information.

	- "detail" cannot be set together with name or destination


**Parameter table**

+---------------+--------------------------------------------------------------------------------------+-------------------+
| Parameter     | Description                                                                          | Range             |
+===============+======================================================================================+===================+
| no filter     | Displays all RSVP tunnels                                                            | \-                |
+---------------+--------------------------------------------------------------------------------------+-------------------+
| tunnel-name   | Filters the information displayed for the specified tunnel                           | 1..255 characters |
+---------------+--------------------------------------------------------------------------------------+-------------------+
| destination   | Filters the information displayed by destination                                     | A.B.C.D           |
+---------------+--------------------------------------------------------------------------------------+-------------------+
| state         | Filters the information by tunnel's state (up/down)                                  | up                |
|               |                                                                                      | down              |
|               |                                                                                      | admin-down        |
+---------------+--------------------------------------------------------------------------------------+-------------------+
| auto-mesh     | Filters the information to auto-mesh generated tunnels                               | \-                |
+---------------+--------------------------------------------------------------------------------------+-------------------+
| template-name | Filters the information to the specified auto-mesh template                          | String            |
+---------------+--------------------------------------------------------------------------------------+-------------------+
| detail        | Displays detailed tunnel information. Does not apply to name or destination filters. | \-                |
+---------------+--------------------------------------------------------------------------------------+-------------------+

**Example**
::

	dnRouter# show rsvp tunnels

	Legend: * - Make-Before-Break

	Destination     Source          Role     State   LabelIn LabelOut Uptime/Downtime    Name
	----------------------------------------------------------------------------------------------
	100.0.0.2       101.0.0.18      head     AdminDn -       -        2d12h25m           to-p2
	100.0.0.3       101.0.0.18      head     up      -       70595    2d12h7m            auto_tunnel_sysp18_sysp3_P_CC_D_R1_3
	100.0.0.3       101.0.0.18      head     up      -       70645    2d12h7m            auto_tunnel_sysp18_sysp3_P_CC_P_R1_4
	100.0.0.3       101.0.0.18      head     AdminDn -       -        2d12h25m           to-p3
	101.0.0.17      101.0.0.18      head     up      -       0        2d12h7m            auto_tunnel_sysp18_sysp17_P_CC_D_R1_10
	101.0.0.17      101.0.0.18      head     up      -       0        2d12h7m            auto_tunnel_sysp18_sysp17_P_CC_P_R1_11
	101.0.1.100     101.0.0.19      head     down    -       -        3d15h57m           P19-P100-PRIORITY



	dnRouter# show rsvp tunnels name tunnel1
	tunnel1: head, up (Operational) 45m18s
	  Created: Thu Jun 21 11:27:45 2018
	  Source: 10.10.10.10, Destination: 30.30.30.30
	  Tunnel-id: 1, Extended-tunnel-id: 10.10.10.10
	  Lsp-id: 1, primary
	  Lsp-local-id: 1
	  Bandwidth: 1000Kbps, Bandwidth Configured: 0kbps
      Load-Balancing: weighted-ecmp, Weight: 1000 (tunnel-bw)
	  Class-Type: ct0
	  Priority: Setup: 7, Hold: 7
	  Hop-limit: 60
	  Auto-bandwidth: enabled
	     Last requested BW: 2500kbps, trigger: Adjustment interval, reason: Adjustment threshold, BW increase
	     Avg-rate sample(min/max/last): 10/3000/2234 kbps
	     Overflow: bandwidth 200kbps, percent 10%, limit 3, count 1
	     Underflow: bandwidth 10kbps, percent 20%, limit 3, count 0
	     Minimum bandwidth: 0 kbps,  Maximum bandwidth: 4294967295 kbps
	     Adjust-interval: 20 min, Adjust-threshold: bandwidth 100k percent 5%
	     Avg-rate sample frequency: 1min, next sample: 22s
	     Next adjustment in: 120s, Last adjustment: Thu Dec 24 07:22:39 2018
	     Total adjustments: 1
	  Downstream: 1.0.0.20 via bundle-2, Label: 70001
	   refresh: 30s, lifetime: 90s, remaining: 72s
	  History:
	     Current LSP uptime 00:05:41, created Thu Dec 24 07:22:39 2018
	     Prior LSP removal trigger: auto-bandwidth optimization
	  Path option: 1
	  Path in use: to-tail
	   1.0.0.20         strict
	   2.0.0.30         strict
	  CSPF: enabled, IGP shortcut disabled, IGP: ISIS instance CORE
	  Retry: interval: 15s, limit: infinite
	  Ero:
	   1.0.0.20         strict
	   2.0.0.30         strict


	dnRouter# show rsvp tunnels name auto_tunnel_R1_R8_PRIORITY_CORE_TUNNELS_1
	 auto_tunnel_R1_R8_PRIORITY_CORE_TUNNELS_1: head, up (Operational) 45m18s
	  Created: Thu Jun 21 11:27:45 2018
	  Auto-mesh Template: PRIORITY_CORE_TUNNELS
	  Source: 10.10.10.10, Destination: 30.30.30.30
	  Tunnel-id: 1, Extended-tunnel-id: 10.10.10.10
	  Lsp-id: 1, primary
	  Lsp-local-id: 1
	  Bandwidth: 1000Kbps, Bandwidth Configured: 0kbps
      Load-Balancing: weighted-ecmp, Weight: 500
	  Class-Type: ct0
	  Priority: Setup: 7, Hold: 7
	  Hop-limit: 255
	  Auto-bandwidth: enabled
	     Last requested BW: 2500kbps, trigger: Adjustment interval, reason: Adjustment threshold, BW increase
	     Avg-rate sample(min/max/last): 10/3000/2234 kbps
	     Overflow: bandwidth 200kbps, percent 10%, limit 3, count 1
	     Underflow: bandwidth 10kbps, percent 20%, limit 3, count 0
	     Minimum bandwidth: 0 kbps, Maximum bandwidth: 4294967295 kbps
	     Adjust-interval: 20 min, Adjust-threshold: bandwidth 100k percent 5%
	     Avg-rate sample frequency: 1min, next sample: 22s
	     Next adjustment in: 120s, Last adjustment: Thu Dec 24 07:22:39 2018
	     Total adjustments: 1, Successful: 1, Failed: 0
	  Downstream: 1.0.0.20 via ifindex: 151, Label: 70001
	   refresh: 30s, lifetime: 90s, remaining: 72s
	  History:
	     Tunnel created Sun Dec 20 09:51:22 2018
	     Current LSP uptime 00:05:41, created Thu Dec 24 07:22:39 2018
	     Prior LSP removal trigger: auto-bandwidth optimization
	  Path option: 1
	  Path in use: to-tail
	   1.0.0.20         strict
	   2.0.0.30         strict
	  CSPF: enabled, IGP shortcut disabled, IGP: ISIS instance CORE
	  Retry: interval: 15s, limit: infinite
	  Ero:
	   1.0.0.20         strict
	   2.0.0.30         strict


**Command History**

+---------+--------------------------------------------------+
| Release | Modification                                     |
+=========+==================================================+
| 9.0     | Command introduced                               |
+---------+--------------------------------------------------+
| 10.0    | Added LSP-local-id and PCEP information          |
+---------+--------------------------------------------------+
| 11.0    | Added auto-mesh filters                          |
+---------+--------------------------------------------------+
| 11.5.6  | Added uptime/downtime column for show brief view |
+---------+--------------------------------------------------+

