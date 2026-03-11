network-services ipsec ike-maps ike-map lifetime
------------------------------------------------

**Minimum user role:** operator

DNOS supports the IPSec tunnels configurable lifetime parameters.

**Command syntax: lifetime**

**Command mode:** config

**Hierarchies**

- network-services ipsec ike-maps ike-map

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# ike-maps
    dnRouter(cfg-netsrv-ipsec-ikemaps)# ike-map MyIkeMap
    dnRouter(cfg-netsrv-ipsec-ikemaps)# lifetime
    dnRouter(cfg-netsrv-ipsec-ikemaps-life)#


**Removing Configuration**

To remove the IPSec lifetime parameters:
::

    dnRouter(cfg-netsrv-ipsec-ikemaps)# no lifetime

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
