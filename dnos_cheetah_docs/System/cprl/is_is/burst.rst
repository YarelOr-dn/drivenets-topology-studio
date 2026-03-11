system cprl is-is burst
-----------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the IS-IS protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl is-is

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
    dnRouter(cfg-system-cprl)# is-is
    dnRouter(cfg-system-cprl-is-is)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the IS-IS protocol:
::

    dnRouter(cfg-system-cprl-is-is)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
