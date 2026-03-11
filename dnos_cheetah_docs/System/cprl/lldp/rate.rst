system cprl lldp rate
---------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the LLDP protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl lldp

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 300     |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# lldp
    dnRouter(cfg-system-cprl-lldp)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the LLDP protocol:
::

    dnRouter(cfg-system-cprl-lldp)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
