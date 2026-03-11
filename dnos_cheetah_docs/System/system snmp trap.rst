system snmp trap
----------------

**Minimum user role:** operator

All traps are enabled by default. You can disable a trap, or enable a disabled trap, as follows:

**Command syntax: trap [trap-type] [trap-name] enabled \| disabled**

**Command mode:** config

**Hierarchies**

- system snmp

**Note**

- When multiple SNMP servers are configured, all enabled traps are sent to all SNMP servers.

.. - all traps are enabled by default

	- no command removes the trap configuration - essentially enables the trap

	- trap-type includes all supported trap-names children (see supported snmp suppressed traps)

**Parameter table**

+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter          | Description                                                                                                                                      |
+====================+==================================================================================================================================================+
| trap-type          | Groups traps together, allowing you to enable/disable the entire group with one command, to control and limit the scale of SMNP traps generated. |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------+
| trap-name          | The name of the trap to be enabled/disabled.                                                                                                     |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------+
| enabled | disabled | Select whether to enable or disable the specified trap. All traps are enabled by default.                                                        |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# trap interface disabled
	dnRouter(cfg-system-snmp)# trap interface linkUp enabled
	dnRouter(cfg-system-snmp)# trap interface linkDown enabled
	dnRouter(cfg-system-snmp)# trap system coldStart enabled



**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-snmp)# no trap bgp
	dnRouter(cfg-system-snmp)# no trap bgp bgpEstablishedNotification

.. **Help line:** Configure system snmp traps

**Command History**

+---------+------------------------------------------------------+
| Release | Modification                                         |
+=========+======================================================+
| 5.1.0   | Command introduced                                   |
+---------+------------------------------------------------------+
| 6.0     | New BFD traps added                                  |
|         | Applied new hierarchy                                |
+---------+------------------------------------------------------+
| 11.4    | Updated BGP traps and added RSVP traps               |
+---------+------------------------------------------------------+
| 11.5    | Renamed bgpEstablished as bgpEstablishedNotification |
+---------+------------------------------------------------------+


