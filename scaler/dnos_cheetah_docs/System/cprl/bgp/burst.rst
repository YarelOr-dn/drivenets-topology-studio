system cprl bgp burst
---------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the BGP protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl bgp

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
    dnRouter(cfg-system-cprl)# bgp
    dnRouter(cfg-system-cprl-bgp)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the BGP protocol:
::

    dnRouter(cfg-system-cprl-bgp)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
