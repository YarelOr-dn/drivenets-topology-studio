protocols isis instance seamless-bfd reflector advertise
--------------------------------------------------------

**Minimum user role:** operator

To enable or disable advertising the Seamless BFD Reflector Discriminator

**Command syntax: advertise [advertise]**

**Command mode:** config

**Hierarchies**

- protocols isis instance seamless-bfd reflector

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
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# seamless-bfd
    dnRouter(cfg-isis-inst-s_bfd)# reflector reflector1
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
| 19.0    | Command introduced |
+---------+--------------------+
