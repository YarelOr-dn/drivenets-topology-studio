services ipsec tunnel vrf version
---------------------------------

**Minimum user role:** operator

Set the ike version for the tunnel establishment against the device.

**Command syntax: version [version]**

**Command mode:** config

**Hierarchies**

- services ipsec tunnel vrf

**Parameter table**

+-----------+--------------+---------+---------+
| Parameter | Description  | Range   | Default |
+===========+==============+=========+=========+
| version   | IKE version. | ikev1   | \-      |
|           |              | ikev2   |         |
+-----------+--------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# tunnel 1 vrf MyVrf
    dnRouter(cfg-srv-ipsec-tun)# version ikev2


**Removing Configuration**

To remove the configuration of the ike version:
::

    dnRouter(cfg-srv-ipsec-tun)# no version

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
