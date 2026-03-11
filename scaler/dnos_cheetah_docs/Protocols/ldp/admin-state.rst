protocols ldp admin-state
-------------------------

**Minimum user role:** operator

Setting the LDP protocol to disable mode. LDP will not send or receive LDP packets.

To set the LDP protocol to disable mode:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ldp

**Parameter table**

+-------------+------------------------------------+--------------+---------+
| Parameter   | Description                        | Range        | Default |
+=============+====================================+==============+=========+
| admin-state | Administratively set the LDP state | | enabled    | enabled |
|             |                                    | | disabled   |         |
+-------------+------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ldp
    dnRouter(cfg-protocols-ldp)# admin-state disabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-ldp)# no admin-state disabled

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
