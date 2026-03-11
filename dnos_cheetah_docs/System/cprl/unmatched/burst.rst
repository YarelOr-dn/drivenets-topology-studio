system cprl unmatched burst
---------------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the Unmatched protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl unmatched

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
    dnRouter(cfg-system-cprl)# unmatched
    dnRouter(cfg-system-cprl-unmatched)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the Unmatched protocol:
::

    dnRouter(cfg-system-cprl-unmatched)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
