system snmp compatibility-mode
------------------------------

**Minimum user role:** operator

To configure SNMP compatibility mode:

**Command syntax: compatibility-mode**

**Command mode:** config

**Hierarchies**

- system snmp

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# snmp
    dnRouter(cfg-system-snmp)# compatibility-mode
    dnRouter(cfg-system-snmp-compatibility)#


**Removing Configuration**

To revert the compatibility-mode configuration to its default value:
::

    dnRouter(cfg-system-snmp)# no compatibility-mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
