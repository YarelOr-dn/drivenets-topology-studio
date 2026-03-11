show rsvp statistics tunnel
----------------------------

**Minimum user role:** viewer

To display RSVP tunnel signaling statistics:



**Command syntax: show rsvp statistics tunnel** {name [tunnel-name] \| state [state] \| destination [destination] \| role [role] \| detail}

**Command mode:** operational



**Parameter table**

+-------------+--------------------------------------------------------------------------------+---------------+
| Parameter   | Description                                                                    | Range         |
+=============+================================================================================+===============+
| tunnel-name | Filters the displayed statistics to the specified tunnel                       | String 1..255 |
+-------------+--------------------------------------------------------------------------------+---------------+
| state       | Filters the displayed statistics to tunnels in a specific state                | Up            |
|             |                                                                                | Down          |
|             |                                                                                | Admin-down    |
+-------------+--------------------------------------------------------------------------------+---------------+
| destination | Filters the displayed statistics to tunnels matching the specified destination | A.B.C.D       |
+-------------+--------------------------------------------------------------------------------+---------------+
| role        | Filters the displayed statistics to tunnels matching the specified role        | Head          |
|             |                                                                                | Transit       |
|             |                                                                                | Tail          |
+-------------+--------------------------------------------------------------------------------+---------------+
| detail      | Displays all statistics for the tunnels                                        | \-            |
+-------------+--------------------------------------------------------------------------------+---------------+

Statistics are displayed for the following Event types:

