protocols ospf instance flex-algo
---------------------------------

**Minimum user role:** operator

Flex-Algo allows IGP constraint-based computation and creates separate IGP algorithms according to the defined set of constraints and metric types.
It compliments the SR-TE solution by adding new prefix segments with specific optimization objectives and constraints.
* Metric types: Minimize IGP-metric, te-metric, or delay.
* Exclude certain SRLGs, include/exclude link admin groups.
To have the DNOS Router join Flex-Algo within the OSPF instance, configure the Flex-Algo participation.

To configure the flexible algorithm, enter the Flex-Algo configuration mode:

**Command syntax: flex-algo**

**Command mode:** config

**Hierarchies**

- protocols ospf instance

**Note**

- Flex-Algo routes are OSPF routes with matching OSPF segment-routing administrative-distance.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf <instance name>
    dnRouter(cfg-protocols-ospf-inst)# flex-algo
    dnRouter(cfg-ospf-inst-flex-algo)#


**Removing Configuration**

To revert all flex-algo configurations to default:
::

    dnRouter(cfg-protocols-ospf-inst)# no flex-algo

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
