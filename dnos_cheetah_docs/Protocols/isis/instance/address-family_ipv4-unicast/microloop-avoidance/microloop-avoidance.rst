protocols isis instance address-family ipv4-unicast microloop-avoidance
-----------------------------------------------------------------------

**Minimum user role:** operator

Microloops are brief packet loops that occur in the network following a topology change (link down, link up, or metric change events).
Microloops are caused by the non-simultaneous convergence of different nodes in the network.
If nodes converge and send traffic to a neighbor node that has not converged yet, traffic may be looped between these two nodes, resulting in packet loss, jitter, and out-of-order packets.

The Segment Routing Microloop Avoidance feature detects if microloops are possible following a topology change.
If a node computes that a microloop could occur on the new topology, the node creates a loop-free SR-TE path to the destination using a list of segments.
After the FIB update delay timer expires, the SR-TE path is replaced with regular forwarding paths.

To configure microloop-avoidance, enter microloop-avoidance configuration mode:

**Command syntax: microloop-avoidance**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast

**Note**

-  For microloop-avoidance to work, segment-routing must be supported for the given address-family.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# microloop-avoidance
    dnRouter(cfg-inst-afi-uloop)#
    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# microloop-avoidance
    dnRouter(cfg-inst-afi-uloop)#


**Removing Configuration**

To revert all microloop-avoidance configuration to default:
::

    dnRouter(cfg-isis-inst-afi)# no microloop-avoidance

**Command History**

+---------+-------------------------------------------+
| Release | Modification                              |
+=========+===========================================+
| 16.3    | Command introduced                        |
+---------+-------------------------------------------+
