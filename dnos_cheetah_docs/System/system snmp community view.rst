system snmp community view
--------------------------

**Minimum user role:** operator

A view is a collection of MIB object types that you want to group together to restrict or provide access to SNMP objects. For information on configuring SNMP views, see system snmp view.

To configure a view for the community:

**Command syntax: view [view]**

**Command mode:** config

**Hierarchies**

- system snmp community

.. **Note**

	- An SNMP community can only have 1 view attached

	- no command reverts the snmp view configuration to default config

**Parameter table**

+-----------+-------------------------------------------------------------------------------------------------------------+--------+-------------+
| Parameter | Description                                                                                                 | Range  | Default     |
+===========+=============================================================================================================+========+=============+
| view      | Select an existing view for the community. For information on configuring SNMP views, see system snmp view. | string | viewdefault |
|           | Only one view is allowed per community.                                                                     |        |             |
+-----------+-------------------------------------------------------------------------------------------------------------+--------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# community MySnmpCommunity vrf default
	dnRouter(cfg-system-snmp-community)# view MySnmpView
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-snmp-community)# no view

.. **Help line:** Configure system snmp community view

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 5.1.0   | Command introduced                  |
+---------+-------------------------------------+
| 6.0     | Applied new hierarchy for SNMP      |
+---------+-------------------------------------+
| 9.0     | Applied new hierarchy for community |
+---------+-------------------------------------+


