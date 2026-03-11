network-services ipsec ike-maps ike-map ike-dh-group
----------------------------------------------------

**Minimum user role:** operator

Set the ike-dh-group for the tunnel establishment against the device.

**Command syntax: ike-dh-group [ike-dh-group]**

**Command mode:** config

**Hierarchies**

- network-services ipsec ike-maps ike-map

**Parameter table**

+--------------+----------------------------------------------------------------------------------+-------------+---------+
| Parameter    | Description                                                                      | Range       | Default |
+==============+==================================================================================+=============+=========+
| ike-dh-group | Group number for Diffie-Hellman Exponentiation used for the IKE SA key exchange. | 2, 5, 14-32 | \-      |
+--------------+----------------------------------------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# ike-maps
    dnRouter(cfg-netsrv-ipsec-ikemaps)# ike-map MyIkeMap
    dnRouter(cfg-netsrv-ipsec-ikemaps)# ike-dh-group 31


**Removing Configuration**

To remove the configuration of the ike-dh-group:
::

    dnRouter(cfg-netsrv-ipsec-ikemaps)# no ike-dh-group

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
