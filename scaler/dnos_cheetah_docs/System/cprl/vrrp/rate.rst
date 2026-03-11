system cprl vrrp rate
---------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the VRRP protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl vrrp

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
    dnRouter(cfg-system-cprl)# vrrp
    dnRouter(cfg-system-cprl-vrrp)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the VRRP protocol:
::

    dnRouter(cfg-system-cprl-vrrp)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
