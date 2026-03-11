protocols isis
--------------

**Minimum user role:** operator

The IS-IS routing protocol is a link-state Interior Gateway Protocol (IGP) providing fast convergence, better stability, and more efficient use of bandwidth, memory, and CPU resources. Like other link-state protocols, IS-IS propagates the information required to build a complete network connectivity map on each participating device. This map is then used to calculate the shortest path to destinations.

In large IS-IS domains, scaling the number of nodes and links can become a limiting factor due to the LSP database's increased size. Splitting the IS-IS domain into levels is an efficient scaling method. Level 1/2 functionality supports route leaking and propagation between the different levels and summarization on level boundaries. DNOS supports pure L2 and L1/L2 border nodes.

To enter the IS-IS global configuration level:

**Command syntax: isis**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- RSVP-TE and BGP-LS are supported on L2 only.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# isis
    dnRouter(cfg-protocols-isis)#


**Removing Configuration**

To remove all IS-IS instances and return all global IS-IS configuration to the default values:
::

    dnRouter(cfg-protocols)# no isis

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
