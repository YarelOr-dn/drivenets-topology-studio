run ping mpls nil-fec
---------------------

**Minimum user role:** operator

You can manually send MPLS-OAM LSP ping probes to check connectivity status of an LSP.

MPLS LSP ping - checks connectivity of LSPs: An MPLS echo request packet is sent through an LSP to validate it. When the packet reaches the end of the path, it is sent to the control plane of the egress LSR. The egress LSR then verifies whether it is indeed an egress for the FEC.

To start sending MPLS-OAM ping echo request probes towards LSP:

**Command syntax: run ping mpls nil-fec { labels [labels-stack] egress-interface [egress-interface] next-hop [next-hop-address] | policy [policy-name] }** source-interface [source-interface] destination-address [destination-address] count [count] size [size] interval [interval] exp [exp] force-explicit-null

**Command mode:** operation

**Note**

- The next-hop-address address family dictates the applicable source-interfaces (having IP address of the same AFI) and the valid destination-address range.

- If the next-hop or the egress-interface are not valid paths for the LSP echo request, a "no FEC mapping" return code is applied.

- Round-trip time (RTT) is computed over the successful echo requests only. Jitter is the standard-variation for delay between a source LER and a destination LER, between different echo requests.

.. - if user set packet size to be smaller than the minimum size required to carry the mandatory TLVs (without padding), packet size will be the minimum size required and no padding will be used.

	- If packet is sent with MTU packet size bigger than path MTU, then MTU TX error counter will raise as no fragmentation is allowed.

	- Interval between sending echo request probe is the max{interval, min{reply-time, timeout}}

		- Interval - user configured minimum interval

		- reply-time - echo reply receive time

		- timeout - 2 seconds, timeout for waiting for an echo reply

	- If next-hop or egress-interface isn't valid path for the LSP echo request, return code of "no FEC mapping" will be applied.

	- Jitter is the standard-variation for delay between source LER and destination LER, between different echo requests

	- round-trip-delay is computed over the successful echo requests only.

	- When there are multiple possible nexthops (ECMP) at headend, determined egress interface and outgoing label will be used.

	- User can stop ping requests using Ctrl+c

