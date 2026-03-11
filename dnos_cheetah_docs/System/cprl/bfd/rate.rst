system cprl bfd rate
--------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the BFD protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl bfd

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 4000    |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# bfd
    dnRouter(cfg-system-cprl-bfd)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the BFD protocol:
::

    dnRouter(cfg-system-cprl-bfd)# no rate

**Command History**

+---------+----------------------------------------+
| Release | Modification                           |
+=========+========================================+
| 10.0    | Command introduced                     |
+---------+----------------------------------------+
| 15.1    | Updated the default CPRL value for BFD |
+---------+----------------------------------------+
