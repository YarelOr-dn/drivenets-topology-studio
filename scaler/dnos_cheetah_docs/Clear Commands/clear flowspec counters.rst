clear flowspec counters
-----------------------

**Minimum user role:** operator

To clear FlowSpec counters:

**Command syntax: clear flowspec counters** instance vrf [vrf-name] {[address-family] | [address-family] nlri [nlri] | [address-family] destination [dest-prefix] source [src-prfix]}

**Command mode:** operation

.. **Hierarchies**

**Note**

- Optional parameters must match the order in the command.

- When clearing counters for a specific NRLI, destination, or source prefix, you must specify an address-family.

**Parameter table:**


+-------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+-------------+
|                   |                                                                                                                                                     |                     |             |
| Parameter         | Description                                                                                                                                         | Range               | Default     |
+===================+=====================================================================================================================================================+=====================+=============+
|                   |                                                                                                                                                     |                     |             |
| vrf-name          | Clears FlowSpec counters only for the specified VRF. If not specified, the clear command will apply to the default VRF.                             | string              | default     |
+-------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+-------------+
|                   |                                                                                                                                                     |                     |             |
| address-family    | Clears FlowSpec counters only for the specified address-family. When the address-family is not specified, it will apply to   both IPv4 and IPv6.    | IPv4                | both        |
|                   |                                                                                                                                                     |                     |             |
|                   |                                                                                                                                                     | IPv6                |             |
+-------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+-------------+
|                   |                                                                                                                                                     |                     |             |
| nlri              | Clears counters for a specific flow                                                                                                                 | string              | \-          |
+-------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+-------------+
|                   |                                                                                                                                                     |                     |             |
| dest-prefix       | Clears counters for all destinations matching the specified destination prefix.                                                                     | A.B.C.D/M           | \-          |
|                   |                                                                                                                                                     |                     |             |
|                   |                                                                                                                                                     | xx:xx::xx:xx/O-M    |             |
+-------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+-------------+
|                   |                                                                                                                                                     |                     |             |
| src-prefix        | Clears counters for all sources matching the specified source prefix                                                                                | A.B.C.D/M           | \-          |
|                   |                                                                                                                                                     |                     |             |
|                   |                                                                                                                                                     | xx:xx::xx:xx/O-M    |             |
+-------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+-------------+


**Example**
::

	dnRouter# clear flowspec counters
	dnRouter# clear flowspec counters ipv4
	dnRouter# clear flowspec counters ipv4 nlri "DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=5,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5"
	dnRouter# clear flowspec counters ipv4 destination 50.0.0.0/8
	dnRouter# clear flowspec counters ipv4 source 50.1.2.3/24
	dnRouter# clear flowspec counters ipv4 destination 50.0.0.0/8 source 50.1.2.3/24
	dnRouter# clear flowspec ipv6 destination 2011:11:100:1::/8-64


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.0        | Command introduced    |
+-------------+-----------------------+