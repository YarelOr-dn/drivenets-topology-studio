protocols isis instance seamless-bfd reflector
----------------------------------------------

**Minimum user role:** operator

Provide the seamless BFD Reflector that should be advertised by ISIS

**Command syntax: reflector [reflector-list-to-advertise]**

**Command mode:** config

**Hierarchies**

- protocols isis instance seamless-bfd

**Parameter table**

+-----------------------------+-----------------------+-------+---------+
| Parameter                   | Description           | Range | Default |
+=============================+=======================+=======+=========+
| reflector-list-to-advertise | Name of the reflector | \-    | \-      |
+-----------------------------+-----------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# seamless-bfd
    dnRouter(cfg-isis-inst-s_bfd)# reflector reflector1
    dnRouter(cfg-inst-s_bfd-reflector)#


**Removing Configuration**

To remove this reflector from being advertised.
::

    dnRouter(cfg-isis-inst-s_bfd)# no reflector

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.0    | Command introduced |
+---------+--------------------+
