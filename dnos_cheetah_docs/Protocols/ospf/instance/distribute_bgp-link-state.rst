protocols ospf instance distribute bgp-link-state id
----------------------------------------------------

**Minimum user role:** operator

This command is part of the BGP-LS feature for Traffic Engineering. In order to support Traffic engineering tunnel delegation to a centralize entity, the network must provide the centralized entity an ongoing full view of the network TE link state. 
BGP-LS is used to send IGP-TE link information to a remote controller. The remote controller, known as PCE, will in turn use this information to create, update and remove TE tunnels in the network.
This command instructs the system to export the OSPFv2 TE database to BGP-LS. The network information, topology, bandwidth, segment-routing attributes, and link cost are all sent to the path computation element through BGP.

To distribute the OSPFv2 database to BGP-LS:

**Command syntax: distribute bgp-link-state id [id]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| id        | A unique identifier to distinguish the OSPFv2 instance in BGP-LS updates. Must   | 0-65535 | \-      |
|           | be unique for all OSPFv2 instances.                                              |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# instance INST_1
    dnRouter(cfg-protocols-ospf-inst)# distribute bgp-link-state id 1


**Removing Configuration**

To stop exporting the OSPFv2 database to BGP-LS:
::

    dnRouter(cfg-protocols-ospf-inst)# no distribute bgp-link-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.0    | Command introduced |
+---------+--------------------+
