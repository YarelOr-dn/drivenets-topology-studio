show ospf database
------------------

**Minimum user role:** viewer

The show ospf database is a group of commands that display lists of information related to the OSPF database.



**Command syntax: show ospf** instance [ospf-instance-name] **database** { [lsa-type] \| [lsa-type] link-state-id [ip-address] } {adv-router [adv-address] \| self-originate}

**Command mode:** operational


..
	**Internal Note**

	- The vertical bar (|) indicates that only one of the parameters can appear in the command.

	- self-originate is optional

	- use "instance [ospf-instance-name]" to display information from a specific OSPF instance, when not specified, display information from all OSPF instances

**Parameter table**

+--------------------+----------------------------------------------------------------+
| Argument           | Description                                                    |
+====================+================================================================+
| No argument        | See example below                                              |
+--------------------+----------------------------------------------------------------+
| asbr-summary       | ASBR summary link states                                       |
+--------------------+----------------------------------------------------------------+
| external           | External link states                                           |
+--------------------+----------------------------------------------------------------+
| network            | Network link states                                            |
+--------------------+----------------------------------------------------------------+
| router             | Router link states                                             |
+--------------------+----------------------------------------------------------------+
| nssa-external      | NSSA external link state                                       |
+--------------------+----------------------------------------------------------------+
| opaque-area        | Link area opaque LSA                                           |
+--------------------+----------------------------------------------------------------+
| opaque-as          | Link AS opaque LSA                                             |
+--------------------+----------------------------------------------------------------+
| opaque-link        | Link local opaque LSA                                          |
+--------------------+----------------------------------------------------------------+
| summary            | Network summary link states                                    |
+--------------------+----------------------------------------------------------------+
| link-state-id      | Link State ID (as an IP address)                               |
+--------------------+----------------------------------------------------------------+
| adv-router         | Advertising Router link states                                 |
+--------------------+----------------------------------------------------------------+
| self-originate     | Self-originated link states                                    |
+--------------------+----------------------------------------------------------------+
| max-age            | LSAs in MaxAge list                                            |
+--------------------+----------------------------------------------------------------+
| ospf-instance-name | Filters the displayed information to a specific OSPF instance. |
+--------------------+----------------------------------------------------------------+

These arguments can appear in several combinations:

+---------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| Command                                                                                                 | Example                                                          |
+=========================================================================================================+==================================================================+
| show ospf database                                                                                      | show ospf database                                               |
+---------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| show ospf database (asbr-summary|external|network|router|summary)                                       | show ospf database router                                        |
+---------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| show ospf database (asbr-summary|external|network|router|summary) link-state-id                         | show ospf database external link-state-id                        |
+---------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| show ospf database (asbr-summary|external|network|router|summary) link-state-id adv-router [adv-router] | show ospf database network link-state-id adv-router [adv-router] |
+---------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| show ospf database (asbr-summary|external|network|router|summary) adv-router [adv-router]               | show ospf database network adv-router [adv-router]               |
+---------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| show ospf database (asbr-summary|external|network|router|summary) link-state-id self-originate          | show ospf database asbr-summary link-state-id self-originate     |
+---------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| show ospf database (asbr-summary|external|network|router|summary) self-originate                        | show ospf database asbr-summary self-originate                   |
+---------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| show ospf database max-age                                                                              | show ospf database max-age                                       |
+---------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+
| show ospf database self-originate                                                                       | show ospf database self-originate                                |
+---------------------------------------------------------------------------------------------------------+------------------------------------------------------------------+


