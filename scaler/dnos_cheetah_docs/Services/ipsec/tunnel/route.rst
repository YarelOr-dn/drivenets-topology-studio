services ipsec tunnel vrf route
-------------------------------

**Minimum user role:** operator

To configure a static route matching an IP prefix to the configured tunnel:

**Command syntax: route [ip-prefix]** admin-distance [admin-distance]

**Command mode:** config

**Hierarchies**

- services ipsec tunnel vrf

**Note**

- You can set multiple routes for the same tunnel.

**Parameter table**

+----------------+---------------------------------------+--------------+---------+
| Parameter      | Description                           | Range        | Default |
+================+=======================================+==============+=========+
| ip-prefix      | target route destination              | A.B.C.D/x    | \-      |
|                |                                       | X:X::X:X/x   |         |
+----------------+---------------------------------------+--------------+---------+
| admin-distance | administrative-distance for the route | 1-255        | 10      |
+----------------+---------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# tunnel 1 vrf MyVrf
    dnRouter(cfg-srv-ipsec-tun)# route 172.16.172.20/24 admin-distance 20


**Removing Configuration**

To return route admin-distance to default:
::

    dnRouter(cfg-srv-ipsec-tun)# no route 172.16.172.20/24 admin-distance 20

To delete route configured for the tunnel:
::

    dnRouter(cfg-srv-ipsec-tun)# no route 172.16.172.20/24

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
