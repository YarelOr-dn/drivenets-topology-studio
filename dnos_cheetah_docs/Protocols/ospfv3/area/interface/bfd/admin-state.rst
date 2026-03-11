protocols ospfv3 area interface bfd admin-state
-----------------------------------------------

**Minimum user role:** operator

To set the OSPFv3 BFD admin state for the interface:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 area interface bfd

**Note**
- Per area interface bfd admin-state configuration.
- The 'no'command returns admin-state to its default settings.

**Parameter table**

+-------------+--------------------------------------------------+--------------+---------+
| Parameter   | Description                                      | Range        | Default |
+=============+==================================================+==============+=========+
| admin-state | Sets the OSPF BFD admin state for the interface. | | enabled    | \-      |
|             |                                                  | | disabled   |         |
+-------------+--------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# area 0
    dnRouter(cfg-protocols-ospfv3-area)# interface ge100-1/2/1
    dnRouter(cfg-ospfv3-area-if)# bfd
    dnRouter(cfg-ospfv3-area-if-bfd)# admin-state enabled
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# area 0
    dnRouter(cfg-protocols-ospfv3-area)# interface ge100-1/2/1
    dnRouter(cfg-ospfv3-area-if)# bfd
    dnRouter(cfg-ospfv3-area-if-bfd)# admin-state disabled


**Removing Configuration**

To return the admin-state to its default value: 
::

    dnRouter(cfg-ospfv3-area-if-bfd)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
