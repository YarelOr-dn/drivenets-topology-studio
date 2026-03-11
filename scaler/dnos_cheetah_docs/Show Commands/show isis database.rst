show isis database
------------------

**Minimum user role:** viewer

The show isis database command displays information related to the IS-IS database.



**Command syntax: show isis** instance [isis-instance-name] **database** lsp-id [lsp-id] level [level] {detail | verbose}

**Command mode:** operational


..
	**Internal Note**

	- use "instance [isis-instance-name]" to display information from a specific ISIS instance, when not specified, display information from all isis instances

	- lsp-id - The first six octets form the system ID

	- set [lsp-id] to show link state information for a specific LSP

	- set detail to display detailed information

	- set verbose to display verbose information (TLV and SubTLV code and length)

**Parameter table**

+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------+---------+---------------+
| Parameter          | Description                                                                                                                                       | Range   | Default       |
+====================+===================================================================================================================================================+=========+===============+
| No argument        | Displays concentric information relating to the IS-IS database                                                                                    | \-      | \-            |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------+---------+---------------+
| isis-instance-name | Displays database information for a specific IS-IS instance. If you do not specify an instance, information from all instances will be displayed  | String  | All instances |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------+---------+---------------+
| lsp-id             | Displays link state information for a specific LSP                                                                                                | String  | \-            |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------+---------+---------------+
| level              | Filters the database information displayed to a specific level                                                                                    | level-1 | Both levels   |
|                    |                                                                                                                                                   | level-2 |               |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------+---------+---------------+
| detail             | Display detailed information on the database                                                                                                      | \-      | \-            |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------+---------+---------------+
| verbose            | Display verbose (including TLV and SubTLV code and length) information on the LSP                                                                 | \-      | \-            |
+--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------+---------+---------------+

