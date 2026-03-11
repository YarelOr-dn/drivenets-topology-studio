system cprl dhcp
----------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the DHCP protocol:

**Command syntax: dhcp**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# dhcp
    dnRouter(cfg-system-cprl-dhcp)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the DHCP protocol:
::

    dnRouter(cfg-system-cprl)# no dhcp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
