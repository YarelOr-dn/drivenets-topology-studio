system cprl bgp
---------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the BGP protocol:

**Command syntax: bgp**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# bgp
    dnRouter(cfg-system-cprl-bgp)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the BGP protocol:
::

    dnRouter(cfg-system-cprl)# no bgp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