**Example**
::

	dnRouter# show isis database

	Legend: ATT - Attached-bit, P - P-bit, OL - Overload-bit

	Instance one:
	System-id: 1111.1111.1111
	IS-IS Level-2 link-state database:
	LSP ID                  PduLen  SeqNumber   Chksum LSP Holdtime  ATT/P/OL
	q1.00-00             *    255   0x0000006e  0x49ae     871       0/0/0
	q1.97-00             *     62   0x00000045  0x7c9f     879       0/0/0
	q2.00-00                  255   0x0000004b  0xbb7f     810       0/0/0
	q3.00-00                  255   0x00000049  0x0f94     824       0/0/0
	q4.00-00                  204   0x00000019  0x53d7     551       0/0/0
	    5 LSPs


	dnRouter# show isis database lsp-id q1.00-00

	Legend: ATT - Attached-bit, P - P-bit, OL - Overload-bit

	Instance one:
	System-id: 1111.1111.1111
	IS-IS Level-2 link-state database:
	LSP ID                  PduLen  SeqNumber   Chksum  LSP Holdtime  ATT/P/OL
	q1.00-00             *    255   0x0000006e  0x49ae     868        0/0/0


	dnRouter# show isis database detail

	Legend: ATT - Attached-bit, P - P-bit, OL - Overload-bit

	Instance one:
	System-id: 1111.1111.1111
	IS-IS Level-2 link-state database:
	LSP ID                  PduLen  SeqNumber   Chksum  LSP Holdtime  ATT/P/OL
	q1.00-00             *    255   0x0000006e  0x49ae     868        0/0/0
	Protocols Supported: IPv4, IPv6
	Area Address: 47.0001
	MT Router Info: ipv4-unicast
	MT Router Info: ipv6-unicast
	MT Router Info: ipv4-multicast
	Hostname: e2e_R1_1
	TE Router ID: 1.1.1.3
	Extended Reachability: 3333.3333.3333.00 (Metric: 10)
		Local Interface IP Address(es): 13.1.1.1
		Remote Interface IP Address(es): 13.1.1.3
		Administrative Group: 0x0
		Maximum Bandwidth: 8 Kbps
		Maximum Reservable Bandwidth: 8 Kbps
		Unreserved Bandwidth:
		[0]: 8 Kbps,	[1]: 8 Kbps
		[2]: 8 Kbps,	[3]: 8 Kbps
		[4]: 8 Kbps,	[5]: 8 Kbps
		[6]: 8 Kbps,	[7]: 8 Kbps
		Traffic Engineering Metric: 10
		Normal Average Link Delay: 33 (micro-sec)
		Normal Min/Max Link Delay: 23 / 53 (micro-sec)
		Delay Variation: 63 (micro-sec)
	Extended Reachability: 4444.4444.4444.00 (Metric: 10)
		Local Interface IP Address(es): 14.1.1.1
		Remote Interface IP Address(es): 14.1.1.4
		Administrative Group: 0x0
		Maximum Bandwidth: 8 Kbps
		Maximum Reservable Bandwidth: 8 Kbps
		Unreserved Bandwidth:
		[0]: 8 Kbps,	[1]: 8 Kbps
		[2]: 8 Kbps,	[3]: 8 Kbps
		[4]: 8 Kbps,	[5]: 8 Kbps
		[6]: 8 Kbps,	[7]: 8 Kbps
		Traffic Engineering Metric: 10
	Extended Reachability: 3333.3333.3333.00 (Metric: 10)
		Local Interface IP Address(es): 13.2.1.1
		Remote Interface IP Address(es): 13.2.1.3
		Administrative Group: 0x0
		Maximum Bandwidth: 8 Kbps
		Maximum Reservable Bandwidth: 8 Kbps
		Unreserved Bandwidth:
		[0]: 8 Kbps,	[1]: 8 Kbps
		[2]: 8 Kbps,	[3]: 8 Kbps
		[4]: 8 Kbps,	[5]: 8 Kbps
		[6]: 8 Kbps,	[7]: 8 Kbps
		Traffic Engineering Metric: 10
	MT Reachability: 3333.3333.3333.00 (Metric: 10) ipv6-unicast
		Normal Average Link Delay: 33 (micro-sec)
		Normal Min/Max Link Delay: 23 / 53 (micro-sec)
		Delay Variation: 63 (micro-sec)
	MT Reachability: 4444.4444.4444.00 (Metric: 10) ipv6-unicast
	MT Reachability: 3333.3333.3333.00 (Metric: 10) ipv6-unicast
	MT Reachability: 3333.3333.3333.00 (Metric: 10) ipv4-multicast
		Normal Average Link Delay: 33 (micro-sec)
		Normal Min/Max Link Delay: 23 / 53 (micro-sec)
		Delay Variation: 63 (micro-sec)
	MT Reachability: 4444.4444.4444.00 (Metric: 10) ipv4-multicast
	MT Reachability: 3333.3333.3333.00 (Metric: 10) ipv4-multicast
	IPv4 Interface Address: 1.1.1.3
	IPv4 Interface Address: 1.1.1.1
	Extended IP Reachability: 1.1.1.1/32 (Metric: 0)
	Extended IP Reachability: 13.1.1.0/24 (Metric: 10)
	Extended IP Reachability: 14.1.1.0/24 (Metric: 10)
	Extended IP Reachability: 13.2.1.0/24 (Metric: 10)
	MT IP Reachability: 1.1.1.1/32 (Metric: 0) ipv4-multicast
	MT IP Reachability: 13.1.1.0/24 (Metric: 10) ipv4-multicast
	MT IP Reachability: 14.1.1.0/24 (Metric: 10) ipv4-multicast
	MT IP Reachability: 13.2.1.0/24 (Metric: 10) ipv4-multicast


	dnRouter# show isis database verbose

	Legend: ATT - Attached-bit, P - P-bit, OL - Overload-bit

	Instance 1:
	System-id: 1111.1411.1111
	IS-IS Level-2 link-state database:
	LSP ID                                PduLen  SeqNumber   Chksum  LSP Holdtime  ATT/P/OL
	q4.00-00                            * 328     0x00000019  0x7994  861           0/0/0
	TLV code:129 length:2
		Protocols Supported: IPv4, IPv6
	TLV code:1 length:4
		Area Address: 47.0001
	TLV code:229 length:4
		MT Router Info: ipv4-unicast
		MT Router Info: ipv6-unicast
	TLV code:137 length:2
		Hostname: q4
	TLV code:134 length:4
		TE Router ID: 44.44.44.44
	TLV code:140 length:16
		IPv6 TE Router ID: 4444::4444
	TLV code:242 length:40
		Router Capability:   44.44.44.44 , D:0, S:0
			SubTLV code:2 length:9
				Segment Routing: I:1 V:1, SRGB Base: 16000 Range: 8000
			SubTLV code:19 length:2
				Algorithm: 0(spf) 1(strict-spf)
			SubTLV code:20 length:0
			SubTLV code:22 length:9
				SRLB Base: 8000 Range: 1000
			SubTLV code:23 length:2
				Node MSD: 9
			SubTLV code:24 length:1
				Mapping-Server Preference: 128
	TLV code:132 length:4
		IPv4 Interface Address: 44.44.44.44
	TLV code:232 length:16
		IPv6 Interface Address: 4444::4444
	TLV code:22 length:30
		Extended Reachability: 1111.1511.1111.00 (Metric: 10)
			SubTLV code:6 length:4
				Local Interface IP Address(es): 1.0.0.3
			SubTLV code:8 length:4
				Remote Interface IP Address(es): 1.0.0.4
			SubTLV code:31 length:5
				Adjacency-SID: 260, Weight: 0, Flags: F:0 B:0, V:1, L:1, S:0, P:0
	TLV code:222 length:56
		MT Reachability: 1111.1511.1111.00 (Metric: 10) ipv6-unicast
			SubTLV code:12 length:16
				Local Interface IPv6 Address(es): 2450::45
			SubTLV code:13 length:16
				Remote Interface IPv6 Address(es): 2450::54
			SubTLV code:31 length:5
				Adjacency-SID: 262, Weight: 0, Flags: F:1 B:0, V:1, L:1, S:0, P:0
	TLV code:135 length:28
		Extended IP Reachability: 3.0.0.0/24 (Metric: 10)
		Extended IP Reachability: 1.0.0.0/24 (Metric: 10)
		Extended IP Reachability: 44.44.44.44/32 (Metric: 0)
	TLV code:237 length:69
		MT IPv6 Reachability: 1230::/120 (Metric: 10) ipv6-unicast
		MT IPv6 Reachability: 2450::/120 (Metric: 10) ipv6-unicast
		MT IPv6 Reachability: 4444::4444/128 (Metric: 0) ipv6-unicast


**Command History**

+---------+--------------------------------------------+
| Release | Modification                               |
+=========+============================================+
| 6.0     | Command introduced                         |
+---------+--------------------------------------------+
| 14.0    | Added support for level-1-2 in the syntax  |
+---------+--------------------------------------------+
| 19.2    | Added support for verbose display option   |
+---------+--------------------------------------------+
