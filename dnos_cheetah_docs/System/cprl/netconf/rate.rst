system cprl netconf rate
------------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the NETCONF protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl netconf

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
    dnRouter(cfg-system-cprl)# netconf
    dnRouter(cfg-system-cprl-netconf)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the NETCONF protocol:
::

    dnRouter(cfg-system-cprl-netconf)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
