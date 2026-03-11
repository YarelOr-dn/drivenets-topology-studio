system snmp compatibility-mode cisco
------------------------------------

**Minimum user role:** operator

To configure the SNMP compatibility mode with Cisco:

**Command syntax: cisco [admin-state]**

**Command mode:** config

**Hierarchies**

- system snmp compatibility-mode

**Parameter table**

+-------------+-------------------------------+--------------+----------+
| Parameter   | Description                   | Range        | Default  |
+=============+===============================+==============+==========+
| admin-state | SNMP Cisco compatibility-mode | | enabled    | disabled |
|             |                               | | disabled   |          |
+-------------+-------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# snmp
    dnRouter(cfg-system-snmp)# compatibility-mode
    dnRouter(cfg-system-snmp-compatibility)# cisco enabled

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# snmp
    dnRouter(cfg-system-snmp)# compatibility-mode
    dnRouter(cfg-system-snmp-compatibility)# cisco disabled


**Removing Configuration**

To revert the SNMP compatibility with Cisco configuration to default:
::

    dnRouter(cfg-system-snmp-compatibility)# no cisco

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
