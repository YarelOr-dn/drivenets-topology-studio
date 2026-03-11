services ipsec tunnel vrf secret
--------------------------------

**Minimum user role:** operator

Set the PSK for the device connecting to the ipsec gateway.

**Command syntax: secret [secret]**

**Command mode:** config

**Hierarchies**

- services ipsec tunnel vrf

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
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# tunnel 1 vrf MyVrf
    dnRouter(cfg-srv-ipsec-tun)# secret MySecret


**Removing Configuration**

To remove the configuration of the secret:
::

    dnRouter(cfg-srv-ipsec-tun)# no secret

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
