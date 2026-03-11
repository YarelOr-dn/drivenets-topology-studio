services ipsec tunnel vrf encryption-algorithm
----------------------------------------------

**Minimum user role:** operator

Set the encryption-algorithm for the tunnel establishment against the device.

**Command syntax: encryption-algorithm [encryption-algorithm]**

**Command mode:** config

**Hierarchies**

- services ipsec tunnel vrf

**Parameter table**

+----------------------+-------------------------------------------------+---------------+---------+
| Parameter            | Description                                     | Range         | Default |
+======================+=================================================+===============+=========+
| encryption-algorithm | encryption algorithm type to use in this tunnel | AES-128-CBC   | \-      |
|                      |                                                 | AES-256-CBC   |         |
+----------------------+-------------------------------------------------+---------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# tunnel 1 vrf MyVrf
    dnRouter(cfg-srv-ipsec-tun)# encryption-algorithm AES-128-CBC


**Removing Configuration**

To remove the configuration of the encryption-algorithm:
::

    dnRouter(cfg-srv-ipsec-tun)# no encryption-algorithm

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
