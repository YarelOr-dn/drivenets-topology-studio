network-services ipsec ike-maps ike-map ike-integrity-algorithm
---------------------------------------------------------------

**Minimum user role:** operator

Integrity algorithm type that are permitted for phase 1 of the IKE negotiations.

**Command syntax: ike-integrity-algorithm [ike-integrity-algorithm]**

**Command mode:** config

**Hierarchies**

- network-services ipsec ike-maps ike-map

**Parameter table**

+-------------------------+---------------------------------------------------------------------------------+----------+---------+
| Parameter               | Description                                                                     | Range    | Default |
+=========================+=================================================================================+==========+=========+
| ike-integrity-algorithm | integrity algorithm type that are permitted for phase 1 of the IKE negotiations | SHA2-256 | \-      |
+-------------------------+---------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# ike-maps
    dnRouter(cfg-netsrv-ipsec-ikemaps)# ike-map MyIkeMap
    dnRouter(cfg-netsrv-ipsec-ikemaps)# ike-integrity-algorithm AES-128-CBC


**Removing Configuration**

To remove the configuration of the ike-integrity-algorithm:
::

    dnRouter(cfg-netsrv-ipsec-ikemaps)# no ike-integrity-algorithm

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
