system cprl punted-ip-multicast
-------------------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the Punted-IP-Multicast protocol:

**Command syntax: punted-ip-multicast**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# punted-ip-multicast
    dnRouter(cfg-system-cprl-punted-ip-multicast)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the Punted-IP-Multicast protocol:
::

    dnRouter(cfg-system-cprl)# no punted-ip-multicast

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
