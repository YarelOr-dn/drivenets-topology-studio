system cprl ospfv3 rate
-----------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the OSPFv3 protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl ospfv3

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
    dnRouter(cfg-system-cprl)# ospfv3
    dnRouter(cfg-system-cprl-ospfv3)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the OSPFv3 protocol:
::

    dnRouter(cfg-system-cprl-ospfv3)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
