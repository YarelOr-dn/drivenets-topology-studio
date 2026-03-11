protocols ospf instance ti-fast-reroute
---------------------------------------

**Minimum user role:** operator

Topology-Independent Loop-Free-Alternate can be used to construct alternate paths using Segment-Routing lsps to provide sub 50msec fast reroute recovery.
With TI-LFA a per-prefix alternate path will be created.
The alternate path may utilize usage of SR labels to construct a specific SR lsp to forward the packet to the desired merge-point with the goal of using the post-convergence path.
By doing so, an alternate path can be provided for any required topology.
To configure ti-lfa, enter ti-lfa configuration mode:

**Command syntax: ti-fast-reroute**

**Command mode:** config

**Hierarchies**

- protocols ospf instance

**Note**

- For ti-fast-reroute to work, segment-routing must be enabled.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# ti-fast-reroute
    dnRouter(cfg-protocols-ospf-ti-frr)#


**Removing Configuration**

To revert all ti-fast-reroute configuration to the default value:
::

    dnRouter(cfg-protocols-ospf)# no ti-fast-reroute

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
