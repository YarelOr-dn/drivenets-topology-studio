show file packet-capture
------------------------

**Command syntax: show file packet-capture {[ file-name ]** {verbosity [verbosity]} **\| list }** 
**Description:** displays packet-capture pcap file

Displays packet-capture files on active ncc. 

When displaying specific file, use verbosity to control pcap verbosity output:
-   Low - When parsing and printing, produce (slightly more) verbose output. For example, the time to live, identification, total length and options in an IP packet are printed. Also enables additional packet integrity checks such as verifying the IP and ICMP header checksum.
-   Medium - additional fields are printed from NFS reply packets, and SMB packets are fully decoded.
-   High - Example telnet SB ... SE options are printed in full

User can use pipe commands to filer results of multiple files

**CLI example:**
::

	dnRouter# show file packet-capture list
	| Type |Id | File name                                      | Size    | Last modified            |
	|------+---+------------------------------------------------+---------+--------------------------|
	| NCC  |0  | BGP_Debug_.1.pcap                              | 854.0K  | 14-Feb-2021 13:21:00 UTC |

	dnRouter# show file packet-capture ISIS_Debug_.1.pcap
	reading from file ISIS_Debug.1.pcap, link-type LINUX_SLL (Linux cooked)
	14:25:13.382322 ethertype Unknown, IS-IS, length 90
	p2p IIH, hlen: 20, v: 1, pdu-v: 1, sys-id-len: 6 (0), max-area: 3 (0)
	0x0000:  8314 0100 1101 0000
	  source-id: 0000.0051.0051, holding time: 27s, Flags: [Level 2 only]
	  circuit-id: 0x01, PDU length: 90
	  0x0000:  0200 0000 5100 5100 1b00 5a01
	    Point-to-point Adjacency State TLV #240, length: 5
	      Adjacency State: Down (2)
	      Neighbor Extended Local circuit-ID: 0x01123301
	      0x0000:  0200 0001 96
	    Protocols supported TLV #129, length: 2
	      NLPID(s): IPv4 (0xcc), IPv6 (0x8e)
	      0x0000:  cc8e
	    IPv4 Interface address(es) TLV #132, length: 4
	      IPv4 interface address: 1.18.51.1
	      0x0000:  0112 3301
	    unknown TLV #233, length: 16
	      0x0000:  2001 0018 0051 0000 0000 0000 0000 0000
	    IPv6 Interface address(es) TLV #232, length: 16
	      IPv6 interface address: fe80::e6fc:8204:fce6:6c3d
	      0x0000:  fe80 0000 0000 0000 e6fc 8204 fce6 6c3d
	    Area address(es) TLV #1, length: 4
	      Area address (length: 3): 47.0000
	      0x0000:  0347 0000
	    Restart Signaling TLV #211, length: 3
	      Flags [none], Remaining holding time 0s
	      0x0000:  0000 00
	    Multi Topology TLV #229, length: 4
	      IPv4 unicast Topology (0x000), Flags: [none]
	      IPv6 unicast Topology (0x002), Flags: [none]
	      0x0000:  0000 0002
	14:25:13.382322 ethertype Unknown, IS-IS, length 90
		p2p IIH, hlen: 20, v: 1, pdu-v: 1, sys-id-len: 6 (0), max-area: 3 (0)
	...
  
    dnRouter# show file packet-capture ISIS_Debug_.1.pcap verbosity low



**Command mode:** operational

**TACACS role:** viewer

**Note:**


-  file packet-capture type has the following location:

	-  packet-capture - /packet-capture/


**Help line:**

**Parameter table:**

+-----------+----------------------------------------------------+---------------+
| Parameter | Values                                             | Default value |
+===========+====================================================+===============+
| file-name | Any string except "list". Including sub-directory. |               |
+-----------+----------------------------------------------------+---------------+
| verbosity | low , medium, high                                 |               |
+-----------+----------------------------------------------------+---------------+