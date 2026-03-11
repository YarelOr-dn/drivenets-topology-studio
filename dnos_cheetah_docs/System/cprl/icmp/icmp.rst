system cprl icmp
----------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the ICMP protocol:

**Command syntax: icmp**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# icmp
    dnRouter(cfg-system-cprl-icmp)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the ICMP protocol:
::

    dnRouter(cfg-system-cprl)# no icmp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
