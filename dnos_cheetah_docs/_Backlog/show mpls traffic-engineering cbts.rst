show mpls traffic-engineering cbts
----------------------------------

**Command syntax: show mpls traffic-engineering cbts**

**Description:** Displays traffic CoS mapping to RSVP-TE tunnels

destination [ipv4-address] - when set, also display the current in-use CoS to Te-class mapping, reflecting te tunnels forwarding state towards the required destination.

-  CoS - traffic class-of-service, either MPLS EXP or IP Precedence

-  te-class - configured CoS to tunnel te-class mapping

**CLI example:**
::

	dnRouter# show mpls traffic-engineering cbts
	CBTS: enabled
	| CoS   | Te-class   |
	|-------+------------|
	|     0 |          4 |
	|     1 |          3 |
	|     2 |          2 |
	|     3 |          2 |
	|     4 |          2 |
	|     5 |          2 |
	|     6 |          1 |
	|     7 |          1 |
	
	
	
**Command mode:** operational

**TACACS role:** viewer

**Note:**

**Help line:**
