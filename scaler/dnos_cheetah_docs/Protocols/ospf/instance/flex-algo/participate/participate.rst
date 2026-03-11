protocols ospf instance flex-algo participate
---------------------------------------------

**Minimum user role:** operator

To have the DNOS Router join the Flex-Algo within the OSPF instance, configure the Flex-Algo participation for the desired Flex-Algo identifier:

**Command syntax: participate [Flex-Algo ID]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance flex-algo

**Parameter table**

+--------------+---------------------------+---------+---------+
| Parameter    | Description               | Range   | Default |
+==============+===========================+=========+=========+
| Flex-Algo ID | flex algorithm identifier | 128-255 | \-      |
+--------------+---------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf instance OSPF1
    dnRouter(cfg-protocols-ospf-inst)# flex-algo
    dnRouter(cfg-ospf-inst-flex-algo)# participate 130
    dnRouter(cfg-flex-algo-participate)#


**Removing Configuration**

To remove participation configuration:
::

    dnRouter(cfg-inst-flex-algo)# no participate 130

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
