network-services ipsec ike-maps global-ike-map lifetime ike-rekey-interval
--------------------------------------------------------------------------

**Minimum user role:** operator

Set the ike-rekey-interval in seconds for the configured tunnel. When the rekey-interval=0, no rekey is performed.

**Command syntax: ike-rekey-interval [ike-rekey-interval]**

**Command mode:** config

**Hierarchies**

- network-services ipsec ike-maps global-ike-map lifetime

**Parameter table**

+--------------------+-----------------------------------------------------------------------+-------------------+---------+
| Parameter          | Description                                                           | Range             | Default |
+====================+=======================================================================+===================+=========+
| ike-rekey-interval | Time in seconds between each IKE SA rekey.The value 0 means infinite. | 0, 300-4294967295 | 14400   |
+--------------------+-----------------------------------------------------------------------+-------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# ike-maps
    dnRouter(cfg-netsrv-ipsec-ikemaps)# global-ike-map
    dnRouter(cfg-netsrv-ipsec-glbl-ikemap)# lifetime
    dnRouter(cfg-netsrv-ipsec-glbl-ikemap)# ike-rekey-interval 14400


**Removing Configuration**

To remove the configuration of the ike-rekey-interval:
::

    dnRouter(cfg-netsrv-ipsec-glbl-ikemap)# no ike-rekey-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
