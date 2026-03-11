system cprl twamp rate
----------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the TWAMP protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl twamp

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 110     |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# twamp
    dnRouter(cfg-system-cprl-twamp)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the TWAMP protocol:
::

    dnRouter(cfg-system-cprl-twamp)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
