show interfaces counters
------------------------

**Minimum user role:** viewer

This command displays L2 and L3 forwarding and error statistics. If you specify an interface name, the output result is filtered to show only the information for the requested interface.

**Command syntax: show interfaces counters** [interface-name]

**Command mode:** operational

**Note**

- The command is applicable to the following interface types:

	- Physical

	- Physical vlan

	- Bundle

	- Bundle vlan

	- sge

	- nat

	- IRB

..
	**Internal Note**

	- If specified interace-name is bundle interface, a summary table of counters per each bundle member is presented as follows:

	- RX [Mbps]: derived from Ethernet counter "RX octets"

	- TX [Mbps]: derived from Ethernet counter "TX octets"

	- RX [pkts]: derived from Ethernet counter "RX frames"

	- TX [pkts]: derived from Ethernet counter "TX frames"

	- RX drops [pkts]: sum of the following:

	- Forwarding drop counter "RX drops"

	- Ethernet drop counters "RX errors"

	- Ethernet drop counters "RX too short"

	- TX drops [pkts]: sum of the following:

	- Forwarding drop counter "TX drops"

	- Ethernet drop counters "TX errors"

	- If no interface-name is specified a summary table is presented for all L3 interfaces (with IP address), except loopback and GRE

	- Summary table does not include non-L3 interfaces

	- If no interface-name is specified a summary table is presented for all L3 interfaces (with IP address), except loopback and GRE

	- Summary table does not include non-L3 interfaces

	- A summary table presents the following counters per logical interfaces:

	- RX [Mbps]

	- for physical interface the value is derived from Ethernet counter "RX octets"

	- for sub-interfaces the value is derived from forwarding counter "RX octets"

	- TX [Mbps]

	- for physical interface the value is derived from Ethernet counter "TX octets"

	- for sub-interfaces the value is derived from forwarding counter "TX octets"

	- RX [pkts]

	- for physical interface the value is [Mfps] derived from Ethernet counter "RX frames"

	- for sub-interface the value derived from forwarding counter "RX packets"

	- TX [pkts]

	- for physical interface the value is [Mfps] derived from Ethernet counter "TX frames"

	- for sub-interface the value derived from forwarding counter "TX packets"

	- RX drops [pkts]

	- for physical interface the value is sum of the following:

	- Forwarding drop counter "RX drops"

	- Ethernet drop counters "RX errors"

	- Ethernet drop counters "RX too short"

	- for sub-interface the value is equal to forwarding drop counter "RX drops"

	- TX drops [pkts] - for physical interface the value is sum of the following:

	- for physical interface the value is sum of the following:

	- Forwarding drop counter "TX drops"

	- Ethernet drop counters "TX errors"

	- for sub-interface the value is equal to forwarding drop counter "TX drops"

**Parameter table**

+----------------+---------------------------------------------------------+---------------------------------------+---------+
| Parameter      | Description                                             | Range                                 | Default |
+================+=========================================================+=======================================+=========+
| interface-name | Optionally filter the counters to a specific interface. | geX-<f>/<n>/<p>.<sub-interface id>    | \-      |
|                |                                                         | ge<interface speed>-<A>/<B>/<C>       |         |
|                |                                                         | bundle-<bundle id>                    |         |
|                |                                                         | bundle-<bundle id>.<sub-interface id> |         |
|                |                                                         | irb<irb id>                           |         |
|                |                                                         | sge<interface speed>-<A>/<B>/<C>      |         |
|                |                                                         | nat-<nat id>                          |         |
+----------------+---------------------------------------------------------+---------------------------------------+---------+

The following information is displayed per interface:

+-----------------+-------------------------------------------------------------------------------------+
| Attribute       | Description                                                                         |
+=================+=====================================================================================+
| Interface       | The name of the interface                                                           |
+-----------------+-------------------------------------------------------------------------------------+
| Operational     | The state of the link (up/down)                                                     |
+-----------------+-------------------------------------------------------------------------------------+
| Rx (Mbps)       | The received Megabits per second:                                                   |
|                 | For physical interfaces, the value is derived from the “RX octets” Ethernet counter |
|                 | For sub-interfaces, the value is derived from the “RX octets” Forwarding counter    |
+-----------------+-------------------------------------------------------------------------------------+
| Tx (Mbps)       | The transmitted Megabits per second:                                                |
|                 | For physical interfaces, the value is derived from the “TX octets” Ethernet counter |
|                 | For sub-interfaces, the value is derived from the “TX octets” Forwarding counter    |
+-----------------+-------------------------------------------------------------------------------------+
| Rx (pkts)       | The received packets:                                                               |
|                 | For physical interfaces, the value is derived from the “RX frames” Ethernet counter |
|                 | For sub-interfaces, the value is derived from the “RX packets” Forwarding counter   |
+-----------------+-------------------------------------------------------------------------------------+
| Tx (pkts)       | The transmitted packets:                                                            |
|                 | For physical interfaces, the value is derived from the “TX frames” Ethernet counter |
|                 | For sub-interfaces, the value is derived from the “TX packets” Forwarding counter   |
+-----------------+-------------------------------------------------------------------------------------+
| Rx drops (pkts) | The number of received packets that were dropped:                                   |
|                 | For physical interfaces, the value is the sum of the following:                     |
|                 | Forwarding drops summary of logical and sub-IF “Total RX dropped”                   |
|                 | Ethernet “RX errors” drop counters                                                  |
|                 | Ethernet “RX too short” drop counters                                               |
|                 | For sub-interfaces, the value is equal to the “RX drops” Forwarding counter         |
+-----------------+-------------------------------------------------------------------------------------+
| Tx drops (pkts) | The number of transmitted packets that were dropped:                                |
|                 | For physical interfaces, the value is the sum of the following:                     |
|                 | Forwarding drops summary of logical and sub-IF “Total TX dropped”                   |
|                 | Ethernet “TX errors” drop counters                                                  |
|                 | For sub-interfaces, the value is equal to the “TX drops” Forwarding counter         |
+-----------------+-------------------------------------------------------------------------------------+

The following counters are displayed:

