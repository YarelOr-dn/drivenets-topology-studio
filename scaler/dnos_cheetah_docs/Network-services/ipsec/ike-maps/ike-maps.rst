network-services ipsec ike-maps
-------------------------------

**Minimum user role:** operator

Configuration parameters for the IPsec ike-maps.

**Command syntax: ike-maps**

**Command mode:** config

**Hierarchies**

- network-services ipsec

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# ike-maps


**Removing Configuration**

To remove all configured ike-maps:
::

    dnRouter(cfg-netsrv-ipsec)# no ike-maps

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
