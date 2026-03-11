run packet-capture ncc
----------------------

**Command syntax: run packet-capture ncc { interface [interface-name] | in-band-vrf [non-default-inband-vrf] }** {file-name [file-name] rotation-file-size [rotation-file-size]| verbosity [verbosity]} count [count] filter-expression [filter-expression]

**Description:** Packet capture control traffic of active NCC

Packet capture is a tool that helps operators to analyze network traffic and troubleshoot network problems. The packet capture tool captures real-time control and management data packets for monitoring and logging.

Packet capture operates like traffic sampling on the device, except that it captures entire packets including the Layer 2 header and saves the contents to a file in pcap format. Packet capture also captures IP fragments

Use Ctrl+C to stop capture

* Interface - Specify the required interface over the NCC control plane for which packet capture will run. The following interfaces are supported:
    * In-Band interfaces:
		- ge<interface speed>-<A>/<B>/<C>- capture all Rx/Tx packets on physical port
		- geX-<f>/<n>/<p>.<sub-interface id> - capture all Rx/Tx packets on physical sub interface
		- bundle-<id> - capture all Rx/Tx packets on bundle interface
		- bundle-<id>.<vlan-id> - capture all Rx/Tx packets on sub bundle interface
		- gre-tunnel-<x> - capture all Rx/Tx packets on gre-tunnel interface
		- high-scale-vrf-<vrf-id> - <vrf-id> is per vrf id known by “show network services vrf”.
			This interface carries all L3VPN Rx traffic for a specific non-default vrf. L3VPN traffic is traffic received with vpn label and designated to local cpu ("for us") in non-default vrf.

			This interface carries all Tx traffic (i.e from NCC) of specific vrf that the destination doesn’t match a route installed NCC forwarding tables. Which is:

			* RSVP route installed to unicast table
			* ISIS unicast route resolved by tunnel
			* Static-route resolved via mpls
			* BGP routes
			* Route to null0
		- any - capture on all in-band control interfaces for all vrfs. Capture is expected to result in packet duplications as different control interfaces carries the same packets


    * Out-of-band interfaces:
        - mgmt0 - Cluster OOB management interface.
        - mgmt-ncc-0 - Physical NCC0 OOB mgmt port.
        - mgmt-ncc-1 - Physical NCC1 OOB mgmt port.

* in-band-vrf - capture all Tx/Rx traffic of a non-default in-band vrf

* file-name - When specified, write capture to file instead of printing to screen.
	* Files will be named file-name.file_number.pcap. where:
	* file-name - the user requested file name
	* file_number - The rotation file number of the requested capture. A rotated file is created once capture size exceed file-size, start with 1. The first captured file will not have .file_number

* rotation-file-size - maximum size of a single rotation of the captured pcap file. Can only be used when file-name is set.

* verbosity - when capture output is printed to terminal, select verbosity of displayed information - low, medium or high
	* Low - When parsing and printing, produce (slightly more) verbose output. For example, the time to live, identification, total length and options in an IP packet are printed. Also enables additional packet integrity checks such as verifying the IP and ICMP header checksum.
	* Medium - additional fields are printed from NFS reply packets, and SMB packets are fully decoded.
	* High - Example elnet SB ... SE options are printed in full
* count - Support limiting packet-capture duration using count. use "unlimited" value for no count limit

* filter-expressions - Linux string filter expressions. See https://www.tcpdump.org/manpages/pcap-filter.7.html


