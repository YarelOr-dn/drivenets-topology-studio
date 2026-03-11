system cprl netconf
-------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the NETCONF protocol:

**Command syntax: netconf**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# netconf
    dnRouter(cfg-system-cprl-netconf)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the NETCONF protocol:
::

    dnRouter(cfg-system-cprl)# no netconf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
