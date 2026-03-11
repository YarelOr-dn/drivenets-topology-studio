network-services ipsec ike-maps ike-map lifetime ipsec-rekey-interval
---------------------------------------------------------------------

**Minimum user role:** operator

Set the ipsec-rekey-interval in seconds for the configured tunnel. When rekey-interval=0, no rekey is performed.

**Command syntax: ipsec-rekey-interval [ipsec-rekey-interval]**

**Command mode:** config

**Hierarchies**

- network-services ipsec ike-maps ike-map lifetime

**Parameter table**

+----------------------+-------------------------------------------------------------------------+-------------------+---------+
| Parameter            | Description                                                             | Range             | Default |
+======================+=========================================================================+===================+=========+
| ipsec-rekey-interval | Time in seconds between each IPsec SA rekey.The value 0 means infinite. | 0, 300-4294967295 | \-      |
+----------------------+-------------------------------------------------------------------------+-------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# ike-maps
    dnRouter(cfg-netsrv-ipsec-ikemaps)# ike-map MyIkeMap
    dnRouter(cfg-netsrv-ipsec-ikemaps)# lifetime
    dnRouter(cfg-netsrv-ipsec-ikemaps-life)# ipsec-rekey-interval 3600


**Removing Configuration**

To remove the configuration of the ipsec-rekey-interval:
::

    dnRouter(cfg-netsrv-ipsec-ikemaps-life)# no ipsec-rekey-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
