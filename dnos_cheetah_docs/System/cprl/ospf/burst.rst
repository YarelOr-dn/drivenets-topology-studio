system cprl ospf burst
----------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the OSPF protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl ospf

**Parameter table**

+------------+---------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                   | Range   | Default |
+============+===============================================================+=========+=========+
| burst-size | Burst size for specific control protocol traffic in [packets] | 2-65024 | 1000    |
+------------+---------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ospf
    dnRouter(cfg-system-cprl-ospf)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the OSPF protocol:
::

    dnRouter(cfg-system-cprl-ospf)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
