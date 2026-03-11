system cprl simple-twamp rate
-----------------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the Simple TWAMP protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl simple-twamp

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 2000    |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# simple-twamp
    dnRouter(cfg-system-cprl-simple-twamp)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the Simple TWAMP protocol:
::

    dnRouter(cfg-system-cprl-simple-twamp)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
