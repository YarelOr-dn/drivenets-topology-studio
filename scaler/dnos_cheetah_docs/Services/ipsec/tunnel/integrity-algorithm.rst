services ipsec tunnel vrf integrity-algorithm
---------------------------------------------

**Minimum user role:** operator

Set the integrity-algorithm for the tunnel establishment against the device.

**Command syntax: integrity-algorithm [integrity-algorithm]**

**Command mode:** config

**Hierarchies**

- services ipsec tunnel vrf

**Parameter table**

+---------------------+-------------------------------------------------+------------+---------+
| Parameter           | Description                                     | Range      | Default |
+=====================+=================================================+============+=========+
| integrity-algorithm | encryption algorithm type to use in this tunnel | SHA2-256   | \-      |
|                     |                                                 | SHA1       |         |
+---------------------+-------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# tunnel 1 vrf MyVrf
    dnRouter(cfg-srv-ipsec-tun)# integrity-algorithm SHA2-256


**Removing Configuration**

To remove the configuration of the integrity-algorithm:
::

    dnRouter(cfg-srv-ipsec-tun)# no integrity-algorithm

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
