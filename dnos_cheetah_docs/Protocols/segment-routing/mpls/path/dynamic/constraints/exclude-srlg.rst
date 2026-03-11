protocols segment-routing mpls path dynamic constraints exclude-srlg
--------------------------------------------------------------------

**Minimum user role:** operator

A link is not valid for to be used in dynamic path if the link has any srlg value that matches the exclude-srlg values. The srlg value is per RFC5307.
To configure a exclude-srlg constraint:

**Command syntax: exclude-srlg [srlg-value]** [, srlg-value, srlg-value]

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path dynamic constraints

**Parameter table**

+------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter  | Description                                                                      | Range        | Default |
+============+==================================================================================+==============+=========+
| srlg-value | link is prun if link has any srlg value that match the exclude-srlg values. srlg | 1-4294967295 | \-      |
|            | value per RFC5307                                                                |              |         |
+------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# path PATH_1
    dnRouter(cfg-sr-mpls-path)# dynamic
    dnRouter(cfg-mpls-path-dynamic)# constraints
    dnRouter(cfg-path-dynamic-constraints)# exclude-srlg 2,50


**Removing Configuration**

To remove a specific exclude-srlg configuration:
::

     dnRouter(cfg-path-dynamic-constraints)# no exclude-srlg 50

To remove all exclude-srlg configuration:
::

     dnRouter(cfg-path-dynamic-constraints)# no exclude-srlg

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
