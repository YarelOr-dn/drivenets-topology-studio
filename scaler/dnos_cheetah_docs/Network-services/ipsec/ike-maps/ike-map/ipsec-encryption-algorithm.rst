network-services ipsec ike-maps ike-map ipsec-encryption-algorithm
------------------------------------------------------------------

**Minimum user role:** operator

Encryption algorithm type that are permitted for phase 1 of the IKE negotiations.

**Command syntax: ipsec-encryption-algorithm [ipsec-encryption-algorithm]**

**Command mode:** config

**Hierarchies**

- network-services ipsec ike-maps ike-map

**Parameter table**

+----------------------------+----------------------------------------------------------------------------------+-----------------+---------+
| Parameter                  | Description                                                                      | Range           | Default |
+============================+==================================================================================+=================+=========+
| ipsec-encryption-algorithm | encryption algorithm type that are permitted for phase 2 of the IKE negotiations | | AES-256-GCM   | \-      |
|                            |                                                                                  | | AES-256-CBC   |         |
+----------------------------+----------------------------------------------------------------------------------+-----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# ike-maps
    dnRouter(cfg-netsrv-ipsec-ikemaps)# ike-map MyIkeMap
    dnRouter(cfg-netsrv-ipsec-ikemaps)# ipsec-encryption-algorithm AES-128-CBC


**Removing Configuration**

To remove the configuration of the ipsec-encryption-algorithm:
::

    dnRouter(cfg-netsrv-ipsec-ikemaps)# no ipsec-encryption-algorithm

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
