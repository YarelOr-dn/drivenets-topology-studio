system cprl ntp
---------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the NTP protocol:

**Command syntax: ntp**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ntp
    dnRouter(cfg-system-cprl-ntp)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the NTP protocol:
::

    dnRouter(cfg-system-cprl)# no ntp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
