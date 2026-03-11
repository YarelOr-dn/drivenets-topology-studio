protocols segment-routing mpls flex-algo
----------------------------------------

**Minimum user role:** operator

Flex-Algo allows IGP constraint-based computation and creates separate IGP algorithms according to the defined set of constraints and metric types.
It compliments the SR-TE solution by adding new prefix segments with specific optimization objectives and constraints. 
- Metric types: Minimize IGP-metric, te-metric, or delay. 
- Exclude certain SRLGs, include/exclude link admin groups. 

Flex-Algo allows calculating constrained-based network paths, with no SR policies, and no TE tunnels.
- Outgoing packets aren’t comprised of multiple transport labels as in SR policies – the label stack is minimal, while a constraint path is used. Each PE in a certain Flex-Algo topology can send traffic to each PE using a single transport label.
- No need for SR Policy per destination – each node participating in the required Flex-Algo is a destination potential PE, and is applicable to be reached by all other PEs of that specific Flex-Algo.
- Simplicity, automation – automated steering, ODN steering according to color, TI-LFA per Flex-Algo, etc.

By default, an IGP uses the Algorithm 0 - Shortest Path First (SPF). 

To configure the flexible algorithm, enter the Flex-Algo configuration mode:

**Command syntax: flex-algo**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls

**Note**

- Enabling participant in flex-algorithm topology is under ISIS/OSPF protocol configuration

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# flex-algo
    dnRouter(cfg-sr-mpls-flex-algo)#


**Removing Configuration**

To revert all flex-algo configurations to default:
::

    dnRouter(cfg-protocols-sr-mpls)# no flex-algo

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
