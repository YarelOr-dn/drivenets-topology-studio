system network-resources resource admin-state
---------------------------------------------

**Minimum user role:** operator

Set the admin-state of the resource:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system network-resources resource

**Parameter table**

+-------------+-----------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                     | Range        | Default  |
+=============+=================================================================+==============+==========+
| admin-state | Desired administrative state of the network-function (resource) | | enabled    | disabled |
|             |                                                                 | | disabled   |          |
+-------------+-----------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# network-resources
    dnRouter(cfg-system-netres)# resource nat-resource-1
    dnRouter(cfg-system-netres-res)# admin-state disabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-system-netres-res)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
