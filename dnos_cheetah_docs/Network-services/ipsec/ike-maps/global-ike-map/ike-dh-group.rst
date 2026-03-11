network-services ipsec ike-maps global-ike-map ike-dh-group
-----------------------------------------------------------

**Minimum user role:** operator

Set the ike-dh-group for the tunnel establishment against the device.

**Command syntax: ike-dh-group [ike-dh-group]**

**Command mode:** config

**Hierarchies**

- network-services ipsec ike-maps global-ike-map

**Parameter table**

+--------------+----------------------------------------------------------------------------------+-------------+---------+
| Parameter    | Description                                                                      | Range       | Default |
+==============+==================================================================================+=============+=========+
| ike-dh-group | Group number for Diffie-Hellman Exponentiation used for the IKE SA key exchange. | 2, 5, 14-32 | 31      |
+--------------+----------------------------------------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# ike-maps
    dnRouter(cfg-netsrv-ipsec-ikemaps)# global-ike-map
    dnRouter(cfg-netsrv-ipsec-glbl-ikemap)# ike-dh-group 31


**Removing Configuration**

To remove the configuration of the ike-dh-group:
::

    dnRouter(cfg-netsrv-ipsec-glbl-ikemap)# no ike-dh-group

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
