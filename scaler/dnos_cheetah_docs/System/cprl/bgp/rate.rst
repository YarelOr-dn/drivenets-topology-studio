system cprl bgp rate
--------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the BGP protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl bgp

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 5000    |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# bgp
    dnRouter(cfg-system-cprl-bgp)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the BGP protocol:
::

    dnRouter(cfg-system-cprl-bgp)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
