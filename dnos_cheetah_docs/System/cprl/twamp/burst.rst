system cprl twamp burst
-----------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the TWAMP protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl twamp

**Parameter table**

+------------+---------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                   | Range   | Default |
+============+===============================================================+=========+=========+
| burst-size | Burst size for specific control protocol traffic in [packets] | 2-65024 | 550     |
+------------+---------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# twamp
    dnRouter(cfg-system-cprl-twamp)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the TWAMP protocol:
::

    dnRouter(cfg-system-cprl-twamp)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
