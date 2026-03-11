run ping mpls rsvp
------------------

**Minimum user role:** operator

You can manually send MPLS-OAM LSP ping probes to check connectivity status of an RSVP tunnel.

MPLS LSP ping - checks connectivity of LSPs: An MPLS echo request packet is sent through an LSP to validate it. When the packet reaches the end of the path, it is sent to the control plane of the egress LSR. The egress LSR then verifies whether it is indeed an egress for the FEC.

To start sending MPLS-OAM ping echo request probes towards an RSVP tunnel tail end:

**Command syntax: run ping mpls rsvp [tunnel-name]** destination-address [destination-address] count [count] size [size] interval [interval] exp [exp] force-explicit-null

**Command mode:** operation 

**Note**

- If you run the command on a tunnel that does not exist, or if the tunnel is down, an error message is displayed.

- Round-trip time (RTT) are computed over the successful echo requests only. Jitter is the standard-variation of a tunnel head to a tunnel tail destination delay between different echo requests.

.. - if user set packet size to be smaller than the minimum size required to carry the mandatory TLVs (without padding), packet size will be the minimum size required and no padding will be used.

	- If packet is sent with mtu packet size bigger than path mtu, then MTU TX error counter will raise as no fragmentation is allowed.

	- Interval between sending echo request probe is the max{interval, min{reply-time, timeout}}

		- Interval - user configured minimum interval

		- reply-time. echo reply receive time

		- timeout - 2 seconds, timeout for waiting to an echo reply

	- In case the user uses a non-existing tunnel, the following message will be displayed: "no tunnel exists"

	- In case tunnel is down, an echo request will not be sent, and the following message will be displayed "no tunnel exists". The packet count is incremented.

	- Jitter is the standard-variation of Tunnel head to Tunnel tail destination delay between different echo requests

	- round-trip-delay is computed over the successful echo requests only. 

	- User can stop ping requests using Ctrl+c

**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-----------------------------------------------------+
| Parameter           | Description                                                                                                                                                                                                                                                                                                                                                 | Range                                                                         | Default                                             |
+=====================+=============================================================================================================================================================================================================================================================================================================================================================+===============================================================================+=====================================================+
| tunnel-name         | The name of an existing tunnel to ping. You can ping any tunnel type: primary, bypass, auto-bypass, auto-mesh.                                                                                                                                                                                                                                              | 1..255 characters                                                             | \-                                                  |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-----------------------------------------------------+
| destination-address | A local host destination address. When the LSP has ECMP, you can send separate pings with different destination addresses in order to change the packet flow and cover the different paths.                                                                                                                                                                 | within 127/8 ipv4 subnet addresses (127.x.y.z with subnet masks from 8 to 32) | 127.0.0.1                                           |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-----------------------------------------------------+
| count               | The number of echo requests to send in a single probe.                                                                                                                                                                                                                                                                                                      | 1..1000000                                                                    | 5                                                   |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-----------------------------------------------------+
| size                | The size of echo request packets. If you set a size that is smaller than the minimum required to support of TLVs, then the echo request packets will not be padded and the default size will be used instead. If packets are sent with an MTU packet size larger than the path MTU, the MTU TX error counter will increment as no fragmentation is allowed. | 100..65507                                                                    | packet size is determent according to the used TLVs |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-----------------------------------------------------+
| interval            | The minimum time interval (in seconds) between LSP ping messages. The interval is max{interval, min{reply-time, timeout}. That is, the highest value between the configured interval and either the echo reply receive time or the timeout (2 seconds) in case of no reply.                                                                                 | 1..86400                                                                      | 1                                                   |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-----------------------------------------------------+
| exp                 | MPLS experimental field value in the MPLS header for echo requests. All inner layers will also be set with a matching CoS value, including the IP precedence field of the IPv4 header. The MPLS echo reply is always sent with IP precedence 6.                                                                                                             | 0..7                                                                          | 0                                                   |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-----------------------------------------------------+
| force-explicit-null | Forces an unsolicited explicit null label to be added to the MPLS label stack and allows LSP ping to be used to detect LSP breakages at the penultimate hop.                                                                                                                                                                                                | \-                                                                            | \-                                                  |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-----------------------------------------------------+

**Example**
::

	
	dnRouter# run ping mpls rsvp TUNNEL_1
	Sending 5 MPLS Echo requests, size: 100, target rsvp tunnel: TUNNEL_1
	Timeout is 2 seconds, send interval is 1 second: 
	
  	Legend:
  	'!' - success, '.' - timeout, 'Q' - request not sent, 'L' - labeled output interface, 'M' - malformed echo request, 'm' - TLVs not understood, 'F' - no FEC mapping, 'D' - downstream Mapping Mismatch, 'I' - upstream Interface Index Unknown, 'B' - unlabeled output interface, 'f' - FEC mismatch, 'N' - no label entry, 'P' - no receive interface label protocol, 'p' - premature termination of the LSP, 'l' - label switched with FEC stack change, 'd' - see DDMAP for return code, 'X' - undefined return code, 'x' - no return code
	
	
	Type ctrl+c to abort 
	- Aug 21 12:34:56.123: 
	!.!!! 
	
	Success rate is 80 percent (4/5)
	Jitter: 1 msec
	Round-trip-delay (min/avg/max): 61/64/71 msec


	dnRouter# run ping mpls rsvp TUNNEL_2
	Sending 5 MPLS Echo requests, size: 100, target rsvp tunnel: TUNNEL_2
	Timeout is 2 seconds, send interval is 1 second: 
	
  	Legend:
  	'!' - success, '.' - timeout, 'Q' - request not sent, 'L' - labeled output interface, 'M' - malformed echo request, 'm' - TLVs not understood, 'F' - no FEC mapping, 'D' - downstream Mapping Mismatch, 'I' - upstream Interface Index Unknown, 'B' - unlabeled output interface, 'f' - FEC mismatch, 'N' - no label entry, 'P' - no receive interface label protocol, 'p' - premature termination of the LSP, 'l' - label switched with FEC stack change, 'd' - see DDMAP for return code, 'X' - undefined return code, 'x' - no return code
	
	
	Type ctrl+c to abort 
	- Aug 21 12:34:56.123: 
	QQQQQ
	
	Success rate is 0 percent (0/5)
	

**Command History**

+---------+------------------------+
| Release | Modification           |
+=========+========================+
| 11.0    | Command introduced     |
+---------+------------------------+
| 15.0    | Updated command legend |
+---------+------------------------+

