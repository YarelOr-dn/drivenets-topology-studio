run traceroute mpls rsvp
------------------------

**Minimum user role:** operator

You can manually run traceroute to a remote host for an RSVP tunnel.

MPLS traceroute - used for hop-by-hop fault localization and/or path tracing: A packet is sent to the control plane of each transit LSR. The transit LSR performs various checks to confirm that it is indeed a transit LSR for this path; this LSR also returns additional information that helps check the control plane against the data plane.

The interval between probes is min{reply-time, timeout}. That is, either the echo reply receive time or the timeout (2 seconds) in case of no reply.

To start a traceroute for an RSVP tunnel:

**Command syntax: run traceroute mpls rsvp [tunnel-name]** destination-address [destination-address] max-hops [max-hops] size [size] exp [exp] force-explicit-null ddmap detail

**Command mode:** operation 

**Note**

- If you run the command on a tunnel that does not exist, or if the tunnel is down, an error message is displayed.

.. - if user set packet size to be smaller than the minimum size required to carry the mandatory TLVs (without padding), packet size will be the minimum size required and no padding will be used.

	- If packet is sent with MTU packet size bigger than path MTU, then MTU TX error counter will raise as no fragmentation is allowed.

	- Echo requests are sent by default with the DSMAP TLV, but DDMAP can be forced instead.

	- In case the user uses a non-existing tunnel, the following message will be displayed: "no tunnel exists" and traceroute action will stop.

	- In case tunnel is down, an echo request will not be sent, and the following message will be displayed "no tunnel exists" and traceroute action will stop.

	- User can stop traceroute requests using Ctrl+c

**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-----------------------------------------------------+
| Parameter           | Description                                                                                                                                                                                                                                                                                                                                                 | Range                                                                         | Default                                             |
+=====================+=============================================================================================================================================================================================================================================================================================================================================================+===============================================================================+=====================================================+
| tunnel-name         | The name of an existing tunnel on which to run the traceroute. You can run traceroute on any tunnel type: primary, bypass, auto-bypass, auto-mesh.                                                                                                                                                                                                          | 1..255 characters                                                             | \-                                                  |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-----------------------------------------------------+
| destination-address | A local host destination address. When the LSP has ECMP, you can run separate traceroutes with different destination addresses in order to change the packet flow and cover the different paths.                                                                                                                                                            | within 127/8 IPv4 subnet addresses (127.x.y.z with subnet masks from 8 to 32) | 127.0.0.1                                           |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-----------------------------------------------------+
| max-hops            | The maximum number of hops before the traceroute action is terminated (the maximum TTL value for the traceroute probe)                                                                                                                                                                                                                                      | 1..255                                                                        | 30                                                  |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-----------------------------------------------------+
| size                | The size of echo request packets. If you set a size that is smaller than the minimum required to support of TLVs, then the echo request packets will not be padded and the default size will be used instead. If packets are sent with an MTU packet size larger than the path MTU, the MTU TX error counter will increment as no fragmentation is allowed. | 100..65507                                                                    | packet size is determent according to the used TLVs |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-----------------------------------------------------+
| exp                 | MPLS experimental field value in the MPLS header for echo requests. All inner layers will also be set with a matching CoS value, including the IP precedence field of the IPv4 header. The MPLS echo reply is always sent with IP precedence 6.                                                                                                             | 0..7                                                                          | 0                                                   |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-----------------------------------------------------+
| force-explicit-null | Forces an unsolicited explicit null label to be added to the MPLS label stack and allows LSP traceroute to be used to detect LSP breakages at the penultimate hop.                                                                                                                                                                                          | \-                                                                            | \-                                                  |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-----------------------------------------------------+
| ddmap               | Forces the Downstream Detailed Mapping TLV instead of the deprecated DSMAP TLV                                                                                                                                                                                                                                                                              | \-                                                                            | \-                                                  |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-----------------------------------------------------+
| detail              | Prints a detailed output for every reply received.                                                                                                                                                                                                                                                                                                          |                                                                               |                                                     |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-----------------------------------------------------+

**Example**
::

	
	dnRouter# run traceroute mpls rsvp TUNNEL_1 
	Tracing MPLS LSP, target rsvp tunnel: TUNNEL_1
	Timeout is 2 seconds: 
	
	Legend:
	'!' - success, '.' - timeout, 'Q' - request not sent, 'L' - labeled output interface, 'M' - malformed echo request, 'm' - TLVs not understood, 'F' - no FEC mapping, 'D' - downstream Mapping Mismatch, 'I' - upstream Interface Index Unknown, 'B' - unlabeled output interface, 'f' - FEC mismatch, 'N' - no label entry, 'P' - no receive interface label protocol, 'p' - premature termination of the LSP, 'l' - label switched with FEC stack change, 'd' - see DDMAP for return code, 'X' - undefined return code, 'x' - no return code
	
	Type ctrl+c to abort 
	Destination address 127.0.0.1
	     0 10.131.191.230 MPLS-MTU 1500 [Labels: 19 Exp: 0]
	L 1 10.131.159.226 MPLS-MTU 1504 [implicit-null] round-trip-delay 20 msec
	! 2 10.131.159.225 rtt 40 msec
	
	

**Command History**

+---------+----------------------------------------------------+
| Release | Modification                                       |
+=========+====================================================+
| 11.0    | Command introduced                                 |
+---------+----------------------------------------------------+
| 15.0    | Updated command syntax                             |
+---------+----------------------------------------------------+
| 15.1    | Updated command syntax to support ddmap and detail |
+---------+----------------------------------------------------+

