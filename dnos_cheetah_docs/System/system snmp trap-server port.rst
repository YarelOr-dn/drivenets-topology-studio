system snmp trap-server port
----------------------------

**Minimum user role:** operator

To configure the SNMP port to which the remote device is connected:

**Command syntax: port [port]**

**Command mode:** config

**Hierarchies**

- system snmp trap-server

.. **Note**

	- no command reverts the port configuration to its default value

**Parameter table**

+-----------+-----------------------------------------------------------------------+----------+---------+
| Parameter | Description                                                           | Range    | Default |
+===========+=======================================================================+==========+=========+
| port      | The port on the local device to which the remote device is connected. | 0..65535 | 162     |
+-----------+-----------------------------------------------------------------------+----------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# trap-server 1.2.3.4 vrf default
	dnRouter(cfg-system-snmp-trap-server)# port 123
	
	dnRouter(cfg-system-snmp)# trap-server 1.1.1.1 vrf default
	dnRouter(cfg-system-snmp-trap-server)# port 444
	
	dnRouter(cfg-system-snmp)# trap-server 1.2.3.5 vrf mgmt0
	dnRouter(cfg-system-snmp-trap-server)# port 43
	
	dnRouter(cfg-system-snmp)# trap-server 1.2.3.4 vrf default
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-snmp-trap-server)# no port

.. **Help line:** Configure system snmp trap server port

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 5.1.0   | Command introduced               |
+---------+----------------------------------+
| 6.0     | Applied new hierarchy for SNMP   |
+---------+----------------------------------+
| 9.0     | Applied new hierarchy for server |
+---------+----------------------------------+


