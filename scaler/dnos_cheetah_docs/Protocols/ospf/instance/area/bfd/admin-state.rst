protocols ospf instance area bfd admin-state
--------------------------------------------

**Minimum user role:** operator

To set the OSPF BFD admin state for the interface:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area bfd

**Note**
- Per area interface bfd admin-state configuration
- 'no'command returns admin-state to its default settings

**Parameter table**

+-------------+--------------------------------------+--------------+----------+
| Parameter   | Description                          | Range        | Default  |
+=============+======================================+==============+==========+
| admin-state | set whether bfd protection is in use | | enabled    | disabled |
|             |                                      | | disabled   |          |
+-------------+--------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-ospf-area)# bfd
    dnRouter(cfg-ospf-area-bfd)# admin-state enabled
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-ospf-area)# bfd
    dnRouter(cfg-ospf-area-bfd)# admin-state disabled


**Removing Configuration**

To return the admin-state to its default value: 
::

    dnRouter(cfg-ospf-area-bfd)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
