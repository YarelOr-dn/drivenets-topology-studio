network-services ipsec ike-maps ike-map
---------------------------------------

**Minimum user role:** operator

DNOS supports the IKE map configuration fur tunnels.

**Command syntax: ike-map [ike-map]**

**Command mode:** config

**Hierarchies**

- network-services ipsec ike-maps

**Parameter table**

+-----------+--------------------+------------------+---------+
| Parameter | Description        | Range            | Default |
+===========+====================+==================+=========+
| ike-map   | IKE map parameters | | string         | \-      |
|           |                    | | length 1-255   |         |
+-----------+--------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# ike-maps
    dnRouter(cfg-netsrv-ipsec-ikemaps)# ike-map MyIkeMap


**Removing Configuration**

To remove the IKE map configurations:
::

    dnRouter(cfg-netsrv-ipsec-ikemaps)# no MyIkeMap

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
