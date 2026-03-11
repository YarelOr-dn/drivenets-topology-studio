system cprl netconf burst
-------------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the NETCONF protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl netconf

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
    dnRouter(cfg-system-cprl)# netconf
    dnRouter(cfg-system-cprl-netconf)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the NETCONF protocol:
::

    dnRouter(cfg-system-cprl-netconf)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
