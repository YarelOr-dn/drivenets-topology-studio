system snmp user view
---------------------

**Minimum user role:** operator

To configure SNMP user authentication:

**Command syntax: view [view-name]**

**Command mode:** config

**Hierarchies**

- system snmp

.. **Note**

	- validation: snmp view must be pre-configured in "system snmp view" for the user view configuration to apply (values for this command should be auto-complete)

	- by default, a user has view value of "viewdefault"(default snmp view in the system)

	- no command removes the specific view configuration

**Parameter table**

+-----------+-----------------------------------------------------------------------------+--------+-------------+
| Parameter | Description                                                                 | Range  | Default     |
+===========+=============================================================================+========+=============+
| view-name | The name of the view collection allowed for the user. See system snmp view. | String | viewdefault |
+-----------+-----------------------------------------------------------------------------+--------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# user MySnmpUser2 
	dnRouter(cfg-system-snmp-user)# view MyAllView
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-snmp-user)# no view

.. **Help line:** Configure system snmp user view

**Command History**

+---------+--------------------------------+
| Release | Modification                   |
+=========+================================+
| 5.1.0   | Command introduced             |
+---------+--------------------------------+
| 6.0     | Applied new hierarchy for SNMP |
+---------+--------------------------------+
| 9.0     | Applied new hierarchy for user |
+---------+--------------------------------+

