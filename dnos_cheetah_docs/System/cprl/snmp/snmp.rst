system cprl snmp
----------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the SNMP protocol:

**Command syntax: snmp**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# snmp
    dnRouter(cfg-system-cprl-snmp)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the SNMP protocol:
::

    dnRouter(cfg-system-cprl)# no snmp

**Command History**

+---------+---------------------------------------------------------+
| Release | Modification                                            |
+=========+=========================================================+
| 10.0    | Command introduced                                      |
+---------+---------------------------------------------------------+
| 11.5    | Changed the default CPRL burst and rate values for SNMP |
+---------+---------------------------------------------------------+
