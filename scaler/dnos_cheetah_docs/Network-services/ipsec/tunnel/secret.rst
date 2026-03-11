network-services ipsec tunnel secret
------------------------------------

**Minimum user role:** operator

Set the PSK for the device connecting to the ipsec gateway.

**Command syntax: secret [secret]**

**Command mode:** config

**Hierarchies**

- network-services ipsec tunnel

**Parameter table**

+-----------+-------------------------+-------+---------+
| Parameter | Description             | Range | Default |
+===========+=========================+=======+=========+
| secret    | Pre-shared secret value | \-    | \-      |
+-----------+-------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-netsrv)# ipsec
    dnRouter(cfg-netsrv-ipsec)# tunnel 1
    dnRouter(cfg-netsrv-ipsec-tun)# secret MySecret


**Removing Configuration**

To remove the configuration of the secret:
::

    dnRouter(cfg-netsrv-ipsec-tun)# no secret

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
