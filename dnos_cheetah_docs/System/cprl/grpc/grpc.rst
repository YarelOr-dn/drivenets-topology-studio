system cprl grpc
----------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the GRPC protocol:

**Command syntax: grpc**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# grpc
    dnRouter(cfg-system-cprl-grpc)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the GRPC protocol:
::

    dnRouter(cfg-system-cprl)# no grpc

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
