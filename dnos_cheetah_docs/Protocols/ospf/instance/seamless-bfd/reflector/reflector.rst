protocols ospf instance seamless-bfd reflector
----------------------------------------------

**Minimum user role:** operator

Provide the seamless BFD reflector that should be advertised by OSPF.

**Command syntax: reflector [reflector-list-to-advertise]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance seamless-bfd

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
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# instance ospf1
    dnRouter(cfg-protocols-ospf-inst)# seamless-bfd
    dnRouter(cfg-ospf-inst-s_bfd)# reflector reflector1
    dnRouter(cfg-inst-s_bfd-reflector)#


**Removing Configuration**

To remove this reflector from being advertised.
::

    dnRouter(cfg-ospf-inst-s_bfd)# no reflector

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
