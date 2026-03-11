system cprl igmp
----------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the IGMP protocol:

**Command syntax: igmp**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# igmp
    dnRouter(cfg-system-cprl-igmp)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the IGMP protocol:
::

    dnRouter(cfg-system-cprl)# no igmp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
