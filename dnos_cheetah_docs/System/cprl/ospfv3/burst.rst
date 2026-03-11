system cprl ospfv3 burst
------------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the OSPFv3 protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl ospfv3

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
    dnRouter(cfg-system-cprl)# ospfv3
    dnRouter(cfg-system-cprl-ospfv3)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the OSPFv3 protocol:
::

    dnRouter(cfg-system-cprl-ospfv3)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
