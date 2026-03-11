show pim statistics
-------------------

**Minimum user role:** viewer

You can use this command to display the PIM message statistics, globally, per all interfaces or per specific interface (if all or specific interface is indicated). PIM enabled interfaces can be either physical interfaces, LAG interfaces or sub-interfaces.



**Command syntax: show pim statistics** interfaces [interface-name]

**Command mode:** operational



**Note**

- The 'show pim statistics interfaces' command is used to display PIM protocol packet statistics for all the interfaces.

- The 'show pim statistics interfaces [interface-name]' command is used to display PIM protocol packet statistics for a specific interface.

- When displaying global or per-specific interface statistics, the Error counters are also displayed.


**Parameter table**

+----------------+-----------------------------------------------------------------------------+----------------------------------------------------+---------+
| Parameter      | Description                                                                 | Range                                              | Default |
+================+=============================================================================+====================================================+=========+
| interface-name | Display PIM message statistics for a specific interface (or all interfaces) | ge<interface speed>-<A>/<B>/<C>                    | \-      |
|                |                                                                             | ge<interface speed>-<A>/<B>/<C>.<sub-interface id> |         |
|                |                                                                             | bundle-<bundle id>                                 |         |
|                |                                                                             | bundle-<bundle id>.<sub-interface id>              |         |
+----------------+-----------------------------------------------------------------------------+----------------------------------------------------+---------+

The following describes the parameters in the table:

