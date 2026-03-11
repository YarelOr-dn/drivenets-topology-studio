system cprl ptp burst
---------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the PTP 1588v2 protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl ptp

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
    dnRouter(cfg-system-cprl)# ptp
    dnRouter(cfg-system-cprl-ptp)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the PTP 1588v2 protocol:
::

    dnRouter(cfg-system-cprl-ptp)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
