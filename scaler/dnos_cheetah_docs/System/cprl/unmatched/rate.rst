system cprl unmatched rate
--------------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the Unmatched protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl unmatched

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 2000    |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# unmatched
    dnRouter(cfg-system-cprl-unmatched)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the Unmatched protocol:
::

    dnRouter(cfg-system-cprl-unmatched)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