+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter                       | Description                                                                                                                                                                                         |
+=================================+=====================================================================================================================================================================================================+
| Bad Length                      | Number of PIM control packets received for which the packet size does not match the PIM length field in the packet                                                                                  |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Bad Checksum                    | Number of PIM control packets received for which the calculated checksum does not match the checksum field in the packet                                                                            |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Unknown type                    | Number of PIM control packets received with an unknown type                                                                                                                                         |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Unknown Version                 | Number of PIM control packets received with an unknown version. The version is not version 1 or version 2                                                                                           |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Neighbor unknown                | Number of PIM control packets received (excluding PIM hello) without first receiving the hello packet                                                                                               |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Rx V1 Require V2                | Number of PIM version 1 control packets received on an interface configured for PIM version 2                                                                                                       |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Rx Register not RP              | Number of PIM register packets received when the routing device is not the RP for the group                                                                                                         |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Rx Register no route            | Number of PIM register packets received when the RP does not have a unicast route back to the source                                                                                                |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| KeepAlive Timeout               | The number of times an (S,G) state was timed out as a result of (1) not receiving PIM NULL register or (2) not receiving MSDP SA refresh or (3) not receiving Traffic (for Data Driven PIM entries) |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Rx Unknown Reg Stop             | Register Stop received with no related known PIM Register                                                                                                                                           |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Rx Join/Prune no state          | Number of join/prune messages received for which the routing device has no state a prune request                                                                                                    |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Rx Join/Prune on upstream if    | Number of join and prune messages received on the interface used to reach the upstream routing device, toward the RP                                                                                |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Rx Join/Prune for invalid group | Number of join/prune messages received for invalid multicast group addresses                                                                                                                        |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show pim statistics

	PIM Statistics

	+-----------------------------+---------------+------------+-----------------+
	| PIM Message type            |   Rx[pkts]    |  Tx[pkts]  |  Rx error[pkts] |
	+-----------------------------+---------------+------------+-----------------+
	| V2 Hello                    |    540        |     467    |       2         |
	| V2 Join/Prune               |    137        |     149    |       4         |
	| V2 Register                 |      0        |       0    |       0         |
	| V2 Register Stop            |      0        |       0    |       0         |
	| V2 State Refresh            |      0        |       0    |       0         |
	+-----------------------------+---------------+------------+-----------------+

	+---------------------------------------+------------------+
	| Rx Error Event Type                   | Error type       |
	|                                       | Events Count     |
	+---------------------------------------+------------------+
	| Bad Length                            |              0   |
	| Bad Checksum                          |              0   |
	| Unknown type                          |              0   |
	| Unknown Version                       |              0   |
	| Neighbor unknown                      |              0   |
	| Rx V1 Require V2                      |              0   |
	| Rx Register not RP                    |              0   |
	| Rx Register no route                  |              0   |
	| KeepAlive Timeout                     |              0   |
	| Rx Unknown Reg Stop                   |              0   |
	| Rx Join/Prune no state                |              0   |
	| Rx Join/Prune on upstream if          |              0   |
	| Rx Join/Prune for invalid group       |              0   |
	+---------------------------------------+------------------+

	dnRouter#


	dnRouter# show pim statistics interfaces

	PIM Statistics

	Total:
	+-----------------------------+---------------+------------+-----------------+
	| PIM Message type            |   Rx[pkts]    |  Tx[pkts]  |  Rx error[pkts] |
	+-----------------------------+---------------+------------+-----------------+
	| V2 Hello                    |    540        |     467    |       2         |
	| V2 Join/Prune               |    137        |     149    |       4         |
	| V2 Register                 |      0        |       0    |       0         |
	| V2 Register Stop            |      0        |       0    |       0         |
	| V2 State Refresh            |      0        |       0    |       0         |
	+-----------------------------+---------------+------------+-----------------+

	Interface ge100-1/1/0 :
	+-----------------------------+---------------+------------+-----------------+
	| PIM Message type            |   Rx[pkts]    |  Tx[pkts]  |  Rx error[pkts] |
	+-----------------------------+---------------+------------+-----------------+
	| V2 Hello                    |     40        |      67    |       0         |
	| V2 Join/Prune               |      7        |       9    |       0         |
	| V2 Register                 |      0        |       0    |       0         |
	| V2 Register Stop            |      0        |       0    |       0         |
	| V2 State Refresh            |      0        |       0    |       0         |
	+-----------------------------+---------------+------------+-----------------+

	Interface bundle-20.222 :
	+-----------------------------+---------------+------------+-----------------+
	| PIM Message type            |   Rx[pkts]    |  Tx[pkts]  |  Rx error[pkts] |
	+-----------------------------+---------------+------------+-----------------+
	| V2 Hello                    |    440        |     367    |       2         |
	| V2 Join/Prune               |     90        |      90    |       3         |
	| V2 Register                 |      0        |       0    |       0         |
	| V2 Register Stop            |      0        |       0    |       0         |
	| V2 State Refresh            |      0        |       0    |       0         |
	+-----------------------------+---------------+------------+-----------------+
	dnRouter#



	dnRouter# show pim statistics interfaces ge100-1/1/0.234

	PIM Statistics

	Interface ge100-1/1/0.234:

	+-----------------------------+---------------+------------+-----------------+
	| PIM Message type            |   Rx[pkts]    |  Tx[pkts]  |  Rx error[pkts] |
	+-----------------------------+---------------+------------+-----------------+
	| V2 Hello                    |     40        |      67    |       0         |
	| V2 Join/Prune               |      7        |       9    |       0         |
	| V2 Register                 |      0        |       0    |       0         |
	| V2 Register Stop            |      0        |       0    |       0         |
	| V2 State Refresh            |      0        |       0    |       0         |
	+-----------------------------+---------------+------------+-----------------+

	+---------------------------------------+------------------+
	| Rx Error Event Type                   | Error type       |
	|                                       | Events Count     |
	+---------------------------------------+------------------+
	| Bad Length                            |              0   |
	| Bad Checksum                          |              0   |
	| Unknown type                          |              0   |
	| Unknown Version                       |              0   |
	| Neighbor unknown                      |              0   |
	| Rx V1 Require V2                      |              0   |
	| Rx Register not RP                    |              0   |
	| Rx Register no route                  |              0   |
	| KeepAlive Timeout                     |              0   |
	| Rx Unknown Reg Stop                   |              0   |
	| Rx Join/Prune no state                |              0   |
	| Rx Join/Prune on upstream if          |              0   |
	| Rx Join/Prune for invalid group       |              0   |
	+---------------------------------------+------------------+


.. **Help line:** Show PIM message statistics

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
