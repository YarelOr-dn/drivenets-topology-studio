system cprl all-routers rate
----------------------------

**Minimum user role:** operator

To set the rate limit of control traffic for all routers:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl all-routers

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
    dnRouter(cfg-system-cprl)# all-routers
    dnRouter(cfg-system-cprl-all-routers)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value:
::

    dnRouter(cfg-system-cprl-all-routers)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