+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Counter                       | Description                                                                                                                                                           | Values         |
+===============================+=======================================================================================================================================================================+================+
| Ethernet counters:                                                                                                                                                                                    |                |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Rx octets                     | The number of Ethernet octets received (also in bits/Megabits per second)                                                                                             | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Rx frames                     | The number of Ethernet frames received (also in frames/Megaframes per second)                                                                                         | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Rx unicast frames             | The number of received Ethernet unicast frames (also in frames/Megaframes per second)                                                                                 | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Rx broadcast frames           | The number of received Ethernet broadcast frames (also in frames/Megaframes per second)                                                                               | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Rx multicast frames           | The number of received Ethernet multicast frames (also in frames/Megaframes per second)                                                                               | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Tx octets                     | The number of Ethernet octets transmitted (also in bits/Megabits per second)                                                                                          | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Tx frames                     | The number of Ethernet frames transmitted (also in frames/Megaframes per second)                                                                                      | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Tx unicast frames             | The number of transmitted Ethernet unicast frames (also in frames/Megaframes per second)                                                                              | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Tx broadcast frames           | The number of transmitted Ethernet broadcast frames (also in frames/Megaframes per second)                                                                            | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Tx multicast frames           | The number of transmitted Ethernet multicast frames (also in frames/Megaframes per second)                                                                            | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Ethernet control                                                                                                                                                                                      |                |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX pause frames               | The number of received Ethernet pause frames                                                                                                                          | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| TX pause frames               | The number of transmitted Ethernet pause frames                                                                                                                       | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX PFC frames                 | The number of received Ethernet PFC pause frames                                                                                                                      | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| TX PFC frames                 | The number of transmitted Ethernet PFC pause frames                                                                                                                   | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Ethernet drop counters:                                                                                                                                                                               |                |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Rx errors                     | The number of RX dropped Ethernet frames according to the ifInErrors counter (RFC2665)                                                                                | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX too short                  | The number of RX dropped Ethernet frames with a frame size less than 64 bytes                                                                                         | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX too long                   | The number of RX dropped Ethernet frames with a frame size exceeding MTU on the ingress interface                                                                     | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX FCS errors                 | The number of RX dropped Ethernet frames with FCS errors                                                                                                              | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX internal MAC errors        | The number of RX dropped Ethernet frames due to internal Ethernet MAC sublayer error                                                                                  | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX pipeline MAC drops         | The number of RX dropped Ethernet frames for any reason between MAC and RX Packet Processor pipeline                                                                  | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| TX errors                     | The number of TX dropped Ethernet frames according to the ifOutErrors counter (RFC2665)                                                                               | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| FEC counters:                                                                                                                                                                                         |                |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| FEC Corrected Errors          | The number of erred code words that were corrected by the FEC sublayer                                                                                                | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| FEC Uncorrected Errors        | The number of erred code words that were not corrected by the FEC sublayer                                                                                            | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| FEC symbol errors             | The number of Ethernet PHY RX symbol errors                                                                                                                           | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| FEC bit errors                | The number of Ethernet PHY RX bit errors                                                                                                                              | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Forwarding counters:                                                                                                                                                                                  |                |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX octets                     | The number of received octets                                                                                                                                         | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX packets                    | The number of received packets                                                                                                                                        | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| TX octets                     | The total number of octets that the device supplied to the lower layers for transmission. This includes packets generated locally and those forwarded by the device.  | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| TX packets                    | The total number of packets that the device supplied to the lower layers for transmission. This includes packets generated locally and those forwarded by the device. | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Forwarding drop counters: - refers to main interfaces only                                                                                                                                            |                |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX drops                      | The total number of received packets on the interface that were dropped for whatever reason.                                                                          | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| TX drops                      | The total number of forwarded or locally generated packets to the interface that were dropped for whatever reason.                                                    | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX TTL is too low             | The number of RX IP or MPLS packets that were dropped due to low TTL value (when TTL equals 1 or 0)                                                                   | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX MPLS label mismatch        | The number of RX MPLS packets that were dropped due to “mpls disabled” mode on an interface or because of an MPLS label mismatch in the ILM table                     | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX MPLS disabled              | The number of RX MPLS packet dropped due to "mpls disabled" mode on an interface                                                                                      | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Destination IF MTU is too low | The number of TX dropped packets with packet length that exceeds L3-MTU on the egress interface                                                                       | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Destination route unreachable | The number of RX IP dropped packets with a destination IP address that has no match in IP LPM table                                                                   | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Destination ARP unresolved    | The number of TX IP dropped packets with a destination IP address that has no match in ARP table                                                                      | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Destination route is null0    | The number of RX dropped IP packets because their route destination interface is Null0                                                                                | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Multicast lookup failure      | The number of RX dropped IP Multicast packets due to multicast forwarding lookup failure                                                                              | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Multicast wrong IIF           | The number of RX Multicast packets dropped due to arrival on an unexpected interface                                                                                  | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Control plane counters:                                                                                                                                                                               |                |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX control packets            | The total number of RX control plane packets                                                                                                                          | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Forwarding drops summary of all sub-IF: - refers to sub-interfaces only                                                                                                                               |                |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX VLAN mismatch              | The total number of RX dropped Ethernet frames with VLAN-ID that does not match any sub-if                                                                            | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Destination MAC mismatch      | The number of RX IP packets dropped because their destination MAC does not match the ingress interface                                                                | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Invalid IP header             | The number of RX IP packets dropped with invalid IP header values or invalid checksum                                                                                 | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX NOMBUF dropped packets     | The number of dropped packets since due to lack of memory for the RX queues. This counter is relevant only for SGE interfaces                                         | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Total RX dropped packets      | The total number of dropped packets for any reason in RX Packet Processor pipeline                                                                                    | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Total TX dropped packets      | The total number of dropped packets for any reason in TX Packet Processor pipeline                                                                                    | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| uRPF                                                                                                                                                                                                  |                |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Dropped packets               | The number of packets dropped due to uRPF ruling (per interface)                                                                                                      | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| MTU violation counters                                                                                                                                                                                |                |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| TX MTU violations             | The number of IPv6 and IPv4 packets with an MTU greater than the destination interface MTU (per interface). IPv4 packets with DF bit set and unset.                   | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| TX Ipv4 fragmented packets    | The number of IPv4 packets, for which the egress interface MTU was too low, and were fragmented (per interface)                                                       | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| TX generated Ipv4 fragments   | The number of IPv4 frame fragments sent to this interface (per interface)                                                                                             | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Interface Forwarding IP Multicast counters                                                                                                                                                            |                |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX IPv4 Multicast octets      | The number of received IPv4 Multicast octets (also in bits/Megabits per second)                                                                                       | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX IPv4 Multicast packets     | The number of received IPv4 Multicast packets (also in frames/Megaframes per second)                                                                                  | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+

The following information is not displayed in case interface is l2-service:

