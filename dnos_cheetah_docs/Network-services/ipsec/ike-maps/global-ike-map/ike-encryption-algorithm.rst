network-services ipsec ike-maps global-ike-map ike-encryption-algorithm
-----------------------------------------------------------------------

**Minimum user role:** operator

Encryption algorithm type that are permitted for phase 2 of the IKE negotiations.

**Command syntax: ike-encryption-algorithm [ike-encryption-algorithm]**

**Command mode:** config

**Hierarchies**

- network-services ipsec ike-maps global-ike-map

**Parameter table**

+--------------------------+----------------------------------------------------------------------------------+-----------------+-------------+
| Parameter                | Description                                                                      | Range           | Default     |
+==========================+==================================================================================+=================+=============+
| ike-encryption-algorithm | encryption algorithm type that are permitted for phase 1 of the IKE negotiations | | AES-256-GCM   | AES-256-CBC |
|                          |                                                                                  | | AES-256-CBC   |             |
+--------------------------+----------------------------------------------------------------------------------+-----------------+-------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# ike-maps
    dnRouter(cfg-netsrv-ipsec-ikemaps)# global-ike-map
    dnRouter(cfg-netsrv-ipsec-glbl-ikemap)# ike-encryption-algorithm AES-128-CBC


**Removing Configuration**

To remove the configuration of the ike-encryption-algorithm:
::

    dnRouter(cfg-netsrv-ipsec-glbl-ikemap)# no ike-encryption-algorithm

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