**CLI example:**
::

	dnRouter# run packet-capture ncc interface any verbosity low filter-expression 'tcp port 179'
	Listening on any, verbosity low, count 100000
	Type ctrl+c to abort

	15:57:45.103525 IP6 (class 0xc0, flowlabel 0xe6351, hlim 64, next-header TCP (6) payload length: 40) 2001:101::16.45585 > 2001:101:0:1::11f.bgp: Flags [S], cksum 0xbdeb (correct), seq 2986641117, win 36960, options [mss 9240,sackOK,TS val 873953361 ecr 0,nop,wscale 14], length 0
	15:57:45.103567 IP6 (class 0xc0, flowlabel 0xe6351, hlim 64, next-header TCP (6) payload length: 40) 2001:101::16.45585 > 2001:101:0:1::11f.bgp: Flags [S], cksum 0xbdeb (correct), seq 2986641117, win 36960, options [mss 9240,sackOK,TS val 873953361 ecr 0,nop,wscale 14], length 0
	15:57:45.103619 IP (tos 0xc0, ttl 64, id 60191, offset 0, flags [DF], proto TCP (6), length 60)
	    101.0.0.16.34637 > 101.0.1.115.bgp: Flags [S], cksum 0x397c (correct), seq 3375892311, win 37040, options [mss 9260,sackOK,TS val 470490934 ecr 0,nop,wscale 14], length 0
	15:57:45.103630 IP (tos 0xc0, ttl 64, id 60191, offset 0, flags [DF], proto TCP (6), length 60)
	    101.0.0.16.34637 > 101.0.1.115.bgp: Flags [S], cksum 0x397c (correct), seq 3375892311, win 37040, options [mss 9260,sackOK,TS val 470490934 ecr 0,nop,wscale 14], length 0
	15:57:45.103724 IP6 (class 0xc0, flowlabel 0x87c64, hlim 64, next-header TCP (6) payload length: 40) 2001:101::16.38689 > 2001:101:0:1::130.bgp: Flags [S], cksum 0x717d (correct), seq 1109688338, win 36960, options [mss 9240,sackOK,TS val 2186348560 ecr 0,nop,wscale 14], length 0
	15:57:45.103735 IP6 (class 0xc0, flowlabel 0x87c64, hlim 64, next-header TCP (6) payload length: 40) 2001:101::16.38689 > 2001:101:0:1::130.bgp: Flags [S], cksum 0x717d (correct), seq 1109688338, win 36960, options [mss 9240,sackOK,TS val 2186348560 ecr 0,nop,wscale 14], length 0
	15:57:45.103773 IP6 (class 0xc0, flowlabel 0x0c4cd, hlim 64, next-header TCP (6) payload length: 40) 2001:101::16.38145 > 2001:101:0:3::210.bgp: Flags [S], cksum 0x541a (correct), seq 323249823, win 36960, options [mss 9240,sackOK,TS val 4096392491 ecr 0,nop,wscale 14], length 0
	15:57:45.109344 IP (tos 0xc0, ttl 64, id 26854, offset 0, flags [DF], proto TCP (6), length 60)
	    101.0.0.16.44911 > 101.0.1.128.bgp: Flags [S], cksum 0x3547 (correct), seq 3978069164, win 37040, options [mss 9260,sackOK,TS val 1659376421 ecr 0,nop,wscale 14], length 0
	15:57:45.109357 IP (tos 0xc0, ttl 64, id 26854, offset 0, flags [DF], proto TCP (6), length 60)
	    101.0.0.16.44911 > 101.0.1.128.bgp: Flags [S], cksum 0x3547 (correct), seq 3978069164, win 37040, options [mss 9260,sackOK,TS val 1659376421 ecr 0,nop,wscale 14], length 0
	...



	dnRouter# run packet-capture ncc interface ge100-0/0/1 file-name BGP_Debug  filter-expression 'tcp port 179'
	Listening on ge100-0/0/1, writing to file BGP_Debug, rotation-size 50MB, count 100000
	Type ctrl+c to abort

	^C274 packets captured
	274 packets received by filter
	0 packets dropped by kernel

**Command mode:** operational

**TACACS role:** admin

**Note:**

-  hostname resolution is disabled by default
-  Can only capture on interfaces in Up state
-  Using the packet-capture command can degrade router performance
-  Use Ctrl+C to stop capture.

**Help line:** Packet capture control traffic of active NCC

**Parameter table:**

+------------------------+-------------------------------------------------------+-----------------------------------+
| Parameter              | Values                                                | Default value                     |
+========================+=======================================================+===================================+
| interface-name         | any                                                   |                                   |
|                        |                                                       |                                   |
|                        | ge<interface speed>-<A>/<B>/<C>                       |                                   |
|                        |                                                       |                                   |
|                        | ge<interface speed>-<A>/<B>/<C>.<sub-interface id>    |                                   |
|                        |                                                       |                                   |
|                        | bundle-<bundle id>                                    |                                   |
|                        |                                                       |                                   |
|                        | bundle-<bundle id>.<sub-interface id>                 |                                   |
|                        |                                                       |                                   |
|                        | gre-tunnel-<x>                                        |                                   |
|                        |                                                       |                                   |
|                        | high-scale-vrf-<vrf-id>                               |                                   |
|                        |                                                       |                                   |
|                        | mgmt0                                                 |                                   |
|                        |                                                       |                                   |
|                        | mgmt-ncc-0                                            |                                   |
|                        |                                                       |                                   |
|                        | mgmt-ncc-1                                            |                                   |
+------------------------+-------------------------------------------------------+-----------------------------------+
| non-default-inband-vrf | string                                                |                                   |
|                        |                                                       |                                   |
|                        | length 1..255                                         |                                   |
+------------------------+-------------------------------------------------------+-----------------------------------+
| file-name              | string                                                |                                   |
|                        |                                                       |                                   |
|                        | length 1..255                                         |                                   |
+------------------------+-------------------------------------------------------+-----------------------------------+
| rotation-file-size     | 1-1000 in MB                                          | 50MB                              |
+------------------------+-------------------------------------------------------+-----------------------------------+
| verbosity              | low, medium, high                                     | medium                            |
+------------------------+-------------------------------------------------------+-----------------------------------+
| count                  | 1..5000000 , unlimited                                | 100000                            |
+------------------------+-------------------------------------------------------+-----------------------------------+
| filter-expression      | tcpdump filter-expression string                      |                                   |
|                        |                                                       |                                   |
|                        | length 1..255                                         |                                   |
+------------------------+-------------------------------------------------------+-----------------------------------+
