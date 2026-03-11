system cprl igmp burst
----------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the IGMP protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl igmp

**Parameter table**

+------------+---------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                   | Range   | Default |
+============+===============================================================+=========+=========+
| burst-size | Burst size for specific control protocol traffic in [packets] | 2-65024 | 600     |
+------------+---------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# igmp
    dnRouter(cfg-system-cprl-igmp)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the IGMP protocol:
::

    dnRouter(cfg-system-cprl-igmp)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
