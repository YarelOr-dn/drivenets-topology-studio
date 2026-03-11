system cprl ipv4-pmtud
----------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the IPv4 PMTUD protocol:

**Command syntax: ipv4-pmtud**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ipv4-pmtud
    dnRouter(cfg-system-cprl-ipv4-pmtud)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the IPv4 PMTUD protocol:
::

    dnRouter(cfg-system-cprl)# no ipv4-pmtud

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