+--------------------------+---------------------------------------------------------------------------------------------------+
| Event                    | Description                                                                                       |
+==========================+===================================================================================================+
| Path                     | The number of RSVP Path messages received.                                                        |
+--------------------------+---------------------------------------------------------------------------------------------------+
| Path Error               | The number of RSVP Path Error messages received                                                   |
+--------------------------+---------------------------------------------------------------------------------------------------+
| PathTear                 | The number of RSVP PathTear messages received                                                     |
+--------------------------+---------------------------------------------------------------------------------------------------+
| Resv                     | The number of RSVP Reservation messages                                                           |
+--------------------------+---------------------------------------------------------------------------------------------------+
| ResvTear                 | The number of RSVP Reservation delete messages                                                    |
+--------------------------+---------------------------------------------------------------------------------------------------+
| ResvError                | The number of RSVP Reservation error messages                                                     |
+--------------------------+---------------------------------------------------------------------------------------------------+
| Packet parsing failure   | The total number of packets dropped due to parsing failure                                        |
+--------------------------+---------------------------------------------------------------------------------------------------+
| LSP attribute change     | The number of RESV messages with read only property that changed                                  |
+--------------------------+---------------------------------------------------------------------------------------------------+
| Path timeout             | The number of times the sender timed out because the path was removed                             |
+--------------------------+---------------------------------------------------------------------------------------------------+
| Resv timeout             | The number of times the receiver timed out because the reservation was removed                    |
+--------------------------+---------------------------------------------------------------------------------------------------+
| Downstream link-down     | The number of link-down events received from downstream node                                      |
+--------------------------+---------------------------------------------------------------------------------------------------+
| Upstream link-down       | The number of link-down events received from upstream node                                        |
+--------------------------+---------------------------------------------------------------------------------------------------+
| CAC failures             | The number of failures to allocate bandwidth in CAC                                               |
+--------------------------+---------------------------------------------------------------------------------------------------+
| LSP preemption           | The number of preemption events (soft & hard)                                                     |
+--------------------------+---------------------------------------------------------------------------------------------------+
| CSPF failure             | The number of times CSPF failed to find a valid path                                              |
+--------------------------+---------------------------------------------------------------------------------------------------+
| Label allocation failure | The number of failures to allocate label                                                          |
+--------------------------+---------------------------------------------------------------------------------------------------+
| Byte count               | The total number of bytes transferred by the tunnel                                               |
+--------------------------+---------------------------------------------------------------------------------------------------+
| Packet count             | The total number of packets transferred by the tunnel                                             |
+--------------------------+---------------------------------------------------------------------------------------------------+
| Path Change              | The number of LSP changes (including initial LSP) for the tunnel                                  |
+--------------------------+---------------------------------------------------------------------------------------------------+
| State Change             | The number of times the tunnel has changed its state                                              |
+--------------------------+---------------------------------------------------------------------------------------------------+
| Path change attempts     | The number of times a tunnel was signalled regardless if it resulted in an established LSP or not |
+--------------------------+---------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show rsvp statistics tunnel

	| Tx [pkts]   | Tx [octets] | Tx [kbps] | State | Name                                               |
	+-------------+-------------+-----------+-------|----------------------------------------------------+
	| 5556790     | 2845076480  | 27000     | up    | auto_tunnel_R1_R8_TEMPLATE_1                       |
	| 80004       | 64963248    | 185180    | up    | auto_tunnel_J2-Cluster_R1-J2-Proto_R2_AA_1         |
	| 0           | 0           | 0         | down  | P3-21-DEFAULT                                      |

	dnRouter# show rsvp statistics tunnel state down

	| Tx [pkts]   | Tx [octets] | Tx [kbps] | State | Name                                               |
	+-------------+-------------+-----------+-------|----------------------------------------------------+
	| 0           | 0           | 0         | down  | P3-21-DEFAULT                                      |


	dnRouter# show rsvp statistics tunnel detail

	tunnel1: head, up
	Source: 10.10.10.10 Destination: 30.30.30.30

	PacketName    Rx        Tx        PacketName    Rx        Tx
	------------------------------------------------------------
	Path          0         20        Resv          18        0
	PathTear      0         1         ResvTear      0         0
	PathError     0         0         ResvError     0         0

	CounterName                             Total     CounterName                             Total
	-----------------------------------------------------------------------------------------------
	Packet parsing failure                  0         LSP attribute change                    0
	Path timeout                            0         Resv timeout                            0
	Downstream link-down                    0         Upstream link-down                      0
	CAC failures                            0         CSPF failures                           0
	LSP Preemption                          0         Label allocation failures               0
	Path changes                            0         State changes                           0
	Packet count                            0         Byte count                              0
	Path change attempts                    1         Tx-rate [kbps]                          1895180


	tunnel4: transit, up
	Source: 2.2.2.2 Destination: 3.3.3.3

	PacketName    Rx        Tx        PacketName    Rx        Tx
	------------------------------------------------------------
	Path          31        30        Resv          30        30
	PathTear      0         0         ResvTear      0         0
	PathError     0         0         ResvError     0         0

	CounterName                             Total     CounterName                             Total
	-----------------------------------------------------------------------------------------------
	Packet parsing failure                  0         LSP attribute change                    0
	Path timeout                            0         Resv timeout                            0
	Downstream link-down                    0         Upstream link-down                      0
	CAC failures                            0         CSPF failures                           0
	LSP Preemption                          0         Label allocation failures               0
	Path changes                            0         State changes                           0


	dnRouter# show rsvp statistics tunnel role head

	tunnel1: head, up
	Source: 10.10.10.10 Destination: 30.30.30.30

	PacketName    Rx        Tx        PacketName    Rx        Tx
	------------------------------------------------------------
	Path          0         20        Resv          18        0
	PathTear      0         1         ResvTear      0         0
	PathError     0         0         ResvError     0         0

	CounterName                             Total     CounterName                             Total
	-----------------------------------------------------------------------------------------------
	Packet parsing failure                  0         LSP attribute change                    0
	Path timeout                            0         Resv timeout                            0
	Downstream link-down                    0         Upstream link-down                      0
	CAC failures                            0         CSPF failures                           0
	LSP Preemption                          0         Label allocation failures               0
	Path changes                            0         State changes                           0
	Packet count                            0         Byte count                              0
	Path change attempts                    1         Tx-rate [kbps]                          1895180


	dnRouter# show rsvp statistics tunnel destination 8.8.8.8

	dnRouter# show rsvp statistics tunnel destination 8.8.8.8 state up

	dnRouter# show rsvp statistics tunnel name auto_tunnel_R1_R8_TEMPLATE_1


**Command History**

+---------+------------------------------------------------------------------------+
| Release | Modification                                                           |
+=========+========================================================================+
| 11.0    | Command introduced                                                     |
+---------+------------------------------------------------------------------------+
| 11.4    | Added state filter and option to display detailed or brief information |
+---------+------------------------------------------------------------------------+

