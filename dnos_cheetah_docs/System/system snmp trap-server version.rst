system snmp trap-server version
-------------------------------

**Minimum user role:** operator

To configure the trap-server SNMP version:

**Command syntax: version [version]**

**Command mode:** config

**Hierarchies**

- system snmp trap-server

.. **Note**

	- No command reverts snmp version to its default value

**Parameter table**

+-----------+------------------+-------+---------+
| Parameter | Description      | Range | Default |
+===========+==================+=======+=========+
| version   | The SNMP version | 1     | 2c      |
|           |                  | 2c    |         |
+-----------+------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# trap-server 1.1.1.1 vrf default
	dnRouter(cfg-system-snmp-trap-server)# version 1
	
	dnRouter(cfg-system-snmp)# trap-server 1.2.3.4 vrf mgmt0
	dnRouter(cfg-system-snmp-trap-server)# version 2c
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-snmp-trap-server)# no version

.. **Help line:** Configure system snmp trap server version

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


