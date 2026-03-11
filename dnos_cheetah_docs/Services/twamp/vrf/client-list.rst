services twamp vrf client-list
------------------------------

**Minimum user role:** operator

The client-list is used to deny or allow IP addresses. By default, no client-list is configured, so any client can initiate a TWAMP session. When a client-list is configured, the type of list is defined by the client list type parameter. You can add a maximum of 1000 clients.

To configure a black or white list of incoming IP-addresses for the TWAMP service:

**Command syntax: client-list [ip-address]** [, ip-address, ip-address]

**Command mode:** config

**Hierarchies**

- services twamp vrf

**Note**

- Both IPv4 and IPv6 prefixes are supported.

**Parameter table**

+------------+---------------------------------------------------------+----------------+---------+
| Parameter  | Description                                             | Range          | Default |
+============+=========================================================+================+=========+
| ip-address | Configure an incoming IP address for the TWAMP service. | | A.B.C.D/x    | \-      |
|            |                                                         | | X:X::X:X/x   |         |
+------------+---------------------------------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# twamp vrf default
    dnRouter(cfg-srv-twamp-vrf)# client-list 200.10.10.6/32
    dnRouter(cfg-srv-twamp-vrf)# client-list 50.1.22.0/24, 2001:608::/32


**Removing Configuration**

To remove all IP addresses from the list:
::

    dnRouter(cfg-srv-twamp-vrf)# no client-list

To remove a specific IP address from the list:
::

    dnRouter(cfg-srv-twamp-vrf)# no client-list 50.1.22.0/24

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 6.0     | Command introduced                 |
+---------+------------------------------------+
| 9.0     | TWAMP not supported                |
+---------+------------------------------------+
| 11.2    | Command re-introduced              |
+---------+------------------------------------+
| 16.2    | Moved under VRF hierarchy          |
+---------+------------------------------------+
| 17.0    | Extended support for IPv6 prefixes |
+---------+------------------------------------+
