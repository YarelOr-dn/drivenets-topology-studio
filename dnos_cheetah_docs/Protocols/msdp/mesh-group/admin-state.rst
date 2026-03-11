protocols msdp mesh-group admin-state
-------------------------------------

**Minimum user role:** operator

To administratively enable/disable the MSDP mesh-group, use the following command.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols msdp mesh-group

**Parameter table**

+-------------+--------------------------------------+--------------+---------+
| Parameter   | Description                          | Range        | Default |
+=============+======================================+==============+=========+
| admin-state | Admin Enable/Disable MSDP mesh-group | | enabled    | enabled |
|             |                                      | | disabled   |         |
+-------------+--------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# mesh-group MSDP_Domain_X
    dnRouter(cfg-protocols-msdp-group)# admin-state disabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# mesh-group MSDP_Domain_X
    dnRouter(cfg-protocols-msdp-group)# admin-state enabled


**Removing Configuration**

To revert the admin-state to its default value:
::

    dnRouter(cfg-protocols-msdp-group)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
