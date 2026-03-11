protocols isis instance address-family ipv4-unicast ti-fast-reroute
-------------------------------------------------------------------

**Minimum user role:** operator

Topology-Independent Loop-Free-Alternate can be used to construct alternate paths using Segment-Routing lsps to provide sub 50msec fast reroute recovery. 
With TI-LFA it will create a per-prefix alternate path. 
The alternate path may utilize usage of SR labels to construct a specific SR LSP to forward the packet to the desired merge-point with the goal of using the post-convergence path. 
By doing so, an alternate path can be provided for any required topology. 

To configure ti-lfa, enter the ti-lfa configuration mode:

**Command syntax: ti-fast-reroute**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast

**Note**

- ti-fast-reroute cannot be enabled if isis fast-reroute is enabled for the same address-family and level.

- For ti-fast-reroute to work, segment-routing must be supported for the given address-family.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)#
    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)#


**Removing Configuration**

To revert all ti-fast-reroute configuration to default:
::

    dnRouter(cfg-isis-inst-afi)# no ti-fast-reroute

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
