protocols bfd seamless-bfd remote-map
-------------------------------------

**Minimum user role:** operator

Configure a remote seamless BFD Reflector map to associate the Discriminator with the IP-Address.

**Command syntax: remote-map**

**Command mode:** config

**Hierarchies**

- protocols bfd seamless-bfd

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# seamless-bfd
    dnRouter(cfg-protocols-bfd-seamless)# remote-map
    dnRouter(cfg-bfd-seamless-map)#


**Removing Configuration**

To remove the remote-map from the system.
::

    dnRouter(cfg-protocols-bfd-seamless)# no remote-map

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