**Example**
::

	dnRouter# show ospf database

	OSPF Instance instance1

		OSPF Router with ID (100.70.1.45)

			Router Link States (Area 0.0.0.0)

	Link ID         ADV Router      Age  Seq#       CkSum  Link count
	0.0.0.1         0.0.0.1         1625 0x8000003d 0x628e 4
	0.0.1.1         0.0.1.1         1625 0x8000003d 0x1679 3
	0.0.2.1         0.0.2.1         1625 0x8000003d 0x1968 3
	0.0.3.1         0.0.3.1         1625 0x8000003d 0x1c57 3
	0.0.4.1         0.0.4.1         1625 0x8000003d 0x277e 2
	0.0.5.1         0.0.5.1         1625 0x8000003d 0x1356 3
	0.0.6.1         0.0.6.1         1625 0x8000003d 0x0713 4
	0.0.7.1         0.0.7.1         1625 0x8000003d 0xc641 4
	0.0.8.1         0.0.8.1         1625 0x8000003d 0x866f 4
	0.0.9.1         0.0.9.1         1625 0x8000003d 0x80b7 3
	0.0.10.1        0.0.10.1        1625 0x8000003d 0x9791 3

		Net Link States (Area 0.0.0.0)

	Link ID       	ADV Router      Age  Seq#       CkSum
	172.16.1.3      1.1.1.1         1245 0x800000EC 0x82E

		Summary Net Link States (Area 0.0.0.0)

	Link ID         ADV Router      Age  Seq#       CkSum
	172.16.240.0    3.3.3.3         1152 0x80000077 0x7A05
	172.16.241.0    8.8.8.8         1152 0x80000070 0xAEB7
	172.16.244.0    1.1.1.1         1152 0x80000071 0x95CB

		Type-10 Opaque Link Area Link States (Area 0.0.0.0)

	Link ID         ADV Router      Age  Seq#       CkSum     Opaque ID
	1.0.0.0         1.1.1.1         73   0x80000080 0x005951        0
	1.0.0.0         2.2.2.2         145  0x80000080 0x005d45        0
	1.0.0.0         3.3.3.3         1871 0x8000007f 0x006338        0
	1.0.0.0         4.4.4.4         1987 0x80000006 0x005ab2        0
	1.0.0.0         8.8.8.8         724  0x8000000c 0x003c09        0
	1.0.0.2         8.8.8.8         724  0x80000005 0x00ce63        2
	1.0.0.4         1.1.1.1         73   0x80000080 0x004aa2        4
	1.0.0.4         2.2.2.2         1134 0x80000080 0x0036a8        4
	1.0.0.4         3.3.3.3         1871 0x8000007f 0x00a9fc        4
	1.0.0.6         1.1.1.1         73   0x8000000e 0x00f44c        6

	Type-9 Opaque Link Local Link States (Area 0.0.0.0)

	Link ID         ADV Router      Age         Seq#       Checksum Opaque ID
	3.0.0.0         4.4.4.4         2           0x80000001 0x008307        0
	3.0.0.0         4.4.4.4         2           0x80000001 0x009513        0
	3.0.0.0         4.4.4.4         2           0x80000001 0x00aef8        0
	3.0.0.0         4.4.4.4         2           0x80000001 0x000f71        0


	dnRouter# show ospf instance instance1 database

	OSPF Instance instance1

		OSPF Router with ID (100.70.1.45)

			Router Link States (Area 0.0.0.0)

	Link ID         ADV Router      Age  Seq#       CkSum  Link count
	0.0.0.1         0.0.0.1         1625 0x8000003d 0x628e 4
	0.0.1.1         0.0.1.1         1625 0x8000003d 0x1679 3
	0.0.2.1         0.0.2.1         1625 0x8000003d 0x1968 3
	0.0.3.1         0.0.3.1         1625 0x8000003d 0x1c57 3
	0.0.4.1         0.0.4.1         1625 0x8000003d 0x277e 2
	0.0.5.1         0.0.5.1         1625 0x8000003d 0x1356 3
	0.0.6.1         0.0.6.1         1625 0x8000003d 0x0713 4
	0.0.7.1         0.0.7.1         1625 0x8000003d 0xc641 4
	0.0.8.1         0.0.8.1         1625 0x8000003d 0x866f 4
	0.0.9.1         0.0.9.1         1625 0x8000003d 0x80b7 3
	0.0.10.1        0.0.10.1        1625 0x8000003d 0x9791 3

		Net Link States (Area 0.0.0.0)

	Link ID       	ADV Router      Age  Seq#       CkSum
	172.16.1.3      1.1.1.1         1245 0x800000EC 0x82E

		Summary Net Link States (Area 0.0.0.0)

	Link ID         ADV Router      Age  Seq#       CkSum
	172.16.240.0    3.3.3.3         1152 0x80000077 0x7A05
	172.16.241.0    8.8.8.8         1152 0x80000070 0xAEB7
	172.16.244.0    1.1.1.1         1152 0x80000071 0x95CB

		Type-10 Opaque Link Area Link States (Area 0.0.0.0)

	Link ID         ADV Router      Age  Seq#       CkSum     Opaque ID
	1.0.0.0         1.1.1.1         73   0x80000080 0x005951        0
	1.0.0.0         2.2.2.2         145  0x80000080 0x005d45        0
	1.0.0.0         3.3.3.3         1871 0x8000007f 0x006338        0
	1.0.0.0         4.4.4.4         1987 0x80000006 0x005ab2        0
	1.0.0.0         8.8.8.8         724  0x8000000c 0x003c09        0
	1.0.0.2         8.8.8.8         724  0x80000005 0x00ce63        2
	1.0.0.4         1.1.1.1         73   0x80000080 0x004aa2        4
	1.0.0.4         2.2.2.2         1134 0x80000080 0x0036a8        4
	1.0.0.4         3.3.3.3         1871 0x8000007f 0x00a9fc        4
	1.0.0.6         1.1.1.1         73   0x8000000e 0x00f44c        6

	Type-9 Opaque Link Local Link States (Area 0.0.0.0)

	Link ID         ADV Router      Age         Seq#       Checksum Opaque ID
	3.0.0.0         4.4.4.4         2           0x80000001 0x008307        0
	3.0.0.0         4.4.4.4         2           0x80000001 0x009513        0
	3.0.0.0         4.4.4.4         2           0x80000001 0x00aef8        0
	3.0.0.0         4.4.4.4         2           0x80000001 0x000f71        0

	dnRouter# show ospf database asbr-summary

	OSPF Instance instance1

		OSPF Router with ID (100.70.1.45)


			ASBR-Summary Link States (Area 0.0.0.0)


	dnRouter# show ospf instance instance1 database asbr-summary

	OSPF Instance instance1

		OSPF Router with ID (100.70.1.45)


			ASBR-Summary Link States (Area 0.0.0.0)


	dnRouter# show ospf database external link-state-id 7.7.7.7

	OSPF Instance instance1

	       OSPF Router with ID (100.70.1.45)

	                AS External Link States

	  LS age: 873
	  Options: 0x0  : *|-|-|-|-|-|-|*
	  LS Flags: 0x6
	  LS Type: AS-external-LSA
	  Link State ID: 7.7.7.7 (External Network Number)
	  Advertising Router: 10.170.1.66
	  LS Seq Number: 8000002a
	  Checksum: 0xa374
	  Length: 36
	  Network Mask: /32
	        Metric Type: 1
	        TOS: 0
	        Metric: 0
	        Forward Address: 0.0.0.0
	        External Route Tag: 0


	dnRouter# show ospf instance instance1 database external link-state-id 7.7.7.7

	OSPF Instance instance1

	       OSPF Router with ID (100.70.1.45)

	                AS External Link States

	  LS age: 873
	  Options: 0x0  : *|-|-|-|-|-|-|*
	  LS Flags: 0x6
	  LS Type: AS-external-LSA
	  Link State ID: 7.7.7.7 (External Network Number)
	  Advertising Router: 10.170.1.66
	  LS Seq Number: 8000002a
	  Checksum: 0xa374
	  Length: 36
	  Network Mask: /32
	        Metric Type: 1
	        TOS: 0
	        Metric: 0
	        Forward Address: 0.0.0.0
	        External Route Tag: 0


	dnRouter# show ospf database network link-state-id 141.128.0.1 adv-router 0.0.0.1

	OSPF Instance instance1

	       OSPF Router with ID (100.70.1.45)


	                Net Link States (Area 0.0.0.0)

	  LS age: 919
	  Options: 0x0  : *|-|-|-|-|-|-|*
	  LS Flags: 0x6
	  LS Type: network-LSA
	  Link State ID: 141.128.0.1 (address of Designated Router)
	  Advertising Router: 0.0.0.1
	  LS Seq Number: 8000002a
	  Checksum: 0x2cf3
	  Length: 32
	  Network Mask: /24
	        Attached Router: 0.0.0.1
	        Attached Router: 0.0.1.1


	dnRouter# show ospf instance instance1 database network link-state-id 141.128.0.1 adv-router 0.0.0.1

	OSPF Instance instance1

	       OSPF Router with ID (100.70.1.45)


	                Net Link States (Area 0.0.0.0)

	  LS age: 919
	  Options: 0x0  : *|-|-|-|-|-|-|*
	  LS Flags: 0x6
	  LS Type: network-LSA
	  Link State ID: 141.128.0.1 (address of Designated Router)
	  Advertising Router: 0.0.0.1
	  LS Seq Number: 8000002a
	  Checksum: 0x2cf3
	  Length: 32
	  Network Mask: /24
	        Attached Router: 0.0.0.1
	        Attached Router: 0.0.1.1


	dnRouter# show ospf database external link-state-id 1.1.1.1 self-originate

	OSPF Instance instance1

		OSPF Router with ID (100.70.1.45)

			AS External Link States


	dnRouter# show ospf instance instance1 database external link-state-id 1.1.1.1 self-originate

	OSPF Instance instance1

		OSPF Router with ID (100.70.1.45)

			AS External Link States


	dnRouter# show ospf database opaque-area self-originate

	Ospf Instance instance1

            OSPF Router with ID (1.1.1.1)

                Type-10 Opaque Link Area Link States (Area 0)

	LS age: 363
	Options: (No TOS-capability, DC)
	LS Type: Opaque Area Router
	Link State ID: 1.0.0.0
	Opaque Type: 1
	Opaque ID: 0
	Advertising Router: 1.1.1.1
	LS Seq Number: 80000098
	Checksum: 0x2969
	Length: 28
	Router Address TLV:
	  MPLS TE router ID : 1.1.1.1


	LS age: 1352
	Options: (No TOS-capability, DC)
	LS Type: Opaque Area Link
	Link State ID: 1.0.0.4
	Opaque Type: 1
	Opaque ID: 4
	Advertising Router: 1.1.1.1
	LS Seq Number: 80000098
	Checksum: 0x71c3
	Length: 176

	    Link Type : Point-to-Point
	    Link ID : Neighbor Router-id 2.2.2.2
	    Interface Address : 10.1.12.1
	    Neighbor Address : 10.1.12.2
	    TE Metric : 3
	    Maximum bandwidth : 125000000 Bps
	    Maximum reservable bandwidth global: 0 Bps
	    Number of Priority : 8
		  Priority 0 :                    0 Bps  Priority 1 :                    0 Bps
		  Priority 2 :                    0 Bps  Priority 3 :                    0 Bps
		  Priority 4 :                    0 Bps  Priority 5 :                    0 Bps
 		  Priority 6 :                    0 Bps  Priority 7 :                    0 Bps
	    Admin Group : 0x0
	    IGP Metric : 3
	    GMPLS Shared Risked Link Group :
	      Number of SRLGs (2)
        	[1]: 123
        	[2]: 435
	    Administrative Group: 0


	LS age: 1352
	Options: (No TOS-capability, DC)
	LS Type: Opaque Area Link
	Link State ID: 1.0.0.6
	Opaque Type: 1
	Opaque ID: 6
	Advertising Router: 1.1.1.1
	LS Seq Number: 80000026
	Checksum: 0x1c6d
	Length: 176

	    Link Type : Point-to-Point
	    Link ID : Neighbor Router-id 4.4.4.4
	    Interface Address : 10.1.14.1
	    Neighbor Address : 10.1.14.4
	    TE Metric : 10
	    Maximum bandwidth : 125000000 Bps
	    Maximum reservable bandwidth global: 0 Bps
	    Number of Priority : 8
		  Priority 0 :                    0 Bps  Priority 1 :                    0 Bps
		  Priority 2 :                    0 Bps  Priority 3 :                    0 Bps
		  Priority 4 :                    0 Bps  Priority 5 :                    0 Bps
 		  Priority 6 :                    0 Bps  Priority 7 :                    0 Bps
	    Admin Group : 0x0
	    IGP Metric : 10
	    GMPLS Shared Risked Link Group :
	      Number of SRLGs (1)
		    [1]: 123
	    Administrative Group: 0


	LS age: 75
	Options: (No TOS-capability, DC)
	LS Type: Opaque Area Link
	Link State ID: 1.0.0.10
	Opaque Type: 1
	Opaque ID: 10
	Advertising Router: 1.1.1.1
	LS Seq Number: 80000023
	Checksum: 0x5613
	Length: 176

	    Link Type : Point-to-Point
	    Link ID : Neighbor Router-id 8.8.8.8
	    Interface Address : 10.1.18.1
	    Neighbor Address : 10.1.18.8
	    TE Metric : 10
	    Maximum bandwidth : 125000000 Bps
	    Maximum reservable bandwidth global: 1250000 Bps
	    Number of Priority : 8
		  Priority 0 :              1250000 Bps  Priority 1 :              1250000 Bps
		  Priority 2 :              1250000 Bps  Priority 3 :              1250000 Bps
		  Priority 4 :              1250000 Bps  Priority 5 :              1250000 Bps
		  Priority 6 :              1250000 Bps  Priority 7 :              1156250 Bps
	    Admin Group : 0x0
	    IGP Metric : 10
	    GMPLS Shared Risked Link Group :
	      Number of SRLGs (1)
	        [1]: 234
	    Administrative Group: 0


	dnRouter# show ospf instance instance1 database opaque-area self-originate

	Ospf Instance instance1

            OSPF Router with ID (1.1.1.1)

                Type-10 Opaque Link Area Link States (Area 0)

	LS age: 363
	Options: (No TOS-capability, DC)
	LS Type: Opaque Area Router
	Link State ID: 1.0.0.0
	Opaque Type: 1
	Opaque ID: 0
	Advertising Router: 1.1.1.1
	LS Seq Number: 80000098
	Checksum: 0x2969
	Length: 28
	Router Address TLV:
	  MPLS TE router ID : 1.1.1.1


	LS age: 1352
	Options: (No TOS-capability, DC)
	LS Type: Opaque Area Link
	Link State ID: 1.0.0.4
	Opaque Type: 1
	Opaque ID: 4
	Advertising Router: 1.1.1.1
	LS Seq Number: 80000098
	Checksum: 0x71c3
	Length: 176

	    Link Type : Point-to-Point
	    Link ID : Neighbor Router-id 2.2.2.2
	    Interface Address : 10.1.12.1
	    Neighbor Address : 10.1.12.2
	    TE Metric : 3
	    Maximum bandwidth : 125000000 Bps
	    Maximum reservable bandwidth global: 0 Bps
	    Number of Priority : 8
		  Priority 0 :                    0 Bps  Priority 1 :                    0 Bps
		  Priority 2 :                    0 Bps  Priority 3 :                    0 Bps
		  Priority 4 :                    0 Bps  Priority 5 :                    0 Bps
 		  Priority 6 :                    0 Bps  Priority 7 :                    0 Bps
	    Admin Group : 0x0
	    IGP Metric : 3
	    GMPLS Shared Risked Link Group :
	      Number of SRLGs (2)
        	[1]: 123
        	[2]: 435
	    Administrative Group: 0


	LS age: 1352
	Options: (No TOS-capability, DC)
	LS Type: Opaque Area Link
	Link State ID: 1.0.0.6
	Opaque Type: 1
	Opaque ID: 6
	Advertising Router: 1.1.1.1
	LS Seq Number: 80000026
	Checksum: 0x1c6d
	Length: 176

	    Link Type : Point-to-Point
	    Link ID : Neighbor Router-id 4.4.4.4
	    Interface Address : 10.1.14.1
	    Neighbor Address : 10.1.14.4
	    TE Metric : 10
	    Maximum bandwidth : 125000000 Bps
	    Maximum reservable bandwidth global: 0 Bps
	    Number of Priority : 8
		  Priority 0 :                    0 Bps  Priority 1 :                    0 Bps
		  Priority 2 :                    0 Bps  Priority 3 :                    0 Bps
		  Priority 4 :                    0 Bps  Priority 5 :                    0 Bps
 		  Priority 6 :                    0 Bps  Priority 7 :                    0 Bps
	    Admin Group : 0x0
	    IGP Metric : 10
	    GMPLS Shared Risked Link Group :
	      Number of SRLGs (1)
		    [1]: 123
	    Administrative Group: 0


	LS age: 75
	Options: (No TOS-capability, DC)
	LS Type: Opaque Area Link
	Link State ID: 1.0.0.10
	Opaque Type: 1
	Opaque ID: 10
	Advertising Router: 1.1.1.1
	LS Seq Number: 80000023
	Checksum: 0x5613
	Length: 176

	    Link Type : Point-to-Point
	    Link ID : Neighbor Router-id 8.8.8.8
	    Interface Address : 10.1.18.1
	    Neighbor Address : 10.1.18.8
	    TE Metric : 10
	    Maximum bandwidth : 125000000 Bps
	    Maximum reservable bandwidth global: 1250000 Bps
	    Number of Priority : 8
		  Priority 0 :              1250000 Bps  Priority 1 :              1250000 Bps
		  Priority 2 :              1250000 Bps  Priority 3 :              1250000 Bps
		  Priority 4 :              1250000 Bps  Priority 5 :              1250000 Bps
		  Priority 6 :              1250000 Bps  Priority 7 :              1156250 Bps
	    Admin Group : 0x0
	    IGP Metric : 10
	    GMPLS Shared Risked Link Group :
	      Number of SRLGs (1)
	        [1]: 234
	    Administrative Group: 0


	dnRouter# show ospf database opaque-link self-originate

	Ospf Instance instance1

            OSPF Router with ID (1.1.1.1)

	        Link-Local Opaque-LSA (Area 0.0.0.0)

	LS age: 7
	Options: (No TOS-capability, DC)
	LS Type: Opaque Link-Local Link (Interface: Gi0/0/0/3)
	Link State ID: 3.0.0.0
	Opaque Type: 3
	Opaque ID: 0
	Advertising Router: 4.4.4.4
	LS Seq Number: 80000001
	Checksum: 0x8307
	Length: 44
	Grace period       : 240 seconds
	Restart reason     : Software reload/upgrade
	IP Address         : 10.4.33.4

	LS age: 7
	Options: (No TOS-capability, DC)
	LS Type: Opaque Link-Local Link (Interface: Gi0/0/0/5)
	Link State ID: 3.0.0.0
	Opaque Type: 3
	Opaque ID: 0
	Advertising Router: 4.4.4.4
	LS Seq Number: 80000001
	Checksum: 0x9513
	Length: 44
	Grace period       : 240 seconds
	Restart reason     : Software reload/upgrade
	IP Address         : 10.1.6.4


	dnRouter# show ospf instance instance1 database opaque-link self-originate

	Ospf Instance instance1

            OSPF Router with ID (1.1.1.1)

	        Link-Local Opaque-LSA (Area 0.0.0.0)

	LS age: 7
	Options: (No TOS-capability, DC)
	LS Type: Opaque Link-Local Link (Interface: Gi0/0/0/3)
	Link State ID: 3.0.0.0
	Opaque Type: 3
	Opaque ID: 0
	Advertising Router: 4.4.4.4
	LS Seq Number: 80000001
	Checksum: 0x8307
	Length: 44
	Grace period       : 240 seconds
	Restart reason     : Software reload/upgrade
	IP Address         : 10.4.33.4

	LS age: 7
	Options: (No TOS-capability, DC)
	LS Type: Opaque Link-Local Link (Interface: Gi0/0/0/5)
	Link State ID: 3.0.0.0
	Opaque Type: 3
	Opaque ID: 0
	Advertising Router: 4.4.4.4
	LS Seq Number: 80000001
	Checksum: 0x9513
	Length: 44
	Grace period       : 240 seconds
	Restart reason     : Software reload/upgrade
	IP Address         : 10.1.6.4

	dnRouter# show ospf database opaque-area adv-router 2.2.2.2

	Ospf Instance instance1

       OSPF Router with ID (1.1.1.1)


                Type-10 Opaque Link Area Link States (Area 0.0.0.0)

  LS age: 101
  Options: 0x42 : *|-|O|-|-|-|-|E|-|*  (O, External Routing)
  LS Flags: 0x6
  LS Type: Opaque Area LSA
  Link State ID: 4.0.0.0
  Advertising Router: 2.2.2.2
  LS Seq Number: 80000001
  Checksum: 0x0f77
  Length: 76
  Opaque Type: 4
  Opaque ID: 0
  Router Capabilities: 0x10000000
  Segment Routing Algorithm TLV:
    Algorithm 0: SPF
    Algorithm 1: Strict SPF
  Segment Routing Global Range TLV:
    Range Size = 8000
    SID Label = 16000

  Segment Routing Local Range TLV:
    Range Size = 8000
    SID Label = 8000

  Node MSD TLV:
    Type: 1, Value: 9

  LS age: 4
  Options: 0x42 : *|-|O|-|-|-|-|E|-|*  (O, External Routing)
  LS Flags: 0x106
  LS Type: Opaque Area LSA
  Link State ID: 7.0.0.1
  Advertising Router: 2.2.2.2
  LS Seq Number: 80000002
  Checksum: 0xa63e
  Length: 56
  Opaque Type: 7
  Opaque ID: 1
  Extended Prefix TLV: Length 28
        Route Type: 1
        Address Family: 0x0
        Flags: A:0, N:1
        Address: 2.2.2.2/32
  Prefix SID Sub-TLV: Length 8
        Algorithm: 0
        Flags: NP:0, M:0, E:0, V:0, L:0
        MT-ID: 0x0
        Index: 2
  Prefix SID Sub-TLV: Length 8
        Algorithm: 1
        Flags: NP:1, M:0, E:1, V:0, L:0
        MT-ID: 0x0
        Index: 22

  LS age: 101
  Options: 0x42 : *|-|O|-|-|-|-|E|-|*  (O, External Routing)
  LS Flags: 0x6
  LS Type: Opaque Area LSA
  Link State ID: 8.0.0.2
  Advertising Router: 2.2.2.2
  LS Seq Number: 80000001
  Checksum: 0x0451
  Length: 56
  Opaque Type: 8
  Opaque ID: 2
  Extended Link TLV: Length 32
        Link Type: Point-to-Point
        Link ID: 1.1.1.1
        Link data: 12.1.1.2
  Adj-SID Sub-TLV: Length 7
        Flags: B:0 V:1 L:1 G:0 P:0
        MT-ID: 0x0
        Weight: 0x0
        Label: 8000
  Remote Interface Address Sub-TLV: Length 4
        Address: 12.1.1.1

  LS age: 101
  Options: 0x42 : *|-|O|-|-|-|-|E|-|*  (O, External Routing)
  LS Flags: 0x6
  LS Type: Opaque Area LSA
  Link State ID: 8.0.0.4
  Advertising Router: 2.2.2.2
  LS Seq Number: 80000001
  Checksum: 0xe54c
  Length: 56
  Opaque Type: 8
  Opaque ID: 4
  Extended Link TLV: Length 32
        Link Type: Point-to-Point
        Link ID: 3.3.3.3
        Link data: 23.1.1.2
  Adj-SID Sub-TLV: Length 7
        Flags: B:0 V:1 L:1 G:0 P:0
        MT-ID: 0x0
        Weight: 0x0
        Label: 8001
  Remote Interface Address Sub-TLV: Length 4
        Address: 23.1.1.3


	dnRouter# show ospf instance instance1 database opaque-area adv-router 2.2.2.2

	Ospf Instance instance1

       OSPF Router with ID (1.1.1.1)


                Type-10 Opaque Link Area Link States (Area 0.0.0.0)

  LS age: 101
  Options: 0x42 : *|-|O|-|-|-|-|E|-|*  (O, External Routing)
  LS Flags: 0x6
  LS Type: Opaque Area LSA
  Link State ID: 4.0.0.0
  Advertising Router: 2.2.2.2
  LS Seq Number: 80000001
  Checksum: 0x0f77
  Length: 76
  Opaque Type: 4
  Opaque ID: 0
  Router Capabilities: 0x10000000
  Segment Routing Algorithm TLV:
    Algorithm 0: SPF
    Algorithm 1: Strict SPF
  Segment Routing Global Range TLV:
    Range Size = 8000
    SID Label = 16000

  Segment Routing Local Range TLV:
    Range Size = 8000
    SID Label = 8000

  Segment Routing MSD TLV:
    Node Maximum Stack Depth = 6

  LS age: 4
  Options: 0x42 : *|-|O|-|-|-|-|E|-|*  (O, External Routing)
  LS Flags: 0x106
  LS Type: Opaque Area LSA
  Link State ID: 7.0.0.1
  Advertising Router: 2.2.2.2
  LS Seq Number: 80000002
  Checksum: 0xa63e
  Length: 56
  Opaque Type: 7
  Opaque ID: 1
  Extended Prefix TLV: Length 28
        Route Type: 1
        Address Family: 0x0
        Flags: A:0, N:1
        Address: 2.2.2.2/32
  Prefix SID Sub-TLV: Length 8
        Algorithm: 0
        Flags: NP:0, M:0, E:0, V:0, L:0
        MT-ID: 0x0
        Index: 2
  Prefix SID Sub-TLV: Length 8
        Algorithm: 1
        Flags: NP:1, M:0, E:1, V:0, L:0
        MT-ID: 0x0
        Index: 22

  LS age: 101
  Options: 0x42 : *|-|O|-|-|-|-|E|-|*  (O, External Routing)
  LS Flags: 0x6
  LS Type: Opaque Area LSA
  Link State ID: 8.0.0.2
  Advertising Router: 2.2.2.2
  LS Seq Number: 80000001
  Checksum: 0x0451
  Length: 56
  Opaque Type: 8
  Opaque ID: 2
  Extended Link TLV: Length 32
        Link Type: Point-to-Point
        Link ID: 1.1.1.1
        Link data: 12.1.1.2
  Adj-SID Sub-TLV: Length 7
        Flags: B:0 V:1 L:1 G:0 P:0
        MT-ID: 0x0
        Weight: 0x0
        Label: 8000
  Remote Interface Address Sub-TLV: Length 4
        Address: 12.1.1.1

  LS age: 101
  Options: 0x42 : *|-|O|-|-|-|-|E|-|*  (O, External Routing)
  LS Flags: 0x6
  LS Type: Opaque Area LSA
  Link State ID: 8.0.0.4
  Advertising Router: 2.2.2.2
  LS Seq Number: 80000001
  Checksum: 0xe54c
  Length: 56
  Opaque Type: 8
  Opaque ID: 4
  Extended Link TLV: Length 32
        Link Type: Point-to-Point
        Link ID: 3.3.3.3
        Link data: 23.1.1.2
  Adj-SID Sub-TLV: Length 7
        Flags: B:0 V:1 L:1 G:0 P:0
        MT-ID: 0x0
        Weight: 0x0
        Label: 8001
  Remote Interface Address Sub-TLV: Length 4
        Address: 23.1.1.3

.. **Help line:** Displays the link state database for OSPF

**Command History**

+---------+-----------------------------------------------+
| Release | Modification                                  |
+=========+===============================================+
| 11.6    | Command introduced                            |
+---------+-----------------------------------------------+
| 17.0    | Added example for segment-routing information |
+---------+-----------------------------------------------+
| 18.2    | Added instance parameter                      |
+---------+-----------------------------------------------+
