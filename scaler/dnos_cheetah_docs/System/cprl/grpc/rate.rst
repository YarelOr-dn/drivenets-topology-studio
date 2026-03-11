system cprl grpc rate
---------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the GRPC protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl grpc

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 50      |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# grpc
    dnRouter(cfg-system-cprl-grpc)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the GRPC protocol:
::

    dnRouter(cfg-system-cprl-grpc)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
