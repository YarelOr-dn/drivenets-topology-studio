show rsvp tunnels role
----------------------

**Minimum user role:** viewer

To display RSVP tunnel information filtered by role:



**Command syntax: show rsvp tunnels role [role]** state [state] detail

**Command mode:** operational



.. 
	**Internal Note**

	- set name to display detailed information for tunnels matching the name

	- set destination to display detailed information for tunnels matching the destination

**Parameter table**

+-----------+--------------------------------------------------+------------+
| Parameter | Description                                      | Range      |
+===========+==================================================+============+
| role      | Displays all RSVP tunnels for the specified role | head       |
|           |                                                  | transit    |
|           |                                                  | tail       |
+-----------+--------------------------------------------------+------------+
| state     | Filters the information by tunnel's state        | up         |
|           |                                                  | down       |
|           |                                                  | admin-down |
+-----------+--------------------------------------------------+------------+
| detail    | Displays detailed tunnel information.            | \-         |
+-----------+--------------------------------------------------+------------+

**Example**
::

	dnRouter# show rsvp tunnels role head

	Legend: * - Make-Before-Break

	Destination    Source          Role    State  LabelIn   LabelOut  LSP-local-id  Uptime/Downtime  Name
	--------------------------------------------------------------------------------------------------------
	30.30.30.30    10.10.10.10     head    up     -         70001     1             45m56s           tunnel1
	30.30.30.30    10.10.10.10     head    up     -         70002     2             45m53s           tunnel2


	dnRouter# show rsvp tunnels role head state up

	Legend: * - Make-Before-Break

	Destination    Source          Role    State  LabelIn   LabelOut  LSP-local-id  Uptime/Downtime  Name
	--------------------------------------------------------------------------------------------------------
	30.30.30.30    10.10.10.10     head    up     -         70001     1             45m56s           tunnel1
	30.30.30.30    10.10.10.10     head    up     -         70002     2             45m53s           tunnel2


	dnRouter# show rsvp tunnels role head state up detail
	tunnel1: head, up (Operational) 45m56s
	  Created: Thu Jun 21 11:27:45 2018
	  Source: 10.10.10.10, Destination: 30.30.30.30
	  Tunnel-id: 1, Extended-tunnel-id: 10.10.10.10
	  Lsp-id: 1, primary
	  Lsp-local-id: 1
	  Bandwidth Requested: 0Kbps
	  Priority: Setup: 7, Hold: 7
	  Downstream: 1.0.0.20 via ifindex: 151, Label: 70001
	   refresh: 30s, lifetime: 90s, remaining: 64s
	  Path in use: to-tail
	   1.0.0.20         strict
	   2.0.0.30         strict
	  CSPF: disabled, IGP shortcut disabled
	  Retry: interval: 15s, limit: infinite
	  Ero:
	   1.0.0.20         strict
	   2.0.0.30         strict

	tunnel2: head, up (Operational) 45m53s
	  Created: Thu Jun 21 11:27:49 2018
	  Source: 10.10.10.10, Destination: 30.30.30.30
	  Tunnel-id: 2, Extended-tunnel-id: 10.10.10.10
	  Lsp-id: 2, primary
	  Lsp-local-id: 2
	  Bandwidth Requested: 0Kbps
	  Priority: Setup: 7, Hold: 7
	  Downstream: 1.0.0.20 via ifindex: 151, Label: 70002
	   refresh: 30s, lifetime: 90s, remaining: 67s
	  Path in use: to-tail
	   1.0.0.20         strict
	   2.0.0.30         strict
	  CSPF: disabled, IGP shortcut disabled
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
| 10.0    | Added LSP-local-id                               |
+---------+--------------------------------------------------+
| 11.5.6  | Added uptime/downtime column for show brief view |
+---------+--------------------------------------------------+

