Label Distribution Protocol (LDP) Overview
------------------------------------------
Label Distribution Protocol (LDP) enables peer label switch routers (LSRs) to exchange label information for supporting hop-by-hop forwarding in a Multi-Protocol Label Switching (MPLS) network.

With IP forwarding, when a packet arrives at a router, the router looks at the destination address in the IP header, performs a route lookup, and forwards the packet to the next hop. With MPLS forwarding, when a packet arrives at a router, the router looks at the incoming label, looks up the label in a table, and forwards the packet to the next hop.

Each router has a unique LSR ID. When you enable LDP, LSRs send out discovery messages ("Hello" messages) to announce their presence in the network. The discovery messages are transmitted periodically as multicast UDP packets to all directly connected routers on the subnet. If a neighbor LSR responds to the message, the two routers can establish an LDP session. Within the "hello" packet, the router advertises its LSR ID and also a transport IP address, which is used to build the TCP connection with the neighbor LSR. The LSRs can then exchange label information.

DNOS supports downstream-unsolicited label distribution method with ordered label control and liberal label retention.

**Downstream-unsolicited** means that as soon as the LSR learns a route, it sends a FEC-to-label binding for that route to all peer LSRs, both upstream and downstream and does not wait for a request from an upstream device.

**Ordered** label control means that an LSR does not advertise a label for a FEC unless it is the egress LSR for the FEC (i.e. when the FEC is its directly attached interface or when MPLS is not configured on the next-hop interface) or until it has received a label for the FEC from its downstream peer. This prevents early data mapping from occurring on the first LSR in the path.

**Liberal** label retention means that any label mapping that may ever be used as a next hop is retained. Should a topology change occur, the labels to use in the new topology are already in place.

The mappings distributed by the LDP protocol are used to build a Label Information Base (LIB) - a data structure representing the mapping of each prefix to a label for each neighboring LDP peer. The LIBs are then used to construct the Label Forwarding Information Base (LFIB), which is the actual table used by the data path to take the forwarding decision.

The MPLS LDP-IGP synchronization feature provides a means to synchronize LDP and IGPs to minimize MPLS packet loss. When an IGP adjacency is established on a link but LDP IGP synchronization is not yet achieved or is lost, the IGP advertises the max-metric on that link. LDP-sync is always enabled in LDP. Also, all OSPF interfaces (except loopbacks) are enabled for LDP sync. See Configuring LDP Sync.