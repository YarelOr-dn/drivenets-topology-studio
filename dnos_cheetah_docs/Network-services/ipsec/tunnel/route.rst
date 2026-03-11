network-services ipsec tunnel ip-prefix
---------------------------------------

**Minimum user role:** operator

To configure a static IP prefix on the configured tunnel:

**Command syntax: ip-prefix [ip-prefix]** admin-distance [admin-distance]

**Command mode:** config

**Hierarchies**

- network-services ipsec tunnel

**Note**

- You can set multiple ip-prefixes for the same tunnel.

**Parameter table**

+----------------+---------------------------------------+----------------+---------+
| Parameter      | Description                           | Range          | Default |
+================+=======================================+================+=========+
| ip-prefix      | target route destination              | | A.B.C.D/x    | \-      |
|                |                                       | | X:X::X:X/x   |         |
+----------------+---------------------------------------+----------------+---------+
| admin-distance | administrative-distance for the route | 1-255          | 10      |
+----------------+---------------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# tunnel 1
    dnRouter(cfg-netsrv-ipsec-tun)# ip-prefix 172.16.172.20/24 admin-distance 20


**Removing Configuration**

To return ip-prefix admin-distance to default:
::

    dnRouter(cfg-srv-ipsec-tun)# no ip-prefix 172.16.172.20/24 admin-distance 20

To delete route configured for the tunnel:
::

    dnRouter(cfg-srv-ipsec-tun)# no ip-prefix 172.16.172.20/24

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