**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| Parameter           | Description                                                                                                                                                                                                                                                                                                                                                 | Range                                                                                                                                     | Default                                               |
+=====================+=============================================================================================================================================================================================================================================================================================================================================================+===========================================================================================================================================+=======================================================+
| label-stack         | The label-stack to be sent. Specified as incoming labels for the responding nodes. Multiple labels are separated by commas, from top to bottom of stack.                                                                                                                                                                                                    | MPLS labels                                                                                                                               | \-                                                    |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| policy-name         | The SR-TE policy name, from which the labels-stack to be sent is derived. Available policies will be listed for the user. If specified policy does not exist, then an error will be printed to the user.                                                                                                                                                    | 1..255 characters (an existing SR-TE policy name)                                                                                         | \-                                                    |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| source-interface    | The interface from which the source IP is taken for the MPLS echo request.                                                                                                                                                                                                                                                                                  | 1..255 characters (an existing interface name)                                                                                            | source-interface to egress-interface according to FIB |
|                     | If the source-interface is used but is not configured with an IP address matching next-hop AFI, an error message is displayed.                                                                                                                                                                                                                              |                                                                                                                                           |                                                       |
|                     | If source-interface is not used, the source address of the egress interface from which the MPLS echo request is transmitted will be used.                                                                                                                                                                                                                   |                                                                                                                                           |                                                       |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| egress-interface    | Specifies the egress-interface from which the outgoing MPLS echo request is to be sent. Available interfaces under the VRF will be listed for the user.                                                                                                                                                                                                     | 1..255 characters (an existing interface name)                                                                                            | \-                                                    |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| next-hop-address    | Specifies the next hop as an IP address. Used for ECMP cases or if two entries exist in the RIB for the same FEC IP address.                                                                                                                                                                                                                                | A.B.C.D                                                                                                                                   | \-                                                    |
|                     |                                                                                                                                                                                                                                                                                                                                                             | X:X::X                                                                                                                                    |                                                       |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| destination-address | A local host destination address. When the LSP has ECMP, you can send separate pings with different destination addresses in order to change the packet flow and cover the different paths.                                                                                                                                                                 | within 127/8 ipv4 subnet addresses (127.x.y.z with subnet masks from 8 to 32) or an IPv6 address from the range 0:0:0:0:0:FFFF:7F00:0/104 | 127.0.0.1 or 0:0:0:0:0:FFFF:7F00:1                    |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| count               | The number of echo requests to send in a single probe.                                                                                                                                                                                                                                                                                                      | 1..1000000                                                                                                                                | 5                                                     |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| size                | The size of echo request packets. If you set a size that is smaller than the minimum required to support of TLVs, then the echo request packets will not be padded and the default size will be used instead. If packets are sent with an MTU packet size larger than the path MTU, the MTU TX error counter will increment as no fragmentation is allowed. | 100..65507                                                                                                                                | packet size is determent according to the used TLVs   |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| interval            | The minimum time interval (in seconds) between LSP ping messages. The interval is max{interval, min{reply-time, timeout}. That is, the highest value between the configured interval and either the echo reply receive time or the timeout (2 seconds) in case of no reply.                                                                                 | 1..86400                                                                                                                                  | 1                                                     |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| exp                 | MPLS experimental field value in the MPLS header for echo requests. All inner layers will also be set with a matching CoS value, including the IP precedence field of the IP header. The MPLS echo reply is always sent with IP precedence 6.                                                                                                               | 0..7                                                                                                                                      | 0                                                     |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| force-explicit-null | Forces an unsolicited explicit null label to be added to the MPLS label stack and allows LSP ping to be used to detect LSP breakages at the penultimate hop.                                                                                                                                                                                                | \-                                                                                                                                        | \-                                                    |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+

**Example**
::


	dnRouter# run ping mpls nil-fec labels 16005,16007 egress-interface ge100-0/0/7 next-hop 10.1.1.1 count 10
	Sending 10 MPLS Echo requests with Nil FEC labels [16005,16007], size: 100
	Timeout is 2 seconds, send interval is 1 second:

  	Legend:
  	'!' - success, '.' - timeout, 'Q' - request not sent, 'L' - labeled output interface, 'M' - malformed echo request, 'm' - TLVs not understood, 'F' - no FEC mapping, 'D' - downstream Mapping Mismatch, 'I' - upstream Interface Index Unknown, 'B' - unlabeled output interface, 'f' - FEC mismatch, 'N' - no label entry, 'P' - no receive interface label protocol, 'p' - premature termination of the LSP, 'l' - label switched with FEC stack change, 'd' - see DDMAP for return code, 'X' - undefined return code, 'x' - no return code

	Type ctrl+c to abort
	- Aug 21 12:34:56.123:
	!!!!!!!!!!

	Success rate is 100 percent (10/10)
	Jitter: 1 msec
	Round-trip-delay (min/avg/max): 61/64/71 msec


	dnRouter# run ping mpls nil-fec policy Policy1 count 10
	Sending 10 MPLS Echo requests with Nil FEC for SR-TE policy Policy1, size: 100
	Timeout is 2 seconds, send interval is 1 second:

  	Legend:
  	'!' - success, '.' - timeout, 'Q' - request not sent, 'L' - labeled output interface, 'M' - malformed echo request, 'm' - TLVs not understood, 'F' - no FEC mapping, 'D' - downstream Mapping Mismatch, 'I' - upstream Interface Index Unknown, 'B' - unlabeled output interface, 'f' - FEC mismatch, 'N' - no label entry, 'P' - no receive interface label protocol, 'p' - premature termination of the LSP, 'l' - label switched with FEC stack change, 'd' - see DDMAP for return code, 'X' - undefined return code, 'x' - no return code

	Type ctrl+c to abort
	- Aug 21 12:34:56.123:
	!!!!!.!!.!

	Success rate is 80 percent (8/10)
	Jitter: 1 msec
	Round-trip-delay (min/avg/max): 61/64/71 msec




**Command History**

+---------+------------------------+
| Release | Modification           |
+=========+========================+
| 15.1    | Command introduced     |
+---------+------------------------+
| 18.2    | Added support for IPv6 |
+---------+------------------------+