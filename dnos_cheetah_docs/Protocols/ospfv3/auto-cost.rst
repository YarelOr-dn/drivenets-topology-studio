protocols ospfv3 auto-cost reference-bandwidth
----------------------------------------------

**Minimum user role:** operator

You can set the reference bandwidth for cost calculations, where this bandwidth is considered equivalent to an OSPFv3 cost of 1 (specified in Mbps). The default is 100 Mbps (i.e. a link of bandwidth 100 Mbps or higher will have a cost of 1. Cost of lower bandwidth links will be scaled with reference to this cost. 
To configure the reference bandwidth:

**Command syntax: auto-cost reference-bandwidth [auto-cost-reference-bandwidth]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Parameter table**

+-------------------------------+----------------------------------------------------------------------------------+-----------+---------+
| Parameter                     | Description                                                                      | Range     | Default |
+===============================+==================================================================================+===========+=========+
| auto-cost-reference-bandwidth | This sets the reference bandwidth for cost calculations, where this bandwidth is | 1-4294967 | 100     |
|                               | considered equivalent to an OSPF cost of 1, specified in Mbits/s. The default is |           |         |
|                               | 100Mbit/s (i.e. a link of bandwidth 100Mbit/s or higher will have a cost of 1.   |           |         |
|                               | Cost of lower bandwidth links will be scaled with reference to this cost).       |           |         |
+-------------------------------+----------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# auto-cost reference-bandwidth 100000


**Removing Configuration**

To return the reference bandwidth to its default value: 
::

    dnRouter(cfg-protocols-ospfv3)# no auto-cost reference-bandwidth

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
