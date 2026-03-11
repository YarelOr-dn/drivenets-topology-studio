network-services ipsec ike-maps global-ike-map lifetime ike-reauth-interval
---------------------------------------------------------------------------

**Minimum user role:** operator

Set the ike-reauth-interval in seconds for the configured tunnel. When the reauth-interval=0, no reauth is performed.

**Command syntax: ike-reauth-interval [ike-reauth-interval]**

**Command mode:** config

**Hierarchies**

- network-services ipsec ike-maps global-ike-map lifetime

**Parameter table**

+---------------------+----------------------------------------------------------------------------------+-------------------+---------+
| Parameter           | Description                                                                      | Range             | Default |
+=====================+==================================================================================+===================+=========+
| ike-reauth-interval | Time in seconds between each IKE SA reauthentication. The value 0 means          | 0, 300-4294967295 | 0       |
|                     | infinite.                                                                        |                   |         |
+---------------------+----------------------------------------------------------------------------------+-------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# ike-maps
    dnRouter(cfg-netsrv-ipsec-ikemaps)# global-ike-map
    dnRouter(cfg-netsrv-ipsec-glbl-ikemap)# lifetime
    dnRouter(cfg-netsrv-ipsec-glbl-ikemap)# ike-reauth-interval 14400


**Removing Configuration**

To remove the configuration of the ike-reauth-interval:
::

    dnRouter(cfg-netsrv-ipsec-glbl-ikemap)# no ike-reauth-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
