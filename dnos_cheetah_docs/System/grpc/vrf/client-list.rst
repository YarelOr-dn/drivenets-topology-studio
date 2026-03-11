system grpc vrf client-list
---------------------------

**Minimum user role:** operator

Create a list of clients that are permitted or denied to open gRPC sessions to the system (according to \"system grpc vrf client-list type\".

To configure a client-list:

**Command syntax: client-list [ipv4-address/ipv6-address]** [, ipv4-address/ipv6-address, ipv4-address/ipv6-address]

**Command mode:** config

**Hierarchies**

- system grpc vrf

**Note**

- You can add up to 20 clients (for both IPv4 and IPv6 addresses combined) per VRF.

**Parameter table**

+---------------------------+------------------------------------------------------------------------------+----------------+---------+
| Parameter                 | Description                                                                  | Range          | Default |
+===========================+==============================================================================+================+=========+
| ipv4-address/ipv6-address | Black/white list of incoming ip-prefixes for system in-band gNMI/gRPC server | | A.B.C.D/x    | \-      |
|                           |                                                                              | | X:X::X:X/x   |         |
+---------------------------+------------------------------------------------------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# grpc vrf default
    dnRouter(cfg-system-grpc-vrf)# client-list 100.54.12.1/32
    dnRouter(cfg-system-grpc-vrf)# client-list 210.4.21.0/24
    dnRouter(cfg-system-grpc-vrf)# client-list 2001:db8:2222::/48


**Removing Configuration**

To remove a specific client from the client list:
::

    dnRouter(cfg-system-grpc-vrf)# no client-list 100.54.12.1/32

To remove all clients from the client-list:
::

    dnRouter(cfg-system-grpc-vrf)# no client-list

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
