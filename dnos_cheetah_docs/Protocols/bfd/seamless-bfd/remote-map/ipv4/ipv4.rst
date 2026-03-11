protocols bfd seamless-bfd remote-map ipv4
------------------------------------------

**Minimum user role:** operator

Configure an iIPv4 remote seamless BFD Reflector map to associate the discriminator with the IPv4-Address.

**Command syntax: ipv4**

**Command mode:** config

**Hierarchies**

- protocols bfd seamless-bfd remote-map

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# seamless-bfd
    dnRouter(cfg-protocols-bfd-seamless)# remote-map
    dnRouter(cfg-bfd-seamless-map)# ipv4
    dnRouter(cfg-seamless-map-ipv4)#


**Removing Configuration**

To remove the ipv4 remote-map from the system.
::

    dnRouter(cfg-bfd-seamless-map)# no ipv4

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
