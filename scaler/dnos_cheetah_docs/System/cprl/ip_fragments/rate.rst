system cprl ip-fragments rate
-----------------------------

**Minimum user role:** operator

To set the rate limit of control traffic for IP Fragments:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl ip-fragments

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
    dnRouter(cfg-system-cprl)# ip-fragments
    dnRouter(cfg-system-cprl-ip-fragments)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for IP Fragments:
::

    dnRouter(cfg-system-cprl-ip-fragments)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
