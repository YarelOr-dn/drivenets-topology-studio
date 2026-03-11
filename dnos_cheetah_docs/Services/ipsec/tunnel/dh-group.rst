services ipsec tunnel vrf dh-group
----------------------------------

**Minimum user role:** operator

Set the dh-group for the tunnel establishment against the device.

**Command syntax: dh-group [dh-group]**

**Command mode:** config

**Hierarchies**

- services ipsec tunnel vrf

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------------+---------+
| Parameter | Description                                                                      | Range         | Default |
+===========+==================================================================================+===============+=========+
| dh-group  | Group number for Diffie-Hellman Exponentiation used during IKE_SA_INIT for the   | 1-2, 5, 14-32 | \-      |
|           | IKE SA key exchange.                                                             |               |         |
+-----------+----------------------------------------------------------------------------------+---------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# tunnel 1 vrf MyVrf
    dnRouter(cfg-srv-ipsec-tun)# dh-group 31


**Removing Configuration**

To remove the configuration of the dh-group:
::

    dnRouter(cfg-srv-ipsec-tun)# no dh-group

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
