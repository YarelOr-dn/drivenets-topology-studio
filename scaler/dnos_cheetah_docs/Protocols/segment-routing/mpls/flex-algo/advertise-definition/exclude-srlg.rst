protocols segment-routing mpls flex-algo advertise-definition exclude-srlg
--------------------------------------------------------------------------

**Minimum user role:** operator

A link is pruned if the link has any srlg value that matches the exclude-srlg values. The srlg value is per RFC5307.
To configure an exclude-srlg constraint:

**Command syntax: exclude-srlg [srlg-value]** [, srlg-value, srlg-value]

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls flex-algo advertise-definition

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
    dnRouter(cfg-protocols-sr-mpls)# flex-algo
    dnRouter(cfg-sr-mpls-flex-algo)# advertise-definition MIN_DELAY_130
    dnRouter(cfg-mpls-flex-algo-fad)# exclude-srlg 2,50


**Removing Configuration**

To remove a specific exclude-srlg configuration:
::

    dnRouter(cfg-mpls-flex-algo-fad)# no exclude-srlg 50

To remove all exclude-srlg configuration:
::

    dnRouter(cfg-mpls-flex-algo-fad)# no exclude-srlg

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