+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Counter                       | Description                                                                                                                                                           | Values         |
+===============================+=======================================================================================================================================================================+================+
| Forwarding drop counters: - refers to main interfaces only                                                                                                                                            |                |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX TTL is too low             | The number of RX IP or MPLS packets that were dropped due to low TTL value (when TTL equals 1 or 0)                                                                   | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX MPLS label mismatch        | The number of RX MPLS packets that were dropped due to “mpls disabled” mode on an interface or because of an MPLS label mismatch in the ILM table                     | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX MPLS disabled              | The number of RX MPLS packet dropped due to "mpls disabled" mode on an interface                                                                                      | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Destination IF MTU is too low | The number of TX dropped packets with packet length that exceeds L3-MTU on the egress interface                                                                       | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Destination route unreachable | The number of RX IP dropped packets with a destination IP address that has no match in IP LPM table                                                                   | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Destination ARP unresolved    | The number of TX IP dropped packets with a destination IP address that has no match in ARP table                                                                      | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Destination route is null0    | The number of RX dropped IP packets because their route destination interface is Null0                                                                                | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Multicast lookup failure      | The number of RX dropped IP Multicast packets due to multicast forwarding lookup failure                                                                              | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Multicast wrong IIF           | The number of RX Multicast packets dropped due to arrival on an unexpected interface                                                                                  | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Control plane counters:                                                                                                                                                                               |                |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX control packets            | The total number of RX control plane packets                                                                                                                          | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Forwarding drops summary of all sub-IF: - refers to sub-interfaces only                                                                                                                               |                |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX VLAN mismatch              | The total number of RX dropped Ethernet frames with VLAN-ID that does not match any sub-if                                                                            | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Destination MAC mismatch      | The number of RX IP packets dropped because their destination MAC does not match the ingress interface                                                                | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Invalid IP header             | The number of RX IP packets dropped with invalid IP header values or invalid checksum                                                                                 | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX NOMBUF dropped packets     | The number of dropped packets since due to lack of memory for the RX queues. This counter is relevant only for SGE interfaces                                         | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Total RX dropped packets      | The total number of dropped packets for any reason in RX Packet Processor pipeline                                                                                    | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Total TX dropped packets      | The total number of dropped packets for any reason in TX Packet Processor pipeline                                                                                    | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Storm Control dropped packets | The total number of dropped packets due to Storm Control Metering                                                                                                     | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| uRPF                                                                                                                                                                                                  |                |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Dropped packets               | The number of packets dropped due to uRPF ruling (per interface)                                                                                                      | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| MTU violation counters                                                                                                                                                                                |                |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| TX MTU violations             | The number of IPv6 and IPv4 packets with an MTU greater than the destination interface MTU (per interface). IPv4 packets with DF bit set and unset.                   | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| TX Ipv4 fragmented packets    | The number of IPv4 packets, for which the egress interface MTU was too low, and were fragmented (per interface)                                                       | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| TX generated Ipv4 fragments   | The number of IPv4 frame fragments sent to this interface (per interface)                                                                                             | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| Interface Forwarding IP Multicast counters                                                                                                                                                            |                |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX IPv4 Multicast octets      | The number of received IPv4 Multicast octets (also in bits/Megabits per second)                                                                                       | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+
| RX IPv4 Multicast packets     | The number of received IPv4 Multicast packets (also in frames/Megaframes per second)                                                                                  | 64-bit counter |
+-------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------+


The following tables summarizes the counters displayed per interface type:

+-----------------------------+-------------------------+------------------+-----+-----+------------+---------------------------+-----------------------------------------+---------------------------+-------------------------------------+
| IF Type                     | Ethernet/ Ethernet drop | Ethernet control | FEC | MAC | Forwarding | Forwarding drop / Control | Forwarding drops summary per LIF/sub-IF | MTU violation counters    | Forwarding IP Multicast counters    |
+=============================+=========================+==================+=====+=====+============+===========================+=========================================+===========================+=====================================+
| Physical without IP address | -                       | -                | -   | -   |            |                           | -                                       |                           |                                     |
+-----------------------------+-------------------------+------------------+-----+-----+------------+---------------------------+-----------------------------------------+---------------------------+-------------------------------------+
| Physical with IP address    | -                       | -                | -   | -   |            | -                         |                                         | -                         | -                                   |
+-----------------------------+-------------------------+------------------+-----+-----+------------+---------------------------+-----------------------------------------+---------------------------+-------------------------------------+
| Bundle without IP address   | -                       | -                | -   |     |            |                           | -                                       |                           |                                     |
+-----------------------------+-------------------------+------------------+-----+-----+------------+---------------------------+-----------------------------------------+---------------------------+-------------------------------------+
| Bundle with IP address      | -                       | -                | -   |     |            | -                         |                                         | -                         | -                                   |
+-----------------------------+-------------------------+------------------+-----+-----+------------+---------------------------+-----------------------------------------+---------------------------+-------------------------------------+
| Physical subinterface       |                         |                  |     |     | -          | -                         |                                         | -                         | -                                   |
+-----------------------------+-------------------------+------------------+-----+-----+------------+---------------------------+-----------------------------------------+---------------------------+-------------------------------------+
| Bundle subinterface         |                         |                  |     |     | -          | -                         |                                         | -                         | -                                   |
+-----------------------------+-------------------------+------------------+-----+-----+------------+---------------------------+-----------------------------------------+---------------------------+-------------------------------------+
| nat                         | -                       |                  |     |     |            |                           | -                                       |                           |                                     |
+-----------------------------+-------------------------+------------------+-----+-----+------------+---------------------------+-----------------------------------------+---------------------------+-------------------------------------+
| sge                         |                         |                  |     |     | -          | -                         |                                         |                           |                                     |
+-----------------------------+-------------------------+------------------+-----+-----+------------+---------------------------+-----------------------------------------+---------------------------+-------------------------------------+
| IRB                         |                         |                  |     |     | -          | -                         |                                         | -                         | -                                   |
+-----------------------------+-------------------------+------------------+-----+-----+------------+---------------------------+-----------------------------------------+---------------------------+-------------------------------------+

