system cprl lacp burst
----------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the LACP protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl lacp

**Parameter table**

+------------+---------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                   | Range   | Default |
+============+===============================================================+=========+=========+
| burst-size | Burst size for specific control protocol traffic in [packets] | 2-65024 | 300     |
+------------+---------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# lacp
    dnRouter(cfg-system-cprl-lacp)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the LACP protocol:
::

    dnRouter(cfg-system-cprl-lacp)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
