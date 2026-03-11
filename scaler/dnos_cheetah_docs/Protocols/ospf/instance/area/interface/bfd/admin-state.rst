protocols ospf instance area interface bfd admin-state
------------------------------------------------------

**Minimum user role:** operator

To set the OSPF BFD admin state for the interface:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface bfd

**Note**
- Per area interface bfd admin-state configuration
- 'no'command returns admin-state to its default settings

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
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# interface ge100-1/2/1
    dnRouter(cfg-ospf-area-if)# bfd
    dnRouter(cfg-ospf-area-if-bfd)# admin-state enabled
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# interface ge100-1/2/1
    dnRouter(cfg-ospf-area-if)# bfd
    dnRouter(cfg-ospf-area-if-bfd)# admin-state disabled


**Removing Configuration**

To return the admin-state to its default value: 
::

    dnRouter(cfg-ospf-area-if-bfd)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
