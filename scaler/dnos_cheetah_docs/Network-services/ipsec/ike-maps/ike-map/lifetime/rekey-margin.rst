network-services ipsec ike-maps ike-map lifetime rekey-margin
-------------------------------------------------------------

**Minimum user role:** operator

The period of time before the key/auth expires and the system initiates the rekey/reauth.

**Command syntax: rekey-margin [rekey-margin]**

**Command mode:** config

**Hierarchies**

- network-services ipsec ike-maps ike-map lifetime

**Parameter table**

+--------------+-------------------------------------------------------------------------------+-------------------+---------+
| Parameter    | Description                                                                   | Range             | Default |
+==============+===============================================================================+===================+=========+
| rekey-margin | the period of time before key/auth expires which stronglahav initiates rekey. | 0, 300-4294967295 | \-      |
+--------------+-------------------------------------------------------------------------------+-------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# ike-maps
    dnRouter(cfg-netsrv-ipsec-ikemaps)# ike-map MyIkeMap
    dnRouter(cfg-netsrv-ipsec-ikemaps)# lifetime
    dnRouter(cfg-netsrv-ipsec-ikemaps-life)# rekey-margin 540


**Removing Configuration**

To remove the configuration of the rekey-margin:
::

    dnRouter(cfg-netsrv-ipsec-ikemaps-life)# no rekey-margin

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
