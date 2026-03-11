show access-lists
-----------------

**Command syntax: show access-lists** [access-list-type] name [access-list-name] interface [interface-name]

**Description:** show access-lists rules with match counter per rule.

**CLI example:**
::

	dnRouter# show access-lists

	Interface bundle-1:

		IPv4 Access Lists name: ACL_IPv4_IN_1    Direction: in
		rule 10 allow
			src-ip=10.1.1.2, src-port=any, dest-ip=1.2.3.4/20, dest-port=123-125, protocol=tcp, ttl=any, next-hop1=10.1.1.3
			Match 48 packets
		rule 15 deny
			src-ip=10.1.1.2, src-port=any, dest-ip=any, dest-port=any, protocol=icmp, ttl=any
			Match 12 packets
		rule default-icmp allow
			src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=icmp, ttl=any
			Match 600 packets
		rule default deny
			src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=any, ttl=an
			Match 0 packets

		IPv6 Access Lists name: ACL_IPv6_IN_1     Direction: in
		rule 10 deny
			src-ip=2001:1234::1, src-port=any, dest-ip=any, dest-port=any, protocol=icmp, hop-limit=any
			Match 48 packets
		rule default-icmp allow
			src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=icmp, ttl=any
			Match 600 packets
		rule default deny
			src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=any, ttl=any
			Match 0 packets

	Interface bundle-2:

		IPv4 Access Lists name: ACL_IPv4_IN_2     Direction: in
		rule 10 allow
			src-ip=10.1.1.2, src-port=100-4500, dest-ip=any, dest-port=any, protocol=tcp, ttl=any
			Match 12 packets
		rule default-icmp allow
			src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=icmp, ttl=any
			Match 600 packets
		rule default deny
			src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=any, ttl=an
			Match 0 packets

	Interface bundle-2:

		IPv4 Access Lists name: ACL_IPv4_OUT_1     Direction: out
		rule 10 allow
			src-ip=10.1.1.2, src-port=100-4500, dest-ip=any, dest-port=any, protocol=tcp, ttl=any
			Match 48 packets
		rule default-icmp allow
			src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=icmp, ttl=any
			Match 124 packets
		rule default deny
			src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=any, ttl=an
			Match 12 packets


	dnRouter# show access-lists ipv4
		Interface bundle-1:

		IPv4 Access Lists name: ACL_IPv4_IN_1      Direction: in
		rule 10 allow
			src-ip=10.1.1.2, src-port=any, dest-ip=1.2.3.4/20, dest-port=123-125, protocol=tcp, ttl=any, next-hop1=10.1.1.3
			Match 48 packets
		rule 15 deny
			src-ip=10.1.1.2, src-port=any, dest-ip=any, dest-port=any, protocol=icmp, ttl=any
			Match 12 packets
		rule default-icmp allow
			src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=icmp, ttl=any
			Match 600 packets
		rule default deny
			src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=any, ttl=an
			Match 0 packets


	Interface bundle-2:

		IPv4 Access Lists name: ACL_IPv4_IN_2     Direction: in
		rule 10 allow
			src-ip=10.1.1.2, src-port=100-4500, dest-ip=any, dest-port=any, protocol=tcp, ttl=any
			Match 12 packets
		rule default-icmp allow
			src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=icmp, ttl=any
			Match 600 packets
		rule default deny
			src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=any, ttl=an
			Match 0 packets

	Interface bundle-2:

		IPv4 Access Lists name: ACL_IPv4_OUT_1     Direction: out
		rule 10 allow
			src-ip=10.1.1.2, src-port=100-4500, dest-ip=any, dest-port=any, protocol=tcp, ttl=any
			Match 48 packets
		rule default-icmp allow
			src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=icmp, ttl=any
			Match 124 packets
		rule default deny
			src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=any, ttl=an
			Match 12 packets


	dnRouter# show access-lists name ACL_IPv4_IN_1
	Interface bundle-1:

		IPv4 Access Lists name: ACL_IPv4_IN_1     Direction: in
		rule 10 allow
			src-ip=10.1.1.2, src-port=any, dest-ip=1.2.3.4/20, dest-port=123-125, protocol=tcp, ttl=any, next-hop1=10.1.1.3
		rule 15 deny
			src-ip=10.1.1.2, src-port=any, dest-ip=any, dest-port=any, protocol=icmp, ttl=any
			Match 12 packets
		rule default-icmp allow
			src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=icmp, ttl=any
			Match 600 packets
		rule default deny
			src-ip=any, src-por


	dnRouter# show access-lists interface bundle-2
	Interface bundle-2:

		IPv4 Access Lists name: ACL_IPv4_IN_2     Direction: in
		rule 10 allow
			src-ip=10.1.1.2, src-port=100-4500, dest-ip=any, dest-port=any, protocol=tcp, ttl=any
			Match 12 packets
		rule default-icmp allow
			src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=icmp, ttl=any
			Match 600 packets
		rule default deny
			src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=any, ttl=an
			Match 0 packets

	Interface bundle-2:

	IPv4 Access Lists name: ACL_IPv4_OUT_1     Direction: out
	rule 10 allow
		src-ip=10.1.1.2, src-port=100-4500, dest-ip=any, dest-port=any, protocol=tcp, ttl=any
		Match 48 packets
	rule default-icmp allow
		src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=icmp, ttl=any
		Match 124 packets
	rule default deny
		src-ip=any, src-port=any, dest-ip=any, dest-port=any, protocol=any, ttl=an
		Match 12 packets



**Command mode:** operational

**TACACS role:** viewer

**Note:**

- When a user selects a specific type/access-list-name/interface-name it will filter according to it

- The user should be able to filter with several parameters on the same line. (filter by access-list-name)

**Help line:** show access-list information

**Parameter table:**

+------------------+-----------+-------------------------+
| Parameter        | Values    | Default value           |
+==================+===========+=========================+
| access-list-type | ipv4/ipv6 |                         |
+------------------+-----------+-------------------------+
| access-list-name | string    |                         |
+------------------+-----------+-------------------------+
| interface-name   | ge<interface speed>-<A>/<B>/<C>     |
|                  | geX-<f>/<n>/<p>.<sub-interface id>  |
|                  |                                     |
|                  | bundle-<bundle-id>                  |
|                  |                                     |
|                  | bundle-<bundle-id.sub-bundle-id>    |
|                  |                                     |
+------------------+-------------------------------------+