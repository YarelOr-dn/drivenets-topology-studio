protocols isis instance admin-state
-----------------------------------

**Minimum user role:** operator

Setting an IS-IS instance to disable mode. The IS-IS instance will not send or receive IS-IS packets.

To set the IS-IS instance disable mode:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Parameter table**

+-------------+--------------------------------------+--------------+---------+
| Parameter   | Description                          | Range        | Default |
+=============+======================================+==============+=========+
| admin-state | Administratively set the IS-IS state | | enabled    | enabled |
|             |                                      | | disabled   |         |
+-------------+--------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# admin-state disabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-isis-inst)# no admin-state disabled

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