**Example**
::

	dnRouter# show interfaces counters

	| Interface    | Operational | RX[Mbps] | TX[Mbps] | RX[pkts] | TX[pkts] | RX drops[pkts] | TX drops[pkts] |
	+--------------+-------------+----------+----------+----------+----------+----------------+----------------|
	| ge100-1/0/1  | down        | 0        | 0        | 0        | 0        | 0              | 0              |
	| ge100-1/0/2.2| down        | 0        | 0        | 0        | 0        | 0              | 0              |
	| bundle-2     | down        | 0        | 0        | 0        | 0        | 0              | 0              |
	| bundle-3.200 | down        | 0        | 0        | 0        | 0        | 0              | 0              |
	| bundle-3.300 | down        | 0        | 0        | 0        | 0        | 0              | 0              |
	| bundle-2.333 | up          | 0        | 0        | 0        | 0        | 0              | 0              |
	| sge100-0/0/0 | up          | 0        | 0        | 0        | 0        | 0              | 0              |
	| sge100-0/1/0 | up          | 0        | 0        | 0        | 0        | 0              | 0              |
	| nat-0        | up          | 0        | 0        | 0        | 0        | 0              | 0              |
	| nat-1        | up          | 0        | 0        | 0        | 0        | 0              | 0              |
	| irb1         | up          | 0        | 0        | 0        | 0        | 0              | 0              |


	dnRouter# show interfaces counters ge100-1/1/1

	Interface ge100-1/1/1:
	Operational state: up

	Ethernet counters:
		RX octets:                      12345 (0 bps / 0 Mbps)
		RX frames:                      111   (0 fps / 0 Mfps)
		RX unicast frames:              111   (0 fps / 0 Mfps)
		RX broadcast frames:            111   (0 fps / 0 Mfps)
		RX multicast frames:            111   (0 fps / 0 Mfps)
		TX octets:                      24690 (0 bps / 0 Mbps)
		TX frames:                      222   (0 fps / 0 Mfps)
		TX unicast frames:              222   (0 fps / 0 Mfps)
		TX broadcast frames:            222   (0 fps / 0 Mfps)
		TX multicast frames:            222   (0 fps / 0 Mfps)

	Ethernet control counters:
		RX pause frames:                12
		TX pause frames:                3
		RX PFC frames:                  0
		TX PFC frames:                  0

	Ethernet drop counters:
		RX errors:                      130
		RX too short:                   45
		RX too long:                    5
		RX FCS errors:                  123
		RX internal MAC errors:         1
		RX pipeline MAC drops:          0
		TX errors:                      15

	FEC counters:
		FEC corrected errors:           1
		FEC uncorrected errors:         0
		FEC symbol errors:              2
		FEC bit errors:                 20

	Interface Forwarding IP Multicast counters:
		RX IPv4 Multicast octets:       123421 (0 bps / 0 Mbps)
		RX IPv4 Multicast packets:      111    (0 fps / 0 Mfps)

	Interface Forwarding drop counters:
		RX drops:                       225
		TX drops:                       6
		RX TTL is too low:              21
		RX MPLS label mismatch:         111
		RX MPLS disabled:               0
		Destination IF MTU is too low:  0
		Destination route unreachable:  0
		Destination MAC unresolved:     1
		Destination route is null0:     15
		Multicast lookup failure:       132
		Multicast wrong IIF:            3
		uRPF IPv4 drops:                0
		uRPF IPv6 drops:                0
		Storm Control Drops:            0

	MTU violation counters:
		TX MTU violations:              180
		TX IPv4 fragmented packets:     20
		TX generated IPv4 fragments:    63

	Forwarding drops summary of logical and sub-IF:
		RX VLAN mismatch:               222
		Destination MAC mismatch:       2
		Invalid IP header:              23
		Total RX dropped packets:       225
		Total TX dropped packets:       6


	dnRouter# show interfaces counters ge100-1/1/2.100

	Interface ge100-1/1/2.100:
	Operational state: up

	Interface forwarding counters:
		RX octets:                      12345 (0 bps / 0 Mbps)
		RX packets:                     111   (0 pps / 0 Mpps)
		TX octets:                      24690 (0 bps / 0 Mbps)
		TX packets:                     222   (0 pps / 0 Mpps)

	Interface Forwarding IP Multicast counters:
		RX IPv4 Multicast octets        0 (0 bps / 0 Mbps)
		RX IPv4 Multicast packets       0 (0 fps / 0 Mfps)

	Interface Forwarding drop counters:
		RX drops:                       225
		TX drops:                       6
		RX TTL is too low:              21
		RX MPLS label mismatch:         111
		RX MPLS disabled:               0
		Destination IF MTU is too low:  30
		Destination route unreachable:  0
		Destination MAC unresolved:     1
		Destination route is null0:     15
		Multicast lookup failure:       132
		Multicast wrong IIF:            3
		uRPF Ipv4 drops:                0
		uRPF Ipv6 drops:                0

	MTU violation counters:
		TX MTU violations:              30
		TX Ipv4 fragmented packets:     0
		TX generated Ipv4 fragments:    0


	dnRouter# show interfaces counters bundle-3

	Interface bundle-3:
	Operational state: up

	Ethernet counters:
		RX octets:                      12345 (0 bps / 0 Mbps)
		RX frames:                      111   (0 fps / 0 Mfps)
		RX unicast frames:              111   (0 fps / 0 Mfps)
		RX broadcast frames:            111   (0 fps / 0 Mfps)
		RX multicast frames:            111   (0 fps / 0 Mfps)
		TX octets:                      24690 (0 bps / 0 Mbps)
		TX frames:                      222   (0 fps / 0 Mfps)
		TX unicast frames:              222   (0 fps / 0 Mfps)
		TX broadcast frames:            222   (0 fps / 0 Mfps)
		TX multicast frames:            222   (0 fps / 0 Mfps)

	Ethernet control counters:
		RX pause frames:                12
		TX pause frames:                3
		RX PFC frames:                  0
		TX PFC frames:                  0

	Ethernet drop counters:
		RX errors:                      130
		RX too short:                   45
		RX too long:                    5
		RX FCS errors:                  123
		RX internal MAC errors:         1
		RX pipeline MAC drops:          0
		TX errors:                      15

	FEC counters:
		FEC corrected errors:           1
		FEC uncorrected errors:         0
		FEC symbol errors:              2
		FEC bit errors:                 20

	LInterface Forwarding IP Multicast counters:
		RX IPv4 Multicast octets        123421 (0 bps / 0 Mbps)
		RX IPv4 Multicast packets       111 (0 fps / 0 Mfps)

	Interface Forwarding drop counters:
		RX drops:                       225
		TX drops:                       6
		RX TTL is too low:              21
		RX MPLS label mismatch:         111
		RX MPLS disabled:               0
		Destination IF MTU is too low:  0
		Destination route unreachable   0
		Destination MAC unresolved:     1
		Destination route is null0:     15
		Multicast lookup failure:       132
		Multicast wrong IIF:            3
		uRPF IPv4 drops:                130
		uRPF IPv6 drops:                5

	MTU violation counters:
		TX MTU violations:              180
		TX IPv4 fragmented packets:     20
		TX generated IPv4 fragments:    63

	Forwarding drops summary of logical and sub-IF:
		RX VLAN mismatch:               222
		Destination MAC mismatch:       2
		Invalid IP header:              23
		Total RX dropped packets:       225
		Total TX dropped packets:       6

	Bundle Members:

	| Interface    | Operational   | RX[Mbps] | TX[Mbps] | RX[pkts] | TX[pkts] | RX drops[pkts] | TX drops[pkts] |
	+--------------+---------------+----------+----------+----------+----------+----------------+----------------|
	| ge100-1/0/20 | up (active)   | 0        | 0        | 0        | 0        | 0              | 0              |
	| ge100-1/0/21 | up (inactive) | 0        | 0        | 0        | 0        | 0              | 0              |
	| ge100-1/0/22 | down          | 0        | 0        | 0        | 0        | 0              | 0              |


	dnRouter# show interfaces counters sge100-0/0/0

	Interface sge100-0/0/0:
	Operational state: up

	Ethernet counters:
		RX octets:                      12345 (0 bps / 0 Mbps)
		RX frames:                      111   (0 fps / 0 Mfps)
		TX octets:                      24690 (0 bps / 0 Mbps)
		TX frames:                      222   (0 fps / 0 Mfps)

	Ethernet drop counters:
		RX errors:                      130
		RX too short:                   45
		RX too long:                    5
		RX FCS errors:                  123
		RX internal MAC errors:         1
		RX pipeline MAC drops:          0
		TX errors:                      15

	Forwarding drops summary of logical and sub-IF:
		RX VLAN mismatch:               222
		Invalid IP header:              23
		RX NOMBUF dropped packets:      2
		Total RX dropped packets:       225
		Total TX dropped packets:       6


	dnRouter# show interfaces counters nat-0

	Interface nat-0:
	Operational state: up

	Interface forwarding counters:
		RX octets:                      12345 (0 bps / 0 Mbps)
		RX packets:                     111   (0 pps / 0 Mpps)
		TX octets:                      24690 (0 bps / 0 Mbps)
		TX packets:                     222   (0 pps / 0 Mpps)

	Interface Forwarding drop counters:
		RX drops:                       225
		TX drops:                       6


	dnRouter# show interfaces counters bundle-3.200

	Interface bundle-3.200:
	Operational state: up

	Interface forwarding counters:
		RX octets:                      12345 (0 bps / 0 Mbps)
		RX packets:                     111   (0 pps / 0 Mpps)
		TX octets:                      24690 (0 bps / 0 Mbps)
		TX packets:                     222   (0 pps / 0 Mpps)

	Interface Forwarding IP Multicast counters:
		RX IPv4 Multicast octets        123421 (0 bps / 0 Mbps)
		RX IPv4 Multicast packets       111 (0 fps / 0 Mfps)

	Interface Forwarding drop counters:
		RX drops:                       225
		TX drops:                       6
		RX TTL is too low:              21
		RX MPLS label mismatch:         111
		RX MPLS disabled:               0
		Destination IF MTU is too low:  50
		Destination route unreachable:  0
		Destination MAC unresolved:     1
		Destination route is null0:     15
		Multicast lookup failure:       132
		Multicast wrong IIF:            3
		uRPF Ipv4 drops:                0
		uRPF Ipv6 drops:                0

	MTU violation counters:
		TX MTU violations:              50
		TX Ipv4 fragmented packets:     0
		TX generated Ipv4 fragments:    0


	dnRouter# show interfaces counters bundle-2.333

	Interface bundle-2.333:
	Operational state: up

	Interface forwarding counters:
		RX octets:                      12345 (0 bps / 0 Mbps)
		RX packets:                     111   (0 pps / 0 Mpps)
		TX octets:                      24690 (0 bps / 0 Mbps)
		TX packets:                     222   (0 pps / 0 Mpps)

	Interface Forwarding IP Multicast counters:
		RX IPv4 Multicast octets        123421 (0 bps / 0 Mbps)
		RX IPv4 Multicast packets       111 (0 fps / 0 Mfps)

	Interface Forwarding drop counters:
		RX drops:                       225
		TX drops:                       6
		RX TTL is too low:              0
		RX MPLS label mismatch:         0
		RX MPLS disabled:               0
		Destination IF MTU is too low:  5
		Destination route unreachable   0
		Destination MAC unresolved:     0
		Destination route is null0:     0
		Multicast lookup failure:       0
		Multicast wrong IIF:            0
		uRPF Ipv4 drops:                0
		uRPF Ipv6 drops:                0

	MTU violation counters:
		TX MTU violations:              5
		TX Ipv4 fragmented packets:     0
		TX generated Ipv4 fragments:    0


	dnRouter# show interfaces counters irb1

	Interface irb1:
	Operational state: up

	Interface forwarding counters:
		RX octets:                                        0 (   150278825 bps /  150.28 Mbps)
		RX packets:                                       0 (       25129 pps /    0.03 Mpps)
		TX octets:                                        0 (    13667047 bps /   13.67 Mbps)
		TX packets:                                       0 (        1423 pps /     0.0 Mpps)

	Interface forwarding IP Multicast counters:
		RX IPv4 Multicast octets:                         0 (           0 bps /       0 Mbps)
		RX IPv4 Multicast packets:                        0 (           0 pps /       0 Mpps)

	Interface forwarding drop counters:
		RX drops:                                         0
		TX drops:                                         0
		RX TTL is too low:                                0
		RX MPLS label mismatch:                           0
		RX MPLS disabled:                                 0
		Destination IF MTU is too low:                    0
		Destination route unreachable:                    0
		Destination MAC unresolved:                       0
		Destination route is null0:                       0
		Multicast lookup failure:                         0
		Multicast wrong IIF:                              0
		uRPF Ipv4 drops:                                  0
		uRPF Ipv6 drops:                                  0

	MTU violation counters:
		TX MTU violations:                                0
		TX IPv4 fragmented packets:                       0
		TX generated IPv4 fragments:                      0


	dnRouter# show interfaces counters ge100-0/0/0

	Interface ge100-0/0/0:
	Operational state: up
	L2-service state: enabled

	Ethernet counters:
		RX octets:                                        0 (           0 bps /       0 Mbps)
		RX frames:                                        0 (           0 fps /       0 Mfps)
		RX unicast frames:                                0 (           0 fps /       0 Mfps)
		RX broadcast frames:                              0 (           0 fps /       0 Mfps)
		RX multicast frames:                              0 (           0 fps /       0 Mfps)
		TX octets:                                      188 (           0 bps /       0 Mbps)
		TX frames:                                        2 (           0 fps /       0 Mfps)
		TX unicast frames:                                0 (           0 fps /       0 Mfps)
		TX broadcast frames:                              0 (           0 fps /       0 Mfps)
		TX multicast frames:                              2 (           0 fps /       0 Mfps)

	Ethernet control counters:
		RX pause frames:                                  0
		TX pause frames:                                  0
		RX PFC frames:                                    0
		TX PFC frames:                                    0

	Ethernet drop counters:
		RX errors:                                        0
		RX too short:                                     0
		RX too long:                                      0
		RX FCS errors:                                    0
		RX internal MAC errors:                           0
		RX pipeline MAC drops:                            0
		TX errors:                                        0

	FEC counters:
		FEC corrected errors:                             0
		FEC uncorrected errors:                           0
		FEC symbol errors:                                0
		FEC bit errors:                                   0

	Interface forwarding drops counters:
		RX drops:                        				  0
		TX drops:                        				  0

	dnRouter# show interfaces counters bundle-1117.1
	Interface bundle-1117.1:
	Operational state: up
	L2-service state: enabled

	Interface forwarding counters:
		RX octets:                                  2439316 (          64 bps /     0.0 Mbps)
		RX packets:                                   35867 (           0 pps /       0 Mpps)
		TX octets:                                  5372346 (         142 bps /     0.0 Mbps)
		TX packets:                                   72579 (           0 pps /       0 Mpps)

	Interface forwarding drop counters:
		RX drops:                                         6
		TX drops:                                         0
		Destination IF MTU is too low:                    0


