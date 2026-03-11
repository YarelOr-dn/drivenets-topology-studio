protocols isis instance flex-algo
---------------------------------

**Minimum user role:** operator

Flex-Algo allows IGP constraint-based computation and creates separate IGP algorithms according to the defined set of constraints and metric types.
It compliments the SR-TE solution by adding new prefix segments with specific optimization objectives and constraints. 
* Metric types: Minimize IGP-metric, te-metric, or delay. 
* Exclude certain SRLGs, include/exclude link admin groups. 
To have the DNOS Router join Flex-Algo within the IS-IS instance, configure the Flex-Algo participation.

To configure the flexible algorithm, enter the Flex-Algo configuration mode:

**Command syntax: flex-algo**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Note**

- Flex-Algo routes are ISIS-SR routes with matching IS-IS segment-routing administrative-distance.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# flex-algo
    dnRouter(cfg-inst-sr-flex-algo)#


**Removing Configuration**

To revert all flex-algo configurations to default:
::

    dnRouter(cfg-isis-inst-sr)# no segment-routing flex-algo

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
