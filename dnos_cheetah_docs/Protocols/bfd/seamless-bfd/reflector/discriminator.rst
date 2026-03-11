protocols bfd seamless-bfd reflector local-discriminator
--------------------------------------------------------

**Minimum user role:** operator

Configure the Seamless BFD Reflector Discriminator value. This value must be globally unique in the network.

**Command syntax: local-discriminator [local-discriminator]**

**Command mode:** config

**Hierarchies**

- protocols bfd seamless-bfd reflector

**Parameter table**

+---------------------+-----------------------------------------------------+------------------+---------+
| Parameter           | Description                                         | Range            | Default |
+=====================+=====================================================+==================+=========+
| local-discriminator | Set the Seamless BFD reflector discriminator value. | | 1-4294967295   | \-      |
|                     |                                                     | | A.B.C.D        |         |
+---------------------+-----------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# seamless-bfd
    dnRouter(cfg-protocols-bfd-seamless)# reflector reflector1
    dnRouter(cfg-bfd-seamless-reflector)# local-discriminator 658709
    dnRouter(cfg-bfd-seamless-reflector)#


**Removing Configuration**

To remove the discriminator configuration
::

    dnRouter(cfg-bfd-seamless-reflector)# no local-discriminator

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
