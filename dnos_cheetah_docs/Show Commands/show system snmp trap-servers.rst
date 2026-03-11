show system snmp trap-servers
-----------------------------

**Minimum user role:** viewer

The following command displays a list of the configured SNMP trap servers. You can filter the display to show a specific server.



**Command syntax: show system snmp trap-servers** [server-ip]

**Command mode:** operational



**Note**

- vrf "default" represents the in-band management, while vrf "mgmt0" represents the out-of-band management.

**Parameter table**

+-----------+------------------------------------------+----------+
| Parameter | Description                              | Range    |
+===========+==========================================+==========+
| server-ip | Filters the output by server IP address. | A.B.C.D  |
|           |                                          | x:x::x:x |
+-----------+------------------------------------------+----------+

**Example**
::

	dnRouter# show system snmp trap-servers
	SNMP Trap-Servers:
	| VRF        | Server           | Port  | Version | Security      | Community             | Max Throughput |
	|------------+------------------+-------+---------+---------------+-----------------------|----------------|
	| default    | 1.2.3.4          | 162   | 1       | none          | MySnmpCommunity       | 100            |
	| mgmt0      | 2001:ab12::1     | 162   | 2c      | none          | MySnmpCommunity       | 1000           |

	dnRouter# show system snmp trap-servers 1.2.3.4
	SNMP Trap Servers:
	| VRF        | Server      | Port  | Version | Security      | Community             | Max Throughput |
	|------------+-------------+-------+---------+---------------+-----------------------|----------------|
	| default    | 1.2.3.4     | 162   | 1       | none          | MySnmpCommunity       | 100            |

.. **Help line:** show system snmp trap servers

**Command History**

+---------+--------------------------------------------------------------------------------+
| Release | Modification                                                                   |
+=========+================================================================================+
| 5.1.0   | Command introduced                                                             |
+---------+--------------------------------------------------------------------------------+
| 10.0    | Updated syntax from servers to trap-servers                                    |
+---------+--------------------------------------------------------------------------------+
| 13.1    | Added in-band (default VRF) / out-of-band (mgmt0 VRF) configuration per server |
+---------+--------------------------------------------------------------------------------+
| 15.1    | Added IPv6 support to SNMP                                                     |
+---------+--------------------------------------------------------------------------------+
| 16.1    | Added Admin-State for Trap-Servers                                             |
+---------+--------------------------------------------------------------------------------+
| 15.2.3  | Added support for Max Throughput                                               |
+---------+--------------------------------------------------------------------------------+
