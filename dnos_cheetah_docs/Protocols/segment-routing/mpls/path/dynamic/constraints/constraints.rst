protocols segment-routing mpls path dynamic constraints
-------------------------------------------------------

**Minimum user role:** operator

To enter configuration level of dynamic path constraints:

**Command syntax: constraints**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path dynamic

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# path PATH_1
    dnRouter(cfg-sr-mpls-path)# dynamic
    dnRouter(cfg-mpls-path-dynamic)# constraints
    dnRouter(cfg-path-dynamic-constraints)#


**Removing Configuration**

To revert all dynamic path constraints configurations to default:
::

    dnRouter(cfg-mpls-path-dynamic)# no constraints

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
