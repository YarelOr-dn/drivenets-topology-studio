protocols bfd seamless-bfd remote-map ipv4 address discriminator
----------------------------------------------------------------

**Minimum user role:** operator

Configure the Seamless BFD Reflector pair: IPv4 address of the reflector and its discriminator value. The discriminator value must be globally unique in the network.

**Command syntax: address [reflector-ipv4-address] discriminator [reflector-discriminator]**

**Command mode:** config

**Hierarchies**

- protocols bfd seamless-bfd remote-map ipv4

**Parameter table**

+-------------------------+-----------------------------------------------------+------------------+---------+
| Parameter               | Description                                         | Range            | Default |
+=========================+=====================================================+==================+=========+
| reflector-ipv4-address  | ipv4 address of the remote reflector                | A.B.C.D          | \-      |
+-------------------------+-----------------------------------------------------+------------------+---------+
| reflector-discriminator | Set the Seamless BFD reflector discriminator value. | | 1-4294967295   | \-      |
|                         |                                                     | | A.B.C.D        |         |
+-------------------------+-----------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# seamless-bfd
    dnRouter(cfg-protocols-bfd-seamless)# remote-map
    dnRouter(cfg-bfd-seamless-map)# ipv4
    dnRouter(cfg-seamless-map-ipv4)# address 185.32.98.12 discriminator 658709
    dnRouter(cfg-seamless-map-ipv4)# address 112.46.22.76 discriminator 97123
    dnRouter(cfg-seamless-map-ipv4)#


**Removing Configuration**

To remove the ip address and its discriminator pair
::

    dnRouter(cfg-seamless-map-ipv4)# no address 185.32.98.12

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
