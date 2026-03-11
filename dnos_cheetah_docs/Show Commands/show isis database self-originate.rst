show isis database self-originate
---------------------------------

**Minimum user role:** viewer

To display self-originated LSPs (from the local router):

**Command syntax: show isis** instance [isis-instance-name] **database self-originate** level [level] {detail | verbose}

**Command mode:** operational


..
	**Note**

	- use "instance [isis-instance-name]" to display information from a specific ISIS instance, when now specified, display information from all isis instances

**Parameter table**

+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------+---------+---------------+
| Parameter          | Description                                                                                                                               | Range   | Default       |
+====================+===========================================================================================================================================+=========+===============+
| isis-instance-name | Displays information from a specific IS-IS instance. If you do not specify an instance, information from all instances will be displayed. | \-      | All instances |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------+---------+---------------+
| level              | Filters the database information displayed to a specific level.                                                                           | level-1 | Both levels   |
|                    |                                                                                                                                           | level-2 |               |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------+---------+---------------+
| detail             | Displays detailed information on the self-originated LSPs.                                                                                | \-      | \-            |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------+---------+---------------+
| verbose            | Displays verbose (including TLV and SubTLV code and length) information on the self-originated LSPs.                                      | \-      | \-            |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------+---------+---------------+

**Example**
::

	dnRouter# # show isis database self-originate

	Legend: ATT - Attached-bit, P - P-bit, OL - Overload-bit

	Instance DT:
	System-id: 0000.1234.8888
	IS-IS Level-2 link-state database:
	LSP ID                                PduLen  SeqNumber   Chksum  LSP Holdtime  ATT/P/OL
	Bert-SA.00-00                       * 506     0x0000143f  0x43da  364           0/0/0
	Bert-SA.00-01                       * 511     0x00001433  0xfb75  364           0/0/0
	Bert-SA.00-02                       * 499     0x0000021f  0x6310  364           0/0/0
	Bert-SA.00-03                       * 499     0x0000021d  0x55ab  364           0/0/0
	Bert-SA.00-04                       * 499     0x0000021d  0xe8d5  364           0/0/0
	Bert-SA.00-05                       * 499     0x0000021c  0x7efe  364           0/0/0
	Bert-SA.00-06                       * 162     0x0000022b  0x9aa5  364           0/0/0



	dnRouter# show isis database self-originate detail

	Legend: ATT - Attached-bit, P - P-bit, OL - Overload-bit

	Instance DT:
	System-id: 0000.1234.8888
	IS-IS Level-2 link-state database:
	LSP ID                                PduLen  SeqNumber   Chksum  LSP Holdtime  ATT/P/OL
	Bert-SA.00-00                       * 506     0x0000143f  0x43da  449           0/0/0
	  Protocols Supported: IPv4, IPv6
	  Area Address: 47.0001
	  MT Router Info: ipv4-unicast
	  MT Router Info: ipv6-unicast
	  Hostname: Bert-SA
	  TE Router ID: 5.5.5.5
	  Router Capability: 5.5.5.5 , D:0, S:0
	    Segment Routing: I:1 V:0, SRGB Base: 56990 Range: 5000
	      SRLB Base: 8000 Range: 8000
	      Algorithm: 0: SPF
	      Node MSD: 5
	  Extended Reachability: 1111.1111.1140.00 (Metric: 10)
	    Local Interface IP Address(es): 12.12.0.1
	    Remote Interface IP Address(es): 12.12.0.2
	    Adjacency-SID: 8143, Weight: 0, Flags: F:0 B:0, V:1, L:1, S:0, P:0
	  Extended Reachability: 1111.1111.1140.00 (Metric: 10)
	    Local Interface IP Address(es): 12.13.0.1
	    Remote Interface IP Address(es): 12.13.0.2
	    Adjacency-SID: 8137, Weight: 0, Flags: F:0 B:0, V:1, L:1, S:0, P:0
	  Extended Reachability: 1111.1111.1114.00 (Metric: 10)
	    Local Interface IP Address(es): 18.0.0.5
	    Remote Interface IP Address(es): 18.0.0.1
	    Administrative Group: 0x0
	    Maximum Bandwidth: 100000000 Kbps
	    Maximum Reservable Bandwidth: 75000000 Kbps
	    Unreserved Bandwidth:
	      [0]: 75000000 Kbps,	[1]: 75000000 Kbps
	      [2]: 75000000 Kbps,	[3]: 75000000 Kbps
	      [4]: 75000000 Kbps,	[5]: 75000000 Kbps
	      [6]: 75000000 Kbps,	[7]: 75000000 Kbps
	    Traffic Engineering Metric: 10
	    Adjacency-SID: 8139, Weight: 0, Flags: F:0 B:0, V:1, L:1, S:0, P:0
	  Extended Reachability: 1111.1111.1114.00 (Metric: 10)
	    Local Interface IP Address(es): 19.0.0.5
	    Remote Interface IP Address(es): 19.0.0.1
	    Administrative Group: 0x0
	    Maximum Bandwidth: 100000000 Kbps
	    Maximum Reservable Bandwidth: 75000000 Kbps
	    Unreserved Bandwidth:
	      [0]: 75000000 Kbps,       [1]: 75000000 Kbps
	      [2]: 75000000 Kbps,       [3]: 75000000 Kbps
	      [4]: 75000000 Kbps,       [5]: 75000000 Kbps
	      [6]: 75000000 Kbps,       [7]: 75000000 Kbps
	    Traffic Engineering Metric: 10
	    Adjacency-SID: 8144, Weight: 0, Flags: F:0 B:0, V:1, L:1, S:0, P:0
	  Extended Reachability: 1111.1111.1112.00 (Metric: 10)
	    Local Interface IP Address(es): 20.0.0.5
	    Remote Interface IP Address(es): 20.0.0.32
	    Administrative Group: 0x0
	    Maximum Bandwidth: 100000000 Kbps
	    Maximum Reservable Bandwidth: 75000000 Kbps
	    Unreserved Bandwidth:
	      [0]: 75000000 Kbps,       [1]: 75000000 Kbps
	      [2]: 75000000 Kbps,       [3]: 75000000 Kbps
	      [4]: 75000000 Kbps,       [5]: 75000000 Kbps
	      [6]: 75000000 Kbps,       [7]: 75000000 Kbps
	    Traffic Engineering Metric: 10
	    Adjacency-SID: 8145, Weight: 0, Flags: F:0 B:0, V:1, L:1, S:0, P:0
	  Extended Reachability: 1111.1111.1112.00 (Metric: 10)
	    Local Interface IP Address(es): 21.0.0.5
	    Remote Interface IP Address(es): 21.0.0.32
	    Administrative Group: 0x0
	    Maximum Bandwidth: 100000000 Kbps
	    Maximum Reservable Bandwidth: 75000000 Kbps
	    Unreserved Bandwidth:
	      [0]: 75000000 Kbps,       [1]: 75000000 Kbps
	      [2]: 75000000 Kbps,       [3]: 75000000 Kbps
	      [4]: 75000000 Kbps,       [5]: 75000000 Kbps
	      [6]: 75000000 Kbps,       [7]: 75000000 Kbps
	    Traffic Engineering Metric: 10
	    Adjacency-SID: 8141, Weight: 0, Flags: F:0 B:0, V:1, L:1, S:0, P:0


	dnRouter# show isis database self-originate verbose

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

+---------+---------------------------------------------------------------------------------------------+
| Release | Modification                                                                                |
+=========+=============================================================================================+
| 10.0    | Command introduced                                                                          |
+---------+---------------------------------------------------------------------------------------------+
| 14.0    | Added support for level-1-2 to the syntax. Added segment routing information in the output. |
+---------+---------------------------------------------------------------------------------------------+
| 19.2    | Added support for verbose display option.                                                   |
+---------+---------------------------------------------------------------------------------------------+

