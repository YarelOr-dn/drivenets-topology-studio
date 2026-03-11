show access-lists statistics-summary
------------------------------------

**Command syntax: show access-lists statistics-summary** [access-list-type] [access-list-name]

**Description:** show access-lists rules with aggregated match packet counter over all atteched interfaces

**CLI example:**
::

	dnRouter# show access-lists statistics-summary

	IPv4 Access Lists name: ACL_IPv4_IN_1
	rule 10 allow
		src-ip=10.1.1.2, src-port=any, dest-ip=1.2.3.4/20, dest-port=123-125, protocol=tcp, ttl=any, next-hop1=10.1.1.3
	    Match 48 packets over all atteched ingress interface
	    Match 0 packets over all atteched egress interface
	rule 15 deny
		src-ip=10.1.1.2, src-port=any, dest-ip=any, dest-port=any, protocol=icmp, ttl=any
		Match 12 packets over all atteched ingress interface
	    Match 0 packets over all atteched egress interface
	rule default-icmp allow
		src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=icmp, ttl=any
		Match 600 packets over all atteched ingress interface
		Match 0 packets over all atteched egress interface
	rule default deny
		src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=any, ttl=an
		Match 0 packets over all atteched ingress interface
		Match 0 packets over all atteched egress interface


	IPv4 Access Lists name: ACL_IPv4_IN_2
	rule 10 allow
		src-ip=10.1.1.2, src-port=100-4500, dest-ip=any, dest-port=any, protocol=tcp, ttl=any
	    Match 12 packets over all atteched ingress interface
	    Match 0 packets over all atteched egress interface
	rule default-icmp allow
		src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=icmp, ttl=any
		Match 600 packets over all atteched ingress interface
		Match 0 packets over all atteched egress interface
	rule default deny
		src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=any, ttl=an
		Match 0 packets over all atteched ingress interface
		Match 0 packets over all atteched egress interface

	dnRouter# show access-lists statistics-summary ipv4 ACL_IPv4_IN_2

	IPv4 Access Lists name: ACL_IPv4_IN_2
		rule 10 allow
			src-ip=10.1.1.2, src-port=100-4500, dest-ip=any, dest-port=any, protocol=tcp, ttl=any
		    Match 12 packets over all atteched ingress interface
		    Match 0 packets over all atteched egress interface
		rule default-icmp allow
			src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=icmp, ttl=any
			Match 600 packets over all atteched ingress interface
			Match 0 packets over all atteched egress interface
		rule default deny
			src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=any, ttl=an
			Match 0 packets over all atteched ingress interface
			Match 0 packets over all atteched egress interface


**Command mode:** operational

**TACACS role:** viewer

**Note:**

- When a user selects a specific type/access-list-name it will filter according to it

- The user should be able to filter with several parameters on the same line. (filter by access-list-name)

**Help line:** show access-lists rules with match counter per rule.

**Parameter table:**

+------------------+-----------+---------------+
| Parameter        | Values    | Default value |
+==================+===========+===============+
| access-list-type | ipv4/ipv6 |               |
+------------------+-----------+---------------+
| access-list-name | string    |               |
+------------------+-----------+---------------+