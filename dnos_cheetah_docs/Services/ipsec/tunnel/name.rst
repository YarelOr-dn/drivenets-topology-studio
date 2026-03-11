services ipsec tunnel vrf name
------------------------------

**Minimum user role:** operator

Set the name of the tunnel provided by the user.

**Command syntax: name [name]**

**Command mode:** config

**Hierarchies**

- services ipsec tunnel vrf

**Parameter table**

+-----------+------------------------------------------+----------------+---------+
| Parameter | Description                              | Range          | Default |
+===========+==========================================+================+=========+
| name      | The name of the tunnel provided by user. | string         | \-      |
|           |                                          | length 1-255   |         |
+-----------+------------------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# tunnel 1 vrf MyVrf
    dnRouter(cfg-srv-ipsec-tun)# name MyTunnel


**Removing Configuration**

To remove the configuration of the tunnel name:
::

    dnRouter(cfg-srv-ipsec-tun)# no name

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
