system cprl ttl-expired burst
-----------------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the TTL-expired protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl ttl-expired

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
    dnRouter(cfg-system-cprl)# ttl-expired
    dnRouter(cfg-system-cprl-ttl-expired)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the TTL-expired protocol:
::

    dnRouter(cfg-system-cprl-ttl-expired)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
