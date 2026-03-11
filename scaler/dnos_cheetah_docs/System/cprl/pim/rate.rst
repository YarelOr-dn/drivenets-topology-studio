system cprl pim rate
--------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the PIM protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl pim

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 600     |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# pim
    dnRouter(cfg-system-cprl-pim)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the PIM protocol:
::

    dnRouter(cfg-system-cprl-pim)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
