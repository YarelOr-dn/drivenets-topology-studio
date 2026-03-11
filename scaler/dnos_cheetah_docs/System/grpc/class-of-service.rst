system grpc class-of-service
----------------------------

**Minimum user role:** operator

Set the DSCP values for DNOS gRPC:

**Command syntax: class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- system grpc

**Parameter table**

+------------------+-------------------------------------------------------------+-------+---------+
| Parameter        | Description                                                 | Range | Default |
+==================+=============================================================+=======+=========+
| class-of-service | This parameter specifies the dscp of generated gRPC packets | 0-56  | 16      |
+------------------+-------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# grpc
    dnRouter(cfg-system-grpc)# class-of-service 32


**Removing Configuration**

To revert DSCP to default:
::

    dnRouter(cfg-system-grpc)# no class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
