protocols msdp mesh-group peer admin-state
------------------------------------------

**Minimum user role:** operator

Use the following command to administratively enable/disable the MSDP mesh-group peer:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols msdp mesh-group peer

**Note**

- By default the peer's admin-state is inherited from the mesh-group admin-state configuration, unless it is explicitly configured for the peer.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| admin-state | Administrative enabling / disabling of the connection with the MSDP mesh-group   | | enabled    | \-      |
|             | peer                                                                             | | disabled   |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# mesh-group MSDP_Domain_X
    dnRouter(cfg-protocols-msdp-group)# peer 2.3.4.5
    dnRouter(cfg-protocols-msdp-group-peer)# admin-state disabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# mesh-group MSDP_Domain_X
    dnRouter(cfg-protocols-msdp-group)# peer 2.3.4.5
    dnRouter(cfg-protocols-msdp-group-peer)# admin-state enabled


**Removing Configuration**

To revert the admin-state to its default value:
::

    dnRouter(cfg-protocols-msdp-group-peer)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
