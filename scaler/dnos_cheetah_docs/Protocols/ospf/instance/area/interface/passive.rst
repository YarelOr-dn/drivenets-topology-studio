protocols ospf instance area interface passive
----------------------------------------------

**Minimum user role:** operator

Setting an OSPF interface as passive disables the sending of routing updates on that interface, hence adjacencies will not be formed in OSPF. However, the particular subnet will continue to be advertised to other interfaces.
To set the interface to passive mode:

**Command syntax: passive [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface

**Note**

- No command returns passive to its default disabled state.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Suppress routing updates on interface, thus disables the sending of routing      | | enabled    | disabled |
|             | updates on that interface                                                        | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# interface ge100-1/2/1
    dnRouter(cfg-ospf-area-if)# passive enabled


**Removing Configuration**

To return the passive mode admin-state to its default value:
::

    dnRouter(cfg-protocols-ospf-area)# interface ge100-2/1/1

::

    dnRouter(cfg-ospf-area-if)# no passive

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
