protocols isis instance distribute bgp-link-state id
----------------------------------------------------

**Minimum user role:** operator

This command is part of the BGP-LS feature for Traffic Engineering. In order to support Traffic engineering tunnel delegation to a centralize entity, the network must provide the centralized entity an ongoing full view of the network TE link state. BGP-LS is used to send IGP-TE link information to a remote controller. The remote controller, known as PCE, will in turn use this information to create, update and remove TE tunnels in the network.

This command instructs the system to export the IS-IS-TE database to BGP-LS. The network information, topology, bandwidth, and link cost are all sent to the path computation element through BGP.

To distribute the IS-IS database to BGP-LS:

**Command syntax: distribute bgp-link-state [level] id [bgp-link-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Note**
- The IS-IS is not exported to BGP-LS by default.

**Parameter table**

+----------------+----------------------------------------------------------------------------------+-------------+---------+
| Parameter      | Description                                                                      | Range       | Default |
+================+==================================================================================+=============+=========+
| level          | The IS-IS routing level database to distribute                                   | | level-1   | \-      |
|                |                                                                                  | | level-2   |         |
+----------------+----------------------------------------------------------------------------------+-------------+---------+
| bgp-link-state | A unique identifier to distinguish the IS-IS instance in BGP-LS updates. Must be | 0-65535     | \-      |
|                | unique for all IS-IS instances.                                                  |             |         |
+----------------+----------------------------------------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# distribute bgp-link-state level-2 id 1


**Removing Configuration**

To stop exporting the IS-IS database to BGP-LS:
::

    dnRouter(cfg-protocols-isis-inst)# no distribute bgp-link-state

**Command History**

+---------+-----------------------------------------+
| Release | Modification                            |
+=========+=========================================+
| 10.0    | Command introduced                      |
+---------+-----------------------------------------+
| 11.0    | Removed option to include ipv6 prefixes |
+---------+-----------------------------------------+
