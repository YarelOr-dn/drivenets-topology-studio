system cprl vrrp burst
----------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the VRRP protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl vrrp

**Parameter table**

+------------+---------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                   | Range   | Default |
+============+===============================================================+=========+=========+
| burst-size | Burst size for specific control protocol traffic in [packets] | 2-65024 | 2000    |
+------------+---------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# vrrp
    dnRouter(cfg-system-cprl-vrrp)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the VRRP protocol:
::

    dnRouter(cfg-system-cprl-vrrp)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
