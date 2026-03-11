system cprl ptp
---------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the PTP 1588v2 protocol:

**Command syntax: ptp**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ptp
    dnRouter(cfg-system-cprl-ptp)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the PTP 1588v2 protocol:
::

    dnRouter(cfg-system-cprl)# no ptp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
