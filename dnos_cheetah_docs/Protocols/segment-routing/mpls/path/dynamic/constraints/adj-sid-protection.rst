protocols segment-routing mpls path dynamic constraints adj-sid-protection
--------------------------------------------------------------------------

**Minimum user role:** operator

When a dynamic calculated path require to use adjacency-sid over the label stack for a given link hop, there may be multiple possible adj-sid possbile differs by protection entitlement.
To configure adjacency sid protection preference:

**Command syntax: adj-sid-protection [srlg-value]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path dynamic constraints

**Note**

- By default prefer adjacency-sids that are eligable for protection

**Parameter table**

+------------+--------------------------------------------+---------------------------+---------+
| Parameter  | Description                                | Range                     | Default |
+============+============================================+===========================+=========+
| srlg-value | adjacency sid protection preference config | | desired                 | desired |
|            |                                            | | mandatory               |         |
|            |                                            | | unprotected-desired     |         |
|            |                                            | | unprotected-mandatory   |         |
+------------+--------------------------------------------+---------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# path PATH_1
    dnRouter(cfg-sr-mpls-path)# dynamic
    dnRouter(cfg-mpls-path-dynamic)# constraints
    dnRouter(cfg-path-dynamic-constraints)# adj-sid-protection mandatory


**Removing Configuration**

To revert adj-sid-protection to default value:
::

     dnRouter(cfg-path-dynamic-constraints)# no adj-sid-protection

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
