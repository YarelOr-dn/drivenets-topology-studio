protocols ospf instance flex-algo participate description
---------------------------------------------------------

**Minimum user role:** operator

When configuring multiple OSPF Flex-Algo participations, it may be helpful to add a description for each participation.

To configure a description for the OSPF Flex-Algo:


**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance flex-algo participate

**Parameter table**

+-------------+---------------------------------------------+-------+---------+
| Parameter   | Description                                 | Range | Default |
+=============+=============================================+=======+=========+
| description | Add a description for the OSPF flex-algo.   | \-    | \-      |
+-------------+---------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# instance OSPF1
    dnRouter(cfg-protocols-ospf-inst)# flex-algo
    dnRouter(cfg-ospf-inst-flex-algo)# participate 130
    dnRouter(cfg-flex-algo-participate)# description "Min Delay Flex-Algo"


**Removing Configuration**

To remove the description:
::

    dnRouter(cfg-flex-algo-participate)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
