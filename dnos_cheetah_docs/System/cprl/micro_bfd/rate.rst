system cprl micro-bfd rate
--------------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the Micro-BFD protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl micro-bfd

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
    dnRouter(cfg-system-cprl)# micro-bfd
    dnRouter(cfg-system-cprl-micro-bfd)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the Micro-BFD protocol:
::

    dnRouter(cfg-system-cprl-micro-bfd)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
