network-services ipsec ike-maps global-ike-map ipsec-encryption-algorithm
-------------------------------------------------------------------------

**Minimum user role:** operator

Encryption algorithm type that are permitted for phase 2 of the IKE negotiations.

**Command syntax: ipsec-encryption-algorithm [ipsec-encryption-algorithm]**

**Command mode:** config

**Hierarchies**

- network-services ipsec ike-maps global-ike-map

**Parameter table**

+----------------------------+----------------------------------------------------------------------------------+-----------------+-------------+
| Parameter                  | Description                                                                      | Range           | Default     |
+============================+==================================================================================+=================+=============+
| ipsec-encryption-algorithm | encryption algorithm type that are permitted for phase 2 of the IKE negotiations | | AES-256-GCM   | AES-256-GCM |
|                            |                                                                                  | | AES-256-CBC   |             |
+----------------------------+----------------------------------------------------------------------------------+-----------------+-------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# ike-maps
    dnRouter(cfg-netsrv-ipsec-ikemaps)# global-ike-map
    dnRouter(cfg-netsrv-ipsec-glbl-ikemap)# ipsec-encryption-algorithm AES-128-CBC


**Removing Configuration**

To remove the configuration of the ipsec-encryption-algorithm:
::

    dnRouter(cfg-netsrv-ipsec-glbl-ikemap)# no ipsec-encryption-algorithm

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
