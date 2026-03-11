protocols isis instance flex-algo participate
---------------------------------------------

**Minimum user role:** operator

To have the DNOS Router join the Flex-Algo within the IS-IS instance, configure the Flex-Algo participation for the desired Flex-Algo identifier:

**Command syntax: participate [Flex-Algo ID]**

**Command mode:** config

**Hierarchies**

- protocols isis instance flex-algo

**Parameter table**

+--------------+---------------------------+---------+---------+
| Parameter    | Description               | Range   | Default |
+==============+===========================+=========+=========+
| Flex-Algo ID | flex algorithm identifier | 128-255 | \-      |
+--------------+---------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# flex-algo
    dnRouter(cfg-isis-inst-flex-algo)# participate 130
    dnRouter(cfg-flex-algo-participate)#


**Removing Configuration**

To remove participation configuration:
::

    dnRouter(cfg-inst-flex-algo)# no participate 130

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
