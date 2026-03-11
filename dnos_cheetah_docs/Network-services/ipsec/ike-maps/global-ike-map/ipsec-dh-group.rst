network-services ipsec ike-maps global-ike-map ipsec-dh-group
-------------------------------------------------------------

**Minimum user role:** operator

Set the ipsec-dh-group for the tunnel establishment against the device.

**Command syntax: ipsec-dh-group [ipsec-dh-group]**

**Command mode:** config

**Hierarchies**

- network-services ipsec ike-maps global-ike-map

**Parameter table**

+----------------+----------------------------------------------------------------------------------+----------------+---------+
| Parameter      | Description                                                                      | Range          | Default |
+================+==================================================================================+================+=========+
| ipsec-dh-group | Group number for Diffie-Hellman Exponentiation used for the IPSEC SA key         | 0, 2, 5, 14-32 | 31      |
|                | exchange.                                                                        |                |         |
+----------------+----------------------------------------------------------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# ike-maps
    dnRouter(cfg-netsrv-ipsec-ikemaps)# global-ike-map
    dnRouter(cfg-netsrv-ipsec-glbl-ikemap)# ipsec-dh-group 31


**Removing Configuration**

To remove the configuration of the ipsec-dh-group:
::

    dnRouter(cfg-netsrv-ipsec-glbl-ikemap)# no ipsec-dh-group

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
