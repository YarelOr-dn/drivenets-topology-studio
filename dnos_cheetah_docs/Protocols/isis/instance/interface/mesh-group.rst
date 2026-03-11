protocols isis instance interface mesh-group
--------------------------------------------

**Minimum user role:** operator

This command allows you to set the mesh-group behavior on an interface.
When set to *blocked*, all LSPs including flooded and self-originated will not be sent over the interface.
When set to *mesh-id*, an LSP received on an interface that matches the same mesh-id within the IS-IS instance will not be flooded over this interface.
To configure the mesh-group behavior for the interface:

**Command syntax: mesh-group [mesh-id]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface

**Parameter table**

+-----------+---------------------------------------+----------------------+---------+
| Parameter | Description                           | Range                | Default |
+===========+=======================================+======================+=========+
| mesh-id   | The mesh-id within the IS-IS instance | 0-4294967295/blocked | \-      |
+-----------+---------------------------------------+----------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# mesh-group blocked

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-1
    dnRouter(cfg-isis-inst-if)# mesh-group 5


**Removing Configuration**

To remove the mesh-group setting:
::

    dnRouter(cfg-isis-inst-if)# no mesh-group

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
