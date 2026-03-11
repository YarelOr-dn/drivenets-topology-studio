protocols ospf instance seamless-bfd reflector advertise
--------------------------------------------------------

**Minimum user role:** operator

To enable or disable advertising the Seamless BFD reflector discriminator.

**Command syntax: advertise [advertise]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance seamless-bfd reflector

**Parameter table**

+-----------+-------------------------------------------+--------------+----------+
| Parameter | Description                               | Range        | Default  |
+===========+===========================================+==============+==========+
| advertise | Set to enable to advertise this reflector | | enabled    | disabled |
|           |                                           | | disabled   |          |
+-----------+-------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# instance ospf1
    dnRouter(cfg-protocols-ospf-inst)# seamless-bfd
    dnRouter(cfg-ospf-inst-s_bfd)# reflector reflector1
    dnRouter(cfg-inst-s_bfd-reflector)# advertise enabled
    dnRouter(cfg-inst-s_bfd-reflector)#


**Removing Configuration**

To stop advertising the reflector discriminator.
::

    dnRouter(ccfg-inst-s_bfd-reflector)# no advertise

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
