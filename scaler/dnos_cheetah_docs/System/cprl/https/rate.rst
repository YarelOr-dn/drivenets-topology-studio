system cprl https rate
----------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the HTTPS protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl https

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 10000   |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# https
    dnRouter(cfg-system-cprl-https)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the HTTPS protocol:
::

    dnRouter(cfg-system-cprl-https)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
