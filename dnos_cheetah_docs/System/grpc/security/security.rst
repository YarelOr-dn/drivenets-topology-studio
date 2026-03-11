system grpc security
--------------------

**Minimum user role:** operator

The gRPC protocol supports transport layer security (TSL). The TLS protocol provides private and protected communication between client/server applications. Without TLS, gRPC will establish unsecured sessions.

To configure TLS parameters, enter gRPC security configuration mode:

**Command syntax: security**

**Command mode:** config

**Hierarchies**

- system grpc

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# grpc
    dnRouter(cfg-system-grpc)# security


**Removing Configuration**

To disable TLS for gRPC sessions:
::

    dnRouter(cfg-system-grpc)# no security

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.1    | Command introduced |
+---------+--------------------+
