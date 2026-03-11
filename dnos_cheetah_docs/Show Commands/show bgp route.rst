show bgp route
--------------

**Minimum user role:** viewer

To display BGP routing table for the specified route:



**Command syntax: show bgp** instance vrf [vrf-name] [address-family] [sub-address-family] **route { [ip-address] \| [ip-prefix]** longer-prefixes} bestpath-compare

**Command mode:** operational


..
	**Internal Note**

	- use vrf to display routing information for a non-default vrf

	- use address-family, sub-address-family for specific afi-safi routes

	- for non-default instance vrf support only "unicast" sub-address-family

	- longer-prefixes can only be set with ip-prefix

	- bestpath-compare dry-runs best path selection algorithm according to the current metrics and shows the best path and its win reason over each other path. During routes updates, the dry-run result may be out-of-sync with FIB and/or RIB, i.e. the displayed best path may be different than the one in the FIB and the one advertised to peers.

	- bestpath-compare doesn't work with longer-prefixes

**Parameter table**

+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Parameter          | Description                                                                                                                                             | Range                    |
+====================+=========================================================================================================================================================+==========================+
| vrf-name           | Display routing information for a non-default VRF                                                                                                       | 1..255 characters        |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| address-family     | Display routing information for a specific address-family (AFI)                                                                                         | IPv4                     |
|                    |                                                                                                                                                         | IPv6                     |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| sub-address-family | Display routing information for a specific subsequent address-family (SAFI). Only unicast is supported with a non-default VRF.                          | unicast                  |
|                    |                                                                                                                                                         | multicast                |
|                    |                                                                                                                                                         | vpn                      |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| ip-address         | IP address in IPv4 format or IPv6 format. Must match the AFI or SAFI when specified.                                                                    | A.B.C.D                  |
|                    |                                                                                                                                                         | xx:xx::xx:xx             |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| ip-prefix          | IP-prefix in IPv4 format or IPv6 format. Must match the AFI or SAFI when specified.                                                                     | A.B.C.D/x                |
|                    |                                                                                                                                                         | xx:xx::xx:xx/x           |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| bestpath-compare   | Compares between each path and the overall best path                                                                                                    |                          |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------+

