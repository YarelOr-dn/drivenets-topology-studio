system cprl icmpv6
------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the ICMPv6 protocol:

**Command syntax: icmpv6**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# icmpv6
    dnRouter(cfg-system-cprl-icmpv6)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the ICMPv6 protocol:
::

    dnRouter(cfg-system-cprl)# no icmpv6

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
