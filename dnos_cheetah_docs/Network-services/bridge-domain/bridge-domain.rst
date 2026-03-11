network-services bridge-domain
------------------------------

**Minimum user role:** operator

Bridge domains (Ethernet Virtual Private Network) refer to a Layer 2 broadcast domain consisting of a set of physical ports (“All-to-one bundling”, “port-mode”), and virtual ports (Attachment Circuits).
Data frames are switched within a bridge domain based on the destination MAC address.  Source MAC address learning is performed on all incoming packets.
Multicast, broadcast, and unknown destination unicast frames are flooded within the bridge domain.
Incoming frames are mapped to a bridge domain by their incoming VLAN/VLANs.
Traffic cannot leak between one bridge domain to another. Each bridge domain is totally independent (a leak is possible only via routing through IRBs).
The bridge domain connects the layer 2 interface(s) of one PE with the layer 2 interface(s) of other PEs, across the layer 3 core mpls network. The EVPN service uses an MPLS or VxLAN transport layer and a BGP control layer.
To enter the Bridge Domain service configuration mode:

**Command syntax: bridge-domain**

**Command mode:** config

**Hierarchies**

- network-services

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# bridge-domain
    dnRouter(cfg-network-services-bd)#


**Removing Configuration**

To remove all EVPN services:
::

    dnRouter(cfg-network-services)# no brifge-domain

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
