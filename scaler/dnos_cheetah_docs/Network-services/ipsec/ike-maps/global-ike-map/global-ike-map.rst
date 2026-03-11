network-services ipsec ike-maps global-ike-map
----------------------------------------------

**Minimum user role:** operator

Configuration of parameters for IPsec global ike map.

**Command syntax: global-ike-map**

**Command mode:** config

**Hierarchies**

- network-services ipsec ike-maps

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# ike-maps
    dnRouter(cfg-netsrv-ipsec-ikemaps)# global-ike-map


**Removing Configuration**

To remove global-ike-map configuration:
::

    dnRouter(cfg-netsrv-ipsec)# no global-ike-map

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
