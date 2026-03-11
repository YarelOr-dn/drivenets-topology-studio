network-services ipsec ike-maps ike-map version
-----------------------------------------------

**Minimum user role:** operator

Set the ike version for the tunnel establishment against the device.

**Command syntax: version [version]**

**Command mode:** config

**Hierarchies**

- network-services ipsec ike-maps ike-map

**Parameter table**

+-----------+--------------+-----------+---------+
| Parameter | Description  | Range     | Default |
+===========+==============+===========+=========+
| version   | IKE version. | | ikev1   | \-      |
|           |              | | ikev2   |         |
+-----------+--------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# ike-maps
    dnRouter(cfg-netsrv-ipsec-ikemaps)# ike-map MyIkeMap
    dnRouter(cfg-netsrv-ipsec-ikemaps)# version ikev2


**Removing Configuration**

To remove the configuration of the ike version:
::

    dnRouter(cfg-netsrv-ipsec-ikemaps)# no version

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