.. **Help line:** Displays counters for the interface(s)


**Command History**

+---------+----------------------------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                                               |
+=========+============================================================================================================================+
| 5.1.0   | Command introduced                                                                                                         |
+---------+----------------------------------------------------------------------------------------------------------------------------+
| 9.0     | Removed unsupported counters                                                                                               |
+---------+----------------------------------------------------------------------------------------------------------------------------+
| 10.0    | Updated counters                                                                                                           |
+---------+----------------------------------------------------------------------------------------------------------------------------+
| 11.0    | Updated counters                                                                                                           |
+---------+----------------------------------------------------------------------------------------------------------------------------+
| 11.4    | Added RX MPLS disabled counter                                                                                             |
+---------+----------------------------------------------------------------------------------------------------------------------------+
| 12.0    | Renamed "L3 forwarding counters" to "Forwarding counters" and "L3 forwarding drop counters" to "Forwarding drop counters"  |
|         | Added "Rx Multicast disabled" and "Multicast lookup failure" counters                                                      |
+---------+----------------------------------------------------------------------------------------------------------------------------+
| 13.0    | Added uRPF drop counters                                                                                                   |
+---------+----------------------------------------------------------------------------------------------------------------------------+
| 13.1    | Added L3 MTU violation counters                                                                                            |
+---------+----------------------------------------------------------------------------------------------------------------------------+
| 15.0    | Added L3 Forwarding IP Multicast counters                                                                                  |
+---------+----------------------------------------------------------------------------------------------------------------------------+
| 16.1    | Added rate to the ethernet unicast, multicast and broadcast counters, and to the L3 RX multicast counters                  |
+---------+----------------------------------------------------------------------------------------------------------------------------+
| 16.2    | Replaced RX multicast disabled counter with Multicast wrong IIF counter and aggregated drop reasons                        |
+---------+----------------------------------------------------------------------------------------------------------------------------+
| 16.2    | Added MAC to RX pipeline drop counter for physical interfaces                                                              |
+---------+----------------------------------------------------------------------------------------------------------------------------+
| 17.0    | Added total RX/TX PFC frames counters for physical and bundle interfaces                                                   |
+---------+----------------------------------------------------------------------------------------------------------------------------+
| 17.2    | Added a bit errors counter and moved symbol errors counter under FEC errors section                                        |
+---------+----------------------------------------------------------------------------------------------------------------------------+
| 18.0    | Added support for IRB interfaces                                                                                           |
+---------+----------------------------------------------------------------------------------------------------------------------------+
| 18.2    | Added SGE and NAT virtual interfaces                                                                                       |
+---------+----------------------------------------------------------------------------------------------------------------------------+
| 18.2    | Replaced any 'L3 forwarding' output with 'Interface forwarding'                                                            |
+---------+----------------------------------------------------------------------------------------------------------------------------+
| 18.2    | Remove irrelevant ip/mpls related counters from show output for cases interface is l2-service enabled                      |
+---------+----------------------------------------------------------------------------------------------------------------------------+