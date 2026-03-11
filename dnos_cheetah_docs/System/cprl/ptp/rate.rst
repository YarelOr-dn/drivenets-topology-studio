system cprl ptp rate
--------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the PTP 1588v2 protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl ptp

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 1000    |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ptp
    dnRouter(cfg-system-cprl-ptp)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the PTP 1588v2 protocol:
::

    dnRouter(cfg-system-cprl-ptp)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
