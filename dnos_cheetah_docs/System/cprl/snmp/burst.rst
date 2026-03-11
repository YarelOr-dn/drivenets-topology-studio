system cprl snmp burst
----------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the SNMP protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl snmp

**Parameter table**

+------------+---------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                   | Range   | Default |
+============+===============================================================+=========+=========+
| burst-size | Burst size for specific control protocol traffic in [packets] | 2-65024 | 4000    |
+------------+---------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# snmp
    dnRouter(cfg-system-cprl-snmp)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the SNMP protocol:
::

    dnRouter(cfg-system-cprl-snmp)# no burst

**Command History**

+---------+-----------------------------------------+
| Release | Modification                            |
+=========+=========================================+
| 10.0    | Command introduced                      |
+---------+-----------------------------------------+
| 11.5    | Changed the default burst rate for SNMP |
+---------+-----------------------------------------+
