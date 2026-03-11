traffic-engineering diffserv-te cbts
------------------------------------

**Minimum user role:** operator

Class-based tunnel selection (CBTS) dynamically routes different class-of-service (CoS) traffic on different TE tunnels. Tunnel selection is based on the packet's CoS: for MPLS packets the EXP value of the topmost label is used; for IP packets the IPP value is used.

When CBTS is enabled, packets will be forwarded to a tunnel only if:

-	The packet destination is resolved by the specific RSVP tunnel (either directly or by an IGP-shortcut)

-	The packet CoS field value matches the tunnel's te-class according to the configured te-class-map te-class (see "mpls traffic-engineering diffserv-te te-class-map te-class" (including fallback selection algorithm).

If multiple tunnels are active for the same te-class selected by CBTS, the traffic is load-balanced across them.

If no active TE tunnel matches the traffic CoS, the traffic will be forwarded according to the following fallback selection algorithm:

#.	Forward traffic over the TE-class X that forwards the lowest CoS value.

#.	If no tunnel is available for TE-class X, use the TE-class of the following CoS value.

#.	If no TE-class matching any of the CoS values is available, don't apply the CBTS constraint and forward the traffic over all available tunnels (ECMP).

To enter the CBTS configuration hierarchy:

**Command syntax: cbts**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering diffserv-te



**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering
	dnRouter(cfg-protocols-mpls-te)# diffserv-te
	dnRouter(cfg-mpls-te-diffserv)# cbts
	dnRouter(cfg-te-diffserv-cbts)#

**Removing Configuration**

To revert all CBTS configuration to default values:
::

	dnRouter(cfg-mpls-te-diffserv)# no cbts


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+