system snmp trap-server trap-source-port
----------------------------------------

**Minimum user role:** operator

To configure system SNMP source port for all outgoing SNMP traps:

**Command syntax: trap-source-port [port]**

**Description:** configure system snmp source port for per server per VRF for outgoing snmp traps

	- no command reverts the port configuration to its default value.

**Parameter table**

+-----------+-------------------------------------------------------------------------+-------------+--------------------------------------+
| Parameter | Description                                                             | Range       | Default                              |
+===========+=========================================================================+=============+======================================+
| port      | Set the port that will be used as a source for all outgoing SNMP traps. | 1024..65535 | Ephemerally allocated from the range |
+-----------+-------------------------------------------------------------------------+-------------+--------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
    dnRouter(cfg-system-snmp)# trap-server 1.2.3.4 vrf default
    dnRouter(cfg-snmp-trap-server)# trap-source-port 1900

	dnRouter(cfg-system-snmp-server)# no trap-source-port

**Command mode:** config

**Removing Configuration**

To revert the router-id to default: 
::

    dnRouter(cfg-system-snmp)# no trap-source-port

Configuration of SNMP traps source port per SNMP trap server per VRF for outgoing snmp traps.

.. **Help line:** Configure system snmp trap source port

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 14.0    | Command introduced |
+---------+--------------------+


To configure system SNMP source port for all outgoing SNMP traps:
