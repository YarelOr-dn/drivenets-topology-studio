protocols segment-routing mpls path dynamic maximum-segment-lists
-----------------------------------------------------------------

**Minimum user role:** operator

Multiple different equal cost paths can be found, as a result of dynamic path calculations.
To choose how many paths to install for forwarding:


**Command syntax: maximum-segment-lists [maximum-segment-lists]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path dynamic

**Note**

- Multiple paths are defined by path differences of label-stack and/or nexthop.

- When stack compression is used, downstream forwarding ECMP may be achieved by transit LSR leveraging Node/Anycast-SID forwarding.

- All paths found that match the desired constraints and optimization requirement (such as min delay) will be considered equal cost for an ECMP selection (even when margin is used). As such, there is no preference in the RIB path selection if more paths are found in comparison with the allowed maximum-path.

**Parameter table**

+-----------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter             | Description                                                                      | Range | Default |
+=======================+==================================================================================+=======+=========+
| maximum-segment-lists | Number of Policy path segment-list ECMP to be installed to rib as result of      | 1-8   | 8       |
|                       | dynamic path calculations                                                        |       |         |
+-----------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# path PATH_1
    dnRouter(cfg-sr-mpls-path)# dynamic
    dnRouter(cfg-mpls-path-dynamic)# maximum-segment-lists 1


**Removing Configuration**

To return maximum-segment-lists to default value:
::

    dnRouter(cfg-mpls-path-dynamic)# no maximum-segment-lists

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
