services mpls-oam
-----------------

**Minimum user role:** operator


MPLS Operations, Administration, and Maintenance (OAM) is used for detecting failures in the datapath (e.g. black holes and misrouting). MPLS OAM provides proactive and on-demand troubleshooting tools for MPLS Networks and services by measuring the MPLS network and diagnosing defects that cannot otherwise be detected.

In addition to detecting operational failures, MPLS OAM can also be used for accounting and performance measurement of the MPLS network.

While Internet Control Message Protocol (ICMP) ping and traceroute can assist in diagnosing the root cause of a forwarding failure, they might not detect LSP failures because an ICMP packet can be forwarded via an IP path to the destination when an LSP breakage occurs.

MPLS LSP ping and traceroute are better suited for identifying LSP breakages because:

-	An MPLS echo request packet cannot be forwarded via an IP path because its IP Time to Live (TTL) is set to 1 and its IP destination address field is set to a 127.x.y.z/8 address.

-	The Forwarding Equivalence Class (FEC) being checked is not stored in the IP destination address field (as is the case of ICMP).

-	An LSP can take multiple paths from ingress to egress. This particularly occurs with Equal Cost Multipath (ECMP). The LSP traceroute command can trace all possible paths to an LSP node.

The MPLS OAM includes the following set of protocols for effectively detecting problems in the MPLS network:

-	MPLS LSP ping - checks connectivity of LSPs: An MPLS echo packet is sent through an LSP to validate it. When the packet reaches the end of the path, it is sent to the control plane of the egress LSR. The egress LSR then verifies whether it is indeed an egress for the FEC. 

-	MPLS traceroute - used for hop-by-hop fault localization and/or path tracing: A packet is sent to the control plane of each transit LSR. The transit LSR performs various checks to confirm that it is indeed a transit LSR for this path; this LSR also returns additional information that helps check the control plane against the data plane.

To configure MPLS OAM, enter the services OAM configuration hierarchy:

**Command syntax: mpls-oam**

**Command mode:** config

**Hierarchies**

- services

**Note**

- MPLS OAM supports RSVP tunnels and BGP-LU LSPs only.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-protocols)# mpls-oam
    dnRouter(cfg-srv-mpls-oam)#


**Removing Configuration**

To revert all MPLS-OAM parameters to their default values and remove all configured profiles:
::

    dnRouter(cfg-srv)# no mpls-oam

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
