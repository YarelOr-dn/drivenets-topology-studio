protocols msdp mesh-group
-------------------------

**Minimum user role:** operator

A mesh-group is a group of MSDP peers. MSDP SA messages received by a peer in the mesh-group are not forwarded to other peers in the group, and by so the number of SA messages are reduced and prevent flooding. You can use this command to define a MSDP mesh-group and enter its configuration. 

**Command syntax: mesh-group [mesh-group]**

**Command mode:** config

**Hierarchies**

- protocols msdp

**Note**
- Peers declared inside a mesh-group, by default will share the same mesh-group configuration

- Mesh group name cannot be all numbers and must contain at least one non-numerical character

- Mesh group peer configurations may differ from the mesh-group configuration.

**Parameter table**

+------------+------------------+-------+---------+
| Parameter  | Description      | Range | Default |
+============+==================+=======+=========+
| mesh-group |  MSDP mesh-group | \-    | \-      |
+------------+------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# mesh-group MSDP_Domain_X
    dnRouter(cfg-protocols-msdp-group)#


**Removing Configuration**

To remove the mesh-group configuration:
::

    dnRouter(cfg-protocols-msdp)# no mesh-group MSDP_Domain_X

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
