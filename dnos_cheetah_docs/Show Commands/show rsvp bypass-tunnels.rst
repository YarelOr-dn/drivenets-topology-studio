show rsvp bypass-tunnels
------------------------

**Minimum user role:** viewer

To display RSVP bypass-tunnel information:



**Command syntax: show rsvp bypass-tunnels** {name [tunnel-name] \| destination [destination] \| state [state]} detail

**Command mode:** operational



**Note**

- Protected Bandwidth displays the total amount of bandwidth (in kbps) of all primary tunnels protected by the bypass tunnel.

.. - ProtectedBW - displays the total amount of bandwidth (in kbps) of all primary tunnels protected by the bypass tunnel

	- set name to display detailed information for tunnels matching the name

	- set destination to display detailed information for tunnels matching the destination

	- set state to display brief information for tunnel matching the state

	- set detail to display tunnel detailed information.

	- "detail" cannot be set together with name or destination

**Parameter table**

+-------------+---------------------------------------------------------------------------------------------------+------------+
| Parameter   | Description                                                                                       | Range      |
+=============+===================================================================================================+============+
| tunnel-name | Displays detailed information on RSVP bypass-tunnels that match the specified name.               | string     |
+-------------+---------------------------------------------------------------------------------------------------+------------+
| destination | Displays detailed information on RSVP bypass-tunnels that match the specified destination.        | A.B.C.D    |
+-------------+---------------------------------------------------------------------------------------------------+------------+
| state       | Displays brief information on RSVP bypass-tunnels matching the specified state                    | up         |
|             |                                                                                                   | down       |
|             |                                                                                                   | admin-down |
+-------------+---------------------------------------------------------------------------------------------------+------------+
| detail      | Displays detailed information on the bypass-tunnels. Not applicable to tunnel-name or destination | \-         |
+-------------+---------------------------------------------------------------------------------------------------+------------+

**Example**
::

	dnRouter# show rsvp bypass-tunnels

	Legend: * - Make-Before-Break

	Destination     Source          Role     State   LabelIn LabelOut  ProtectedBW [kbps] Uptime/Downtime  Name
	------------------------------------------------------------------------------------------------------------------
	100.0.0.3       101.0.0.19      bypass   up      -       556       9000000            4h7m14s          tunnel_bypass_node-bundle-1719.1719_9
	101.0.0.17      101.0.0.19      bypass   up      -       71649     1000000            1d18h46          tunnel_bypass_link-bundle-1719.1719_12
	101.0.0.21      101.0.0.19      bypass   down    -       -         0                  2d12h7m          tunnel_bypass_node-bundle-1719.1719_60


	dnRouter# show rsvp bypass-tunnels name tunnel_bypass_node-bundle-1719.1719_9

	tunnel_bypass_node-bundle-1719.1719_9: bypass, up
	  Tunnel up-time: 4h7m14s
	  Lsp up-time: 4h7m14s
	  Lsp status: up (Operational), active
	  Created: Thu Nov 21 14:47:22 2019
	  Source: 101.0.0.19, Destination: 100.0.0.3
	  Tunnel-id: 298, Extended-tunnel-id: 101.0.0.19
	  Tunnel-local-id: 795
	  Install-delay: 5s, Hold-down-delay: 5s
	  Lsp-id: 482, primary
	  Lsp-local-id: 799
	  Bandwidth Requested: 1kbps
	  Protected Lsps: 1
	  Backup bandwidth: any-class unlimited
	  Protected bandwidth: 9000000kbps
	  Class-Type: 0
	  Priority: Setup: 6, Hold: 6
	  Soft-preemption desired, timeout: 30s
	  Exclude interface: bundle-1719.1719
	  Fast Reroute: Disabled
	  BFD: disabled
	  Number of LSP protected: 157
	  Downstream: 1.3.19.0 via: bundle-319.319, Label: 556
	   refresh: 45s, lifetime: 135s, remaining: 102s
	   next message in: 12s, refresh reduction active
	  Optimization: enabled, interval: 300s, next: due-in 157s
	   Last optimization attempt: Thu Nov 21 18:52:21 2019
	  PCEP:
	    Configured delegation: Enabled
	    Operational delegation: Delegated
	    Sticky-ERO: Enabled
	    Delegated PCE 100.64.2.215 priority 20
	    Redelegation time: 60
	    Lsp-state time: 120
	    Last optimization reason: local change
	  SRLG-Policy: avoid
	  CSPF: enabled, IGP shortcut enabled, Equal-cost: least-fill
	  IGP: ISIS
	  IGP metric: 40, CSPF metric: 70, Hop-Limit: 255
	  Retry: interval: 45s, limit: infinite
	  Admin-Group:
	   Exclude-Any: 0x80
	  Ero:
	   1.3.19.0         strict
	  Record Route:
	   IPV4 100.0.0.3, flags 0x20 (Node-ID)
	   Label: 0, flags 0x1
	   IPV4 1.3.19.0, flags 0x0
	   Label: 0, flags 0x1


**Command History**

+---------+--------------------------------------------------+
| Release | Modification                                     |
+=========+==================================================+
| 10.0    | Command introduced                               |
+---------+--------------------------------------------------+
| 11.5.6  | Added uptime/downtime column for show brief view |
+---------+--------------------------------------------------+


