system cprl esmc rate
---------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the SyncE ESMC protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl esmc

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
    dnRouter(cfg-system-cprl)# esmc
    dnRouter(cfg-system-cprl-esmc)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the SyncE ESMC protocol:
::

    dnRouter(cfg-system-cprl-esmc)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
