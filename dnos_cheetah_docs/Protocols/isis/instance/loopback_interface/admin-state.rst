protocols isis instance interface admin-state
---------------------------------------------

**Minimum user role:** operator

Setting an IS-IS interface to disable mode. The IS-IS interface will not send or receive IS-IS packets.

To set the IS-IS interface to disable mode:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface

**Parameter table**

+-------------+------------------------------------------------+--------------+---------+
| Parameter   | Description                                    | Range        | Default |
+=============+================================================+==============+=========+
| admin-state | Administratively set the IS-IS interface state | | enabled    | enabled |
|             |                                                | | disabled   |         |
+-------------+------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# admin-state disabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-isis-inst-if)# no admin-state disabled

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
