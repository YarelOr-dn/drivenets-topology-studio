Neighbor Discovery Protocol Overview
------------------------------------
In IPv6 networks, the neighbor discovery protocol (NDP) is responsible for:

- Router discovery - locating the routers that reside on an attached link
- Prefix discovery - discovering the set of address prefixes that define which destinations are on-link
- Parameter discovery - learning parameters (MTU, hop limit value) to place in outgoing packets
- Address auto-configuration - nodes automatically configure addresses for interfaces
- Neighbor address resolution - determining the link-layer address of an on-link destination given only the destination's IP address
- Next-hop determination - mapping an IP destination address to the IP address of the neighbor to which traffic for the destination should be sent (i.e. the next hop).
- Neighbor reachability verification - determining if the neighbor is reachable
- Duplicate address detection - determining if an address it wants to use is in use by another node
- Redirect - informing a host of a better next-hop node for reaching a specific destination

NDP uses the following ICMPv6 message types to carry out its tasks:

- Router solicitation (type 133) - When an interface becomes enabled, hosts may send out Router Solicitations that request routers to generate Router Advertisements immediately rather than at their next scheduled time.
- Router advertisement (type 134) - IPv6 routers send router advertisement messages periodically or in response to a Router Solicitation message, to inform hosts about the IPv6 prefixes used on the link.
- Neighbor solicitation (type 135) - Sent by a node to determine the link-layer address of a neighbor, or to verify that the neighbor is still reachable. Neighbor solicitation messages are also used for duplicate address detection.
- Neighbor advertisement (type 136) - A response to a Neighbor Solicitation message, or to announce a link-layer address change.
- Redirect (type 137) - Used by routers to inform hosts of a better next hop for a destination.

When IS-IS is available, DNOS takes the IP and MAC addresses from the IS-IS hello messages and periodic messages and pre-installs them entries in the NDP table.

For NDP-related commands, see:

- interfaces ndp

- show ndp

- clear ndp

For dynamic ARP/NDP synchronization, see:

- Dynamic ARP
