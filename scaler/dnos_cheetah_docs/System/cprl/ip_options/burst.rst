system cprl ip-options burst
----------------------------

**Minimum user role:** operator

To set the burst limit of control traffic for IP Options:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl ip-options

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
    dnRouter(cfg-system-cprl)# ip-options
    dnRouter(cfg-system-cprl-ip-options)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for IP Options:
::

    dnRouter(cfg-system-cprl-ip-options)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
