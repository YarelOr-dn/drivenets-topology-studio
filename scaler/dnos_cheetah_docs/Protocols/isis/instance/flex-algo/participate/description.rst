protocols isis instance flex-algo participate description
---------------------------------------------------------

**Minimum user role:** operator

When configuring multiple IS-IS Flex-Algo participations, it may be helpful to add a description for each participation.

To configure a description for the IS-IS Flex-Algo:


**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- protocols isis instance flex-algo participate

**Parameter table**

+-------------+----------------------------------------------+-------+---------+
| Parameter   | Description                                  | Range | Default |
+=============+==============================================+=======+=========+
| description | Add a description for the IS-IS flex-algo.   | \-    | \-      |
+-------------+----------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# flex-algo
    dnRouter(cfg-isis-inst-flex-algo)# participate 130
    dnRouter(cfg-flex-algo-participate)# description "Min Delay Flex-Algo"


**Removing Configuration**

To remove the description:
::

    dnRouter(cfg-flex-algo-participate)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
