protocols ospf instance microloop-avoidance
-------------------------------------------

**Minimum user role:** operator

Microloops are brief packet loops that occur in the network following a topology change (link down, link up, or metric change events).
Microloops are caused by the non-simultaneous convergence of different nodes in the network.
If the nodes have converge and send traffic to a neighbor node that does not have converged yet, traffic may be looped between these two nodes, resulting in packet loss, jitter, and out-of-order packets.

The Segment Routing Microloop Avoidance feature detects if microloops are possible following a topology change.
If a node computes that a microloop could occur on the new topology, the node creates a loop-free SR-TE path to the destination using a list of segments.
After the FIB update delay timer expires, the SR-TE path is replaced with regular forwarding paths.

To configure microloop-avoidance, enter microloop-avoidance configuration mode:

**Command syntax: microloop-avoidance**

**Command mode:** config

**Hierarchies**

- protocols ospf instance

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# instance INSTANCE_1
    dnRouter(cfg-protocols-ospf-inst)# microloop-avoidance
    dnRouter(cfg-ospf-inst-uloop)#


**Removing Configuration**

To revert all microloop-avoidance configuration to the default value:
::

    dnRouter(cfg-protocols-ospf-inst)# no microloop-avoidance

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
