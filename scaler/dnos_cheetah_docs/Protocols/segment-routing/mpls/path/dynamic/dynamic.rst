protocols segment-routing mpls path dynamic
-------------------------------------------

**Minimum user role:** operator

With a dynamic path, DNOS will calculate an SR-TE path that matches the set of constraints desired by the user.
A dynmaic path is calculated towards the SR-TE policy destination and may include multiple segment-lists.
The dynamic path may be a fully strict hop by hop adjacency list, or a minimized SID list leveraging LSR node-sid forwarding.
To enter a dynamic path configuration level:


**Command syntax: dynamic**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# path PATH_1
    dnRouter(cfg-sr-mpls-path)# dynamic
    dnRouter(cfg-mpls-path-dynamic)#


**Removing Configuration**

To revert all dynamic path configurations to default:
::

    dnRouter(cfg-sr-mpls-path)# no dynamic

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
