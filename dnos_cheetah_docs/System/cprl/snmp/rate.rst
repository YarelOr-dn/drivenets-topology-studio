system cprl snmp rate
---------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the SNMP protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl snmp

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 2000    |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# snmp
    dnRouter(cfg-system-cprl-snmp)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the SNMP protocol:
::

    dnRouter(cfg-system-cprl-snmp)# no rate

**Command History**

+---------+----------------------------------------------+
| Release | Modification                                 |
+=========+==============================================+
| 10.0    | Command introduced                           |
+---------+----------------------------------------------+
| 11.5    | Changed the default CPRL rate value for SNMP |
+---------+----------------------------------------------+
