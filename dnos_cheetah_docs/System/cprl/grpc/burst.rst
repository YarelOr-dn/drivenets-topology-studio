system cprl grpc burst
----------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the GRPC protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl grpc

**Parameter table**

+------------+---------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                   | Range   | Default |
+============+===============================================================+=========+=========+
| burst-size | Burst size for specific control protocol traffic in [packets] | 2-65024 | 50      |
+------------+---------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# grpc
    dnRouter(cfg-system-cprl-grpc)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the GRPC protocol:
::

    dnRouter(cfg-system-cprl-grpc)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
