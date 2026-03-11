system snmp packet-size
----------------------------

**Minimum user role:** operator

You can configure the maximum packet size (in bytes) for all outgoing SNMP packets.

**Command syntax: packet-size [packet-size]**

**Command mode:** config

**Hierarchies**

- system snmp 

.. **Note**

	- Configuration is global for all outgoing SNMP responses and traps.

	- Value includes 20 bytes for IPv4 header and 8 bytes for UDP header.

	- 'no' command reverts the value to default.

**Parameter table**

+-------------+----------------------------------------+-----------+---------+
| Parameter   | Description                            | Range     | Default |
+=============+========================================+===========+=========+
| packet-size | The size of the SNMP packet (in bytes) | 100..9300 | 1500    |
+-------------+----------------------------------------+-----------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# packet-size 1000
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-snmp)# no packet-size

.. **Help line:** Configure SNMP maximum outgoing packet size in bytes.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


