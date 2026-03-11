system cprl is-is rate
----------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the IS-IS protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl is-is

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 500     |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# is-is
    dnRouter(cfg-system-cprl-is-is)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the IS-IS protocol:
::

    dnRouter(cfg-system-cprl-is-is)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
