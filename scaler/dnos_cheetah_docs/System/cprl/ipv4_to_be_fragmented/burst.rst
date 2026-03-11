system cprl ipv4-to-be-fragmented burst
---------------------------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the IPv4-to-be-fragmented protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl ipv4-to-be-fragmented

**Parameter table**

+------------+---------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                   | Range   | Default |
+============+===============================================================+=========+=========+
| burst-size | Burst size for specific control protocol traffic in [packets] | 2-65024 | 500     |
+------------+---------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ipv4-to-be-fragmented
    dnRouter(cfg-system-cprl-ipv4-to-be-fragmented)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the IPv4-to-be-fragmented protocol:
::

    dnRouter(cfg-system-cprl-ipv4-to-be-fragmented)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
