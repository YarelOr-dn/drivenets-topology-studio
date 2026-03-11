protocols ospf instance area interface delay-normalization offset
-----------------------------------------------------------------

**Minimum user role:** operator

To configure the OSPFv2 delay normalization offset on the interface:


**Command syntax: offset [delay-normalization-offset]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface delay-normalization

**Parameter table**

+----------------------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter                  | Description                                                                      | Range        | Default |
+============================+==================================================================================+==============+=========+
| delay-normalization-offset | The value of the delay normalization offset in microseconds. This value must be  | 0-4294967294 | 0       |
|                            | smaller than the value of normalized interval.                                   |              |         |
+----------------------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area
    dnRouter(cfg-protocols-ospf-area)# interface ge100-0/0/0
    dnRouter(cfg-ospf-area-interface)# delay-normalization
    dnRouter(cfg-area-interface-normalization)# offset 3


**Removing Configuration**

To revert the delay normalization offset configuration to its default value:
::

    dnRouter(cfg-area-interface-normalization)# no offset

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
