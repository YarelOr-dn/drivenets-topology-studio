protocols segment-routing mpls path dynamic constraints algorithm
-----------------------------------------------------------------

**Minimum user role:** operator

A dynamic path is calculated over a given topology. Operator can control over which flex-algo algorithm topology path will be calculated.
When path is calculated over a non algo 0 topology, SID usage for path label stack will match SIDs valid in that topology only, with exception of adjacency-sid usage.
To set desired algorithm:

**Command syntax: algorithm [srlg-value]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path dynamic constraints

**Note**

- Default algorithm to use is per policy configured destination sid algorithm

- When algorithm is configured for dynamic path, the Segement-Routing destination algorithm is ignored in path construction and only destination address is taken in to account

**Parameter table**

+------------+--------------------------------------------------------------+--------------+---------+
| Parameter  | Description                                                  | Range        | Default |
+============+==============================================================+==============+=========+
| srlg-value | topology algorithm overwhich dynamic path will be calculated | 0-1, 128-255 | \-      |
+------------+--------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# path PATH_1
    dnRouter(cfg-sr-mpls-path)# dynamic
    dnRouter(cfg-mpls-path-dynamic)# constraints
    dnRouter(cfg-path-dynamic-constraints)# algorithm 128


**Removing Configuration**

To remove a algorithm configuration:
::

     dnRouter(cfg-path-dynamic-constraints)# no algorithm

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
