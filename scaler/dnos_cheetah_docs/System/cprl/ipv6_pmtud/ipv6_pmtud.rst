system cprl ipv6-pmtud
----------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the IPv6 PMTUD protocol:

**Command syntax: ipv6-pmtud**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ipv6-pmtud
    dnRouter(cfg-system-cprl-ipv6-pmtud)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the IPv6 PMTUD protocol:
::

    dnRouter(cfg-system-cprl)# no ipv6-pmtud

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
