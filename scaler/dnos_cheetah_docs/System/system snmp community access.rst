system snmp community access
----------------------------

**Minimum user role:** operator

You can set the following access rights for the SNMP community:

Read-only - The device responds to SNMP Get, GetNext, and GetBulk commands

To set the SNMP community authorization:

**Command syntax: access [authorization]**

**Command mode:** config

**Hierarchies**

- system snmp community

.. **Note**

    - By default, snmp community access is read-only

    - no command reverts the snmp community access to its default value

**Parameter table**

+-----------+---------------------------------------+------------+-----------+
| Parameter | Description                           | Range      | Default   |
+===========+=======================================+============+===========+
| access    | The access rights for SNMP community. | read-only  | read-only |
+-----------+---------------------------------------+------------+-----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# snmp
    dnRouter(cfg-system-snmp)# community MyPublicSnmpCommunity vrf default
    dnRouter(cfg-system-snmp-community)# access read-only

    dnRouter(cfg-system-snmp)# community MyPrivateSnmpCommunity vrf mgmt0
    dnRouter(cfg-system-snmp-community)# access read-write


**Removing Configuration**

To revert the router-id to default:
::

    dnRouter(cfg-system-snmp-community)# no access

.. **Help line:** Configure system snmp community

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
| 18.1    | Removed the access right read-write |
+---------+-------------------------------------+
