system cprl ipv4-to-be-fragmented
---------------------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the IPv4-to-be-fragmented protocol:

**Command syntax: ipv4-to-be-fragmented**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ipv4-to-be-fragmented
    dnRouter(cfg-system-cprl-ipv4-to-be-fragmented)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the IPv4-to-be-fragmented protocol:
::

    dnRouter(cfg-system-cprl)# no ipv4-to-be-fragmented

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
