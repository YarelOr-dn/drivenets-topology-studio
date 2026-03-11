network-services ipsec ike-maps global-ike-map ipsec-integrity-algorithm
------------------------------------------------------------------------

**Minimum user role:** operator

Integrity algorithm type that are permitted for phase 2 of the IKE negotiations.

**Command syntax: ipsec-integrity-algorithm [ipsec-integrity-algorithm]**

**Command mode:** config

**Hierarchies**

- network-services ipsec ike-maps global-ike-map

**Parameter table**

+---------------------------+---------------------------------------------------------------------------------+----------+----------+
| Parameter                 | Description                                                                     | Range    | Default  |
+===========================+=================================================================================+==========+==========+
| ipsec-integrity-algorithm | integrity algorithm type that are permitted for phase 2 of the IKE negotiations | SHA2-256 | SHA2-256 |
+---------------------------+---------------------------------------------------------------------------------+----------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# ike-maps
    dnRouter(cfg-netsrv-ipsec-ikemaps)# global-ike-map
    dnRouter(cfg-netsrv-ipsec-glbl-ikemap)# ipsec-integrity-algorithm AES-128-CBC


**Removing Configuration**

To remove the configuration of the ipsec-integrity-algorithm:
::

    dnRouter(cfg-netsrv-ipsec-glbl-ikemap)# no ipsec-integrity-algorithm

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