**Example**
::

	dnRouter# show bgp route 6.6.6.6/32
	BGP IPv4 Unicast routing table entry for 6.6.6.6/32
	Paths: (2 available, best #2, table Default-IP-Routing-Table)
	  Advertised to non peer-group peers:
	  7.7.7.7 11.0.0.11 11.0.0.12
	 Path #1:
	  Local
	    10.10.10.10 (metric 22) from 10.10.10.10 (10.10.10.10)
	      Origin incomplete, metric 15, localpref 100, aigp metric 10 (total 32), remote-label 3, valid, internal
	      RPKI best-path selection: enabled, allow-invalid: disabled, prefix-validation state: valid
	      Last update: Wed Feb 28 15:18:09 2018
	 Path #2:
	  Local
	    5.5.5.5 (metric 21) from 5.5.5.5 (5.5.5.5)
	      Origin incomplete, metric 20, localpref 100, aigp metric 10 (total 31), local-label 100001, remote-label 3, valid, internal, best
	      RPKI best-path selection: enabled, allow-invalid: disabled, prefix-validation state: valid
	      Last update: Wed Feb 28 15:18:29 2018

	% Network not in IPv4 Multicast table
	% Network not in VPN-IPv4 Unicast table


	dnRouter# show bgp route 44.33.2.0/24
	BGP IPv4 Unicast routing table entry for 44.33.2.0/24
	Paths: (2 available, best #1, table Default-IP-Routing-Table)
	  Advertised to non peer-group peers:
	  173.0.12.11 173.0.25.5
	 Path #1:
	  3 4
	    173.0.23.3 from 173.0.23.3 (9.9.9.3)
	      Origin IGP, localpref 100, local-label 100001, remote-label 100001, valid, external, best
	      RPKI best-path selection: enabled, allow-invalid: disabled, prefix-validation state: unverified
	      AddPath ID: RX 0, TX 3
	      Last update: Thu Oct 11 10:46:20 2018
	 Path #2:
	  5 4
	    173.0.25.5 from 173.0.25.5 (9.9.9.5)
	      Origin IGP, localpref 100, remote-label 100001, valid, external, alternate-path
	      RPKI best-path selection: enabled, allow-invalid: disabled, prefix-validation state: unverified
	      AddPath ID: RX 0, TX 2
	      Last update: Thu Oct 11 10:46:20 2018


	dnRouter# show bgp route 55.44.33.0/24
	BGP IPv4 Unicast routing table entry for 55.44.33.0/24
	Paths: (1 available, best #1, table Default-IP-Routing-Table)
	  Advertised to non peer-group peers:
	  3.3.3.3
	 Path #1:
	  Local
	    2.2.2.2 from 2.2.2.2 (2.2.2.2)
	      Origin IGP, localpref 100, valid, confed-internal, best
	      RPKI best-path selection: disabled, allow-invalid: disabled, prefix-validation state: unverified
	      AddPath ID: RX 0, TX 3
	      Last update: Thu Oct 11 10:46:20 2018


	dnRouter# show bgp route 55.66.77.0/24
	BGP IPv4 Unicast routing table entry for 55.66.77.0/24
	Paths: (1 available, best #1, table Default-IP-Routing-Table)
	  Advertised to non peer-group peers:
	  2.2.2.2
	 Path #1:
	  (65001) 300
	    3.3.3.3 from 3.3.3.3 (3.3.3.3)
	      Origin IGP, localpref 100, local-label 100001, valid, confed-external, best
	      RPKI best-path selection: disabled, allow-invalid: disabled, prefix-validation state: unverified
	      AddPath ID: RX 0, TX 3
	      Last update: Thu Oct 11 10:46:20 2018


	dnRouter# show bgp route 54.54.54.55/32
	BGP IPv4 Unicast routing table entry for 54.54.54.55/32
	Paths: (1 available, best #1, table Default-IP-Routing-Table)
	  Advertised best to peers:
	  1.1.1.1 11.11.11.11
	 Path #1
	  Local, (Received from a RR-client)
	      54.54.54.54 (metric 10) from 54.54.54.54 (54.54.54.55)
	     Origin IGP, metric 0, localpref 100, local-label 24100, remote-label 3, valid, internal, best
	     Prefix-SID: label-index 100, Originator-SRGB base 24000 range 8000
	     RPKI best-path selection: enabled, allow-invalid: disabled, prefix-validation state: unverified
	     AddPath ID: RX 0, TX 2
	     Last update: 26-Feb-2023 12:12:56 UTC


	dnRouter# show bgp route 54.54.54.55/32
	BGP IPv4 Unicast routing table entry for 54.54.54.55/32
	Paths: (1 available, best #1, table Default-IP-Routing-Table)
	  Advertised best to peers:
	  1.1.1.1 11.11.11.11
	 Path #1
	  Local, (stale), (Received from a RR-client)
	      54.54.54.54 (metric 10) from 54.54.54.54 (54.54.54.55)
	     Origin IGP, metric 0, localpref 100, local-label 24100, remote-label 3, valid, internal, best
	     Prefix-SID: label-index 100, Originator-SRGB base 24000 range 8000
	     RPKI best-path selection: enabled, allow-invalid: disabled, prefix-validation state: unverified
	     AddPath ID: RX 0, TX 2
	     Last update: 26-Feb-2023 12:12:56 UTC


	dnRouter# show bgp ipv4 unicast route 54.54.54.55/32
	BGP IPv4 Unicast routing table entry for 54.54.54.55/32
	Paths: (1 available, best #1, table Default-IP-Routing-Table)
	  Advertised best to peers:
	  1.1.1.1 11.11.11.11
	 Path #1
	  Local, (Received from a RR-client)
	      54.54.54.54 (metric 10) from 54.54.54.54 (54.54.54.55)
	     Origin IGP, metric 0, localpref 100, local-label 24100, remote-label 3, valid, internal, best
	     Prefix-SID: label-index 100, Originator-SRGB base 24000 range 8000
	     RPKI best-path selection: enabled, allow-invalid: disabled, prefix-validation state: unverified
	     AddPath ID: RX 0, TX 2
	     Last update: 26-Feb-2023 12:12:56 UTC


	dnRouter# show bgp route 100.10.0.3/32 bestpath-compare
	BGP IPv4 Unicast routing table entry for 100.10.0.3/32
	Paths: (4 available, best #1, table Default-IP-Routing-Table)
	  Advertised to non peer-group peers:
	   101.0.1.150 101.0.3.210
	 Path #1:
	  4210010000
	    100.10.0.2 (metric 23) from 100.0.0.2 (100.0.0.2)
	      Origin incomplete, localpref 100, aigp metric 5 (total 28), local-label 152761, remote-label 100002, weight 200, valid, internal, best
	      Community: 7018:6649 7018:8203 7018:8205 7018:8206 7018:8211
	      Extended Community: SoO:4210010000L:700
	      RPKI best-path selection: disabled, allow-invalid: disabled, prefix-validation state: unverified
	      AddPath ID: RX 0, TX 2
	      Last update: Thu Jan 30 10:30:37 2020
	      Overall best
	 Path #2:
	  4210010000
	    101.10.0.17 (metric 3) from 101.0.0.17 (101.0.0.17)
	      Origin incomplete, localpref 50, aigp metric 26 (total 29), remote-label 100003, valid, internal
	      Community: 7018:6649 7018:8203 7018:8205 7018:8206 7018:8207 7018:8211 65060:8207
	      Extended Community: SoO:4210010000L:700
	      RPKI best-path selection: disabled, allow-invalid: disabled, prefix-validation state: unverified
	      AddPath ID: RX 0, TX 5
	      Last update: Thu Jan 30 10:30:38 2020
	      Lower local preference than best path (Path #1)
	 Path #3:
	  4210010000 4210010001
	    101.10.0.19 (metric 13) from 101.0.0.19 (101.0.0.19)
	      Origin incomplete, localpref 100, aigp metric 36 (total 49), remote-label 152514, valid, external
	      Community: 7018:6649 7018:8203 7018:8205 7018:8206 7018:8207 7018:8211
	      Extended Community: SoO:4210010000L:700
	      RPKI best-path selection: disabled, allow-invalid: disabled, prefix-validation state: valid
	      AddPath ID: RX 0, TX 4
	      Last update: Thu Jan 30 10:30:38 2020
	      Longer AS path than best path (Path #1)
	 Path #4:
	  4210010000
	    100.10.0.3 (metric 27) from 100.0.0.3 (100.0.0.3)
	      Origin incomplete, metric 0, localpref 100, aigp metric 0 (total 27), remote-label 3, valid, internal, alternate-path
	      Community: 7018:6649 7018:8203 7018:8205 7018:8211
	      Extended Community: SoO:4210010000L:700
	      RPKI best-path selection: disabled, allow-invalid: disabled, prefix-validation state: unverified
	      AddPath ID: RX 0, TX 3
	      Last update: Thu Jan 30 09:44:44 2020
	      Higher router ID than best path (Path #1)

	dnRouter# show bgp instance vrf vrf1 route 2.120.0.0/24
	BGP IPv4 Unicast routing table entry for 2.120.0.0/24
	Paths: (1 available, best #1, table Default-IP-Routing-Table)
	Advertised best to peers:
	1.0.0.5 2.0.0.5 3.0.0.5 4.0.0.5 5.0.0.5
	Path #1
	Local
		6.0.0.5 [vrf vrf2] from 6.0.0.5 (207.0.0.1)
		Origin IGP, leaked-from: vrf vrf2, localpref 100, valid, external, best
		RPKI best-path selection: enabled, allow-invalid: disabled, prefix-validation state: unverified
		AddPath ID: RX 0, TX 2
		Last update: 28-Mar-2022 13:48:08 UTC
	
	dnRouter# show bgp route 1.1.1.1

	dnRouter# show bgp instance vrf A route 1.1.1.0/24

	dnRouter# show bgp instance vrf A ipv4 unicast route 1.1.1.0/24


	dnRouter# show bgp ipv6 unicast network 2:2::2:/32 longer-prefixes


.. **Help line:** show bgp ipv4 routes

**Command History**

+---------+-------------------------------------------------------------------------------------------+
| Release | Modification                                                                              |
+=========+===========================================================================================+
| 6.0     | Command introduced                                                                        |
+---------+-------------------------------------------------------------------------------------------+
| 7.0     | Added AIGP information to output                                                          |
+---------+-------------------------------------------------------------------------------------------+
| 11.6    | Added BGP confederation show command output                                               |
+---------+-------------------------------------------------------------------------------------------+
| 13.1    | Added path numbering to numbering and bestpath-compare option to display the winning path |
+---------+-------------------------------------------------------------------------------------------+
| 15.0    | Added support for the display of Route Reflector and Route-Reflector Client               |
+---------+-------------------------------------------------------------------------------------------+
| 16.1    | Added support for IPv4 Multicast SAFI                                                     |
+---------+-------------------------------------------------------------------------------------------+
