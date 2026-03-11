show interfaces fabric
----------------------

**Minimum user role:** viewer


Fabric ports are 400Gbps interfaces located on NCPs and NCFs.

To display the list of fabric interfaces:

**Command syntax: show interfaces fabric** [interface-name]

**Command mode:** operational



**Note**

- This command is applicable to fabric interfaces.

- If the node is not yet configured or is not connected to the NCC, the operational state of its interfaces will display as "not-exist".

- The operational state relates to the link-state. The uptime for fabric interfaces is with a "watch" interval of 1 second and is displayed for interfaces with an operational state "up", otherwise the uptime is "0".

- Operational-state for fabric interface relates to link-state (laser state)

**Parameter table**

+----------------+--------------------------------------------------------+--------------------------------+---------+
| Parameter      | Description                                            | Range                          | Default |
+================+========================================================+================================+=========+
| interface-name | Optionally filter the display to a specific interface. | -  fab-ncpX-Y/Z/W              | \-      |
|                |                                                        | -  fab-ncpX-Y/Z/W/U            |         |
|                |                                                        | -  fab-ncfX-Y/Z/W              |         |
|                |                                                        | -  fab-ncfX-Y/Z/W/U            |         |
|                |                                                        |                                |         |
|                |                                                        | X - interface speed            |         |
|                |                                                        | Y - NCP/NCF id                 |         |
|                |                                                        | Z - slot id, value 0           |         |
|                |                                                        | W - port id as shown at the WB |         |
|                |                                                        | U - port internal breakout     |         |
+----------------+--------------------------------------------------------+--------------------------------+---------+

The following information is displayed per interface:

+-------------------+-----------------------------------------------------------------------------------------------------------------------------------+-------------------+
| Parameter         | Description                                                                                                                       | Range             |
+===================+===================================================================================================================================+===================+
| Interface         | The name of the fabric interface                                                                                                  | fab-ncf-400-x/y/z |
|                   |                                                                                                                                   | fab-ncp-400-x/y/z |
+-------------------+-----------------------------------------------------------------------------------------------------------------------------------+-------------------+
| Admin state       | The administrative state of the fabric interface                                                                                  | Enabled           |
|                   |                                                                                                                                   | Disabled          |
+-------------------+-----------------------------------------------------------------------------------------------------------------------------------+-------------------+
| Operational state | The operational state of the fabric interface. The operational state relates to the link-state (laser-state)                      | Up                |
|                   |                                                                                                                                   | Down              |
|                   |                                                                                                                                   | Not-exist         |
+-------------------+-----------------------------------------------------------------------------------------------------------------------------------+-------------------+
| SNMP ifindex      | The fabric interface's unique identifying number                                                                                  | Integer           |
+-------------------+-----------------------------------------------------------------------------------------------------------------------------------+-------------------+
| Uptime            | The amount of time that the interface's operational state is "up". When the operational state goes down, the uptime returns to 0. | D days, HH:MM:SS  |
+-------------------+-----------------------------------------------------------------------------------------------------------------------------------+-------------------+
| State transitions | The number of operational state transitions of an interface from up to down state.                                                | #                 |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------+
| Last cleared      | The time since the operational state transitions counter was last cleared.                                                        | D days, HH:MM:SS  |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------+
| Speed             | The speed of the fabric interface (in Gbps)                                                                                       | 400Gbps           |
+-------------------+-----------------------------------------------------------------------------------------------------------------------------------+-------------------+

**Example**
::

	dnRouter# show interfaces fabric
	
	| Interface              | Admin    | Operational   |
	+------------------------+----------+---------------|
	| fab-ncf-400-0/0/0      | enabled  | up            |
	| fab-ncf-400-0/0/1      | disabled | down          |
	| fab-ncp-400-0/0/0      | enabled  | up            |
	| fab-ncp-400-0/0/1      | disabled | down          |
	| fab-ncp-400-1/0/0      | enabled  | up            |
	| fab-ncp-400-1/0/1      | enabled  | up            |
	| fab-ncp-400-2/0/0      |          | not-exist     |
	| fab-ncp-400-2/0/1      |          | not-exist     |
	
	
	dnRouter# show interfaces fabric fab-ncp400-0/0/0
	
	Interface fab-ncp400-0/0/0
	  SNMP ifindex: 46341
	  Admin state: enabled, Operational state: up, Uptime: 1 day, 4:00:39
	  State transitions: 2, Last cleared: 0 days, 0:00:00
	  Speed: 400Gbps
	  Total lanes: 8
	  Active lanes: 8

	  Flags:	C - Non-zero CRC rate, S - Non-zero size error-count, G - Non-zero code group error-count
	            M - Link down, misalignment error, L - Link down, SerDes signal lock error
	            R - Link up, but not accepting reachability cells
	            T - Bad link connectivity or link down, based on reachability cells


	  | Lane id          | Operational    | Flags          |
	  +------------------+----------------+----------------+
	  | 0 (sfi51_0/371)  | up             |                |
	  | 1 (sfi51_0/370)  | up             |                |
	  | 2 (sfi51_0/369)  | up             |                |
	  | 3 (sfi51_0/368)  | up             |                |
	  | 4 (sfi51_1/379)  | up             |                |
	  | 5 (sfi51_1/378)  | up             |                |
	  | 6 (sfi51_1/377)  | up             |                |
	  | 7 (sfi51_1/376)  | up             |                |
	
	dnRouter# show interfaces fabric

	| Interface              | Admin    | Operational   |
	+------------------------+----------+---------------|
	| fab-ncf-400-100/0/0/0  | enabled  | up            |
	| fab-ncf-400-100/0/0/1  | disabled | down          |
	| fab-ncp-400-4/0/0/0    | enabled  | up            |
	| fab-ncp-400-4/0/0/1    | enabled  | up            |
	| fab-ncp-400-2/0/0/0    |          | not-exist     |
	| fab-ncp-400-2/0/0/1    |          | not-exist     |

.. **Help line:** Displays backplane interface(s)

**Command History**

+---------+------------------------------------------------------------+
| Release | Modification                                               |
+=========+============================================================+
| 11.0    | Command introduced                                         |
+---------+------------------------------------------------------------+
| 11.2    | Output updated                                             |
+---------+------------------------------------------------------------+
| 17.2    | Added interface operational status transitions information |
+---------+------------------------------------------------------------+
