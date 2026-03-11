protocols bfd seamless-bfd reflector source-address-ipv4
--------------------------------------------------------

**Minimum user role:** operator

To set the IPv4 address of the Reflector that is sent in the response message. If not set the SR-TE policy router-ID is sent as the Source IP address.

**Command syntax: source-address-ipv4 [source-address-ipv4]**

**Command mode:** config

**Hierarchies**

- protocols bfd seamless-bfd reflector

**Parameter table**

+---------------------+--------------------------------------------------------------+---------+---------+
| Parameter           | Description                                                  | Range   | Default |
+=====================+==============================================================+=========+=========+
| source-address-ipv4 | The source IP address to be inserted in the reflected packet | A.B.C.D | \-      |
+---------------------+--------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# seamless-bfd
    dnRouter(cfg-protocols-bfd-seamless)# reflector reflector1
    dnRouter(cfg-bfd-seamless-reflector)# source-address-ipv4 189.91.10.32
    dnRouter(cfg-bfd-seamless-reflector)#


**Removing Configuration**

To remove the source-address-ipv4 configuration
::

    dnRouter(cfg-bfd-seamless-reflector)# no source-address-ipv4

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
