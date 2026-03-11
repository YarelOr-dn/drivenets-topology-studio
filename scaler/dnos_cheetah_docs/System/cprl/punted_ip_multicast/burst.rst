system cprl punted-ip-multicast burst
-------------------------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the Punted-IP-Multicast protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl punted-ip-multicast

**Parameter table**

+------------+---------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                   | Range   | Default |
+============+===============================================================+=========+=========+
| burst-size | Burst size for specific control protocol traffic in [packets] | 2-65024 | 6000    |
+------------+---------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# punted-ip-multicast
    dnRouter(cfg-system-cprl-punted-ip-multicast)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the Punted-IP-Multicast protocol:
::

    dnRouter(cfg-system-cprl-punted-ip-multicast)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
