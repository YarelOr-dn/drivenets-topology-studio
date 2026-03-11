system cprl lldp
----------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the LLDP protocol:

**Command syntax: lldp**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# lldp
    dnRouter(cfg-system-cprl-lldp)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the LLDP protocol:
::

    dnRouter(cfg-system-cprl)# no lldp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
