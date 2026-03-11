system cprl mac-unresolved rate
-------------------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the MAC-Unresolved protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl mac-unresolved

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 50      |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# mac-unresolved
    dnRouter(cfg-system-cprl-mac-unresolved)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the MAC-Unresolved protocol:
::

    dnRouter(cfg-system-cprl-mac-unresolved)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
