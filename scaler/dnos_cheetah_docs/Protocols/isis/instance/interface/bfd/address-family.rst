protocols isis instance interface bfd address-family
----------------------------------------------------

**Minimum user role:** operator

By default, a BFD session is established to the interface IP address in the neighbor hello packets, for both IPv4 and IPv6 sessions. When a specific address-family is configured, a BFD session will be establish for that address-family only. BFD protection is per address family, i.e a BFD session down event will update connectivity for the relevant address family topology only.

To configure BFD protection a specific address family:

**Command syntax: address-family [address-family]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface bfd

**Parameter table**

+----------------+----------------------------------------------------------------------------------+---------------+-----------+
| Parameter      | Description                                                                      | Range         | Default   |
+================+==================================================================================+===============+===========+
| address-family | The address-family for which to set BFD protection.                              | | ipv4        | ipv4-ipv6 |
|                | A BFD session will be established for this address family only and a BFD session | | ipv6        |           |
|                | down event will update connectivity for the relevant address family topology     | | ipv4-ipv6   |           |
|                | only.                                                                            |               |           |
+----------------+----------------------------------------------------------------------------------+---------------+-----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# isis-level level-1-2
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# bfd
    dnRouter(cfg-inst-if-bfd)# address-family ipv4


**Removing Configuration**

To revert all BFD configuration to their default values:
::

    dnRouter(cfg-inst-if-bfd)# no address-family

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
