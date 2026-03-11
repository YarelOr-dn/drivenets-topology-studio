system cprl ip-fragments
------------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for IP Fragments:

**Command syntax: ip-fragments**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ip-fragments
    dnRouter(cfg-system-cprl-ip-fragments)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for IP Fragments:
::

    dnRouter(cfg-system-cprl)# no ip-fragments

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
