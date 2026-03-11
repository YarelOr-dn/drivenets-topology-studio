protocols pim nsr
-----------------

**Minimum user role:** operator

You can use this command to enable PIM non-stop-routing. To enable or disable PIM NSR:

**Command syntax: nsr [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols pim

**Note**

- By default, PIM NSR is enabled.

**Parameter table**

+-------------+-------------------------+--------------+---------+
| Parameter   | Description             | Range        | Default |
+=============+=========================+==============+=========+
| admin-state | The PIM NSR admin state | | enabled    | enabled |
|             |                         | | disabled   |         |
+-------------+-------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# nsr enabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# nsr disabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim


**Removing Configuration**

To revert PIM NSR to the default value:
::

    dnRouter(cfg-protocols-pim)# no nsr

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
