system cprl https burst
-----------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the HTTPS protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl https

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
    dnRouter(cfg-system-cprl)# https
    dnRouter(cfg-system-cprl-https)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the HTTPS protocol:
::

    dnRouter(cfg-system-cprl-https)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
