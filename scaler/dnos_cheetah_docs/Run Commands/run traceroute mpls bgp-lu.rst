run traceroute mpls bgp-lu
--------------------------

**Minimum user role:** operator

You can manually run traceroute to a remote host for a BGP-LU LSP.

MPLS traceroute - used for hop-by-hop fault localization and/or path tracing: A packet is sent to the control plane of each transit LSR. The transit LSR performs various checks to confirm that it is indeed a transit LSR for this path; this LSR also returns additional information that helps check the control plane against the data plane.

The interval between probes is min{reply-time, timeout}. That is, either the echo reply receive time or the timeout (2 seconds) in case of no reply.

To start a traceroute for a BGP-LU LSP:

**Command syntax: run traceroute mpls bgp-lu [target-address]** multipath destination-address [destination-address] next-hop [next-hop-address] source-interface [source-interface] size [size] exp [exp] max-hops [max-hops] force-explicit-null ddmap detail

**Command mode:** operation

**Note**

..  - If user set packet size to be smaller than the minimum size required to carry the mandatory TLVs (without padding), packet size will be the minimum size required and no padding shall be used.

    - If the next-hop-address is not a valid path for the LSP echo request, a "no FEC mapping" return code is applied.

    - The target-address address family dictates the applicable source-interfaces (having IP address of the same AFI) and the valid destination-address range.

    - If packet is sent with MTU packet size bigger than path MTU, then MTU TX error counter will rise as no fragmentation is allowed.

    - Echo requests are sent by default with the DSMAP TLV, but DDMAP can be forced instead.

    - In the event that the user uses an unknown IP prefix, then the following message will be displayed: "no route exists" and traceroute action will stop.

    - If the multipath knob is used and there are multiple possible nexthops (ECMP), each possibe ECMP path and subsequent reported paths matching filters used will be validated end-to-end using the determined information as derived internally (egress interface, outgoing labels, destination address, etc.); or by downstream objects returned within the MPLS echo replies.

    - If the multipath knob is not used, echo request will be sent with the valid determined information, contingent on information provided by the operator, necessary to probe a single path, and no multipath information will be printed in CLI.

    - If next-hop is invalid or specified with address-family different than destination address-family ip address, then output code Q will be printed and error message will be displayed on the screen notifying: “no route to host via specified next-hop”.

    - User can stop traceroute requests using ctrl+c.

    - Total Time Elapsed in multipath traceroute represents the total time the traceroute operation took from start to finish.

    - In multipath traceroute each reported path is determined to be 'Found', 'Unexplorable' or 'Broken'. Found paths are valid paths for verified LSPs all the way to the egress LER; Unexplorable paths are discovered paths that could not be verified end-to-end for various reasons, inter alia, because the 127/8 destination IP address range used for the LSP selection has been exhausted, or due to disruptions along the LSP such as consecutive timeouts that break the trace (as opposed to certain non-compliant LSRs that are skipped) or TTL expiration; Broken paths indicate that the LSP is broken, meaning that traffic will not be sent across this path and may be discarded.

    - For multipath traceroute hops that timeout will be indicated in the summary of each path, but not in the detailed per-hop output.

    - FEC stack sent shows FEC stack from top to bottom of stack, left to right.

**Parameter table**

+---------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| Parameter           | Description                                                                                                                                                                                                                                                                                                                                                                        | Range                                                                                                                                     | Default                                               |
+=====================+====================================================================================================================================================================================================================================================================================================================================================================================+===========================================================================================================================================+=======================================================+
| multipath           | Validates all reported paths.                                                                                                                                                                                                                                                                                                                                                      | \-                                                                                                                                        | \-                                                    |
|                     | If the multipath knob is used and there are multiple possible nexthops (ECMP), each possible ECMP path, and subsequent reported paths, that match used filters will be validated end-to-end using the determined information as derived internally (egress interface, outgoing labels, destination address, etc.); or by downstream objects returned within the MPLS echo replies. |                                                                                                                                           |                                                       |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| target-address      | An IPv4 or IPv6 destination address FEC for BGP-LU FEC types. If the target-address is not a valid address known by BGP-LU, an error message is displayed.                                                                                                                                                                                                                         | A.B.C.D/M                                                                                                                                 | \-                                                    |
|                     |                                                                                                                                                                                                                                                                                                                                                                                    | X:X::X/M                                                                                                                                  |                                                       |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| source-interface    | The interface from which the source IP is taken for the MPLS echo request.                                                                                                                                                                                                                                                                                                         | 1..255 characters (an existing interface name)                                                                                            | source-interface to egress-interface according to FIB |
|                     | If the source-interface is used but is not configured with an applicable AFI IP address, an error message is displayed.                                                                                                                                                                                                                                                            |                                                                                                                                           |                                                       |
|                     | If source-interface is not used, the source address of the egress interface from which the MPLS echo request is transmitted will be used.                                                                                                                                                                                                                                          |                                                                                                                                           |                                                       |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| next-hop-address    | Specifies the next hop as an IP address. Can be used for ECMP cases or if two entries exist in the RIB for the same IP FEC.                                                                                                                                                                                                                                                        | A.B.C.D                                                                                                                                   | \-                                                    |
|                     |                                                                                                                                                                                                                                                                                                                                                                                    | X:X::X                                                                                                                                    |                                                       |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| destination-address | A local host destination address. When the LSP has ECMP, you can send separate pings with different destination addresses in order to change the packet flow and cover the different paths.                                                                                                                                                                                        | within 127/8 ipv4 subnet addresses (127.x.y.z with subnet masks from 8 to 32) or an IPv6 address from the range 0:0:0:0:0:FFFF:7F00:0/104 | 127.0.0.1 or 0:0:0:0:0:FFFF:7F00:1                    |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| size                | The size of echo request packets. If you set a size that is smaller than the minimum required to support of TLVs, then the echo request packets will not be padded and the default size will be used instead. If packets are sent with an MTU packet size larger than the path MTU, the MTU TX error counter will increment as no fragmentation is allowed.                        | 100..9300                                                                                                                                 | packet size is determent according to the used TLVs   |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| exp                 | MPLS experimental field value in the MPLS header for echo requests. All inner layers will also be set with a matching CoS value, including the IP precedence field of the IP header. The MPLS echo reply is always sent with IP precedence 6.                                                                                                                                      | 0..7                                                                                                                                      | 0                                                     |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| max-hops            | The maximum number of hops before the traceroute action is terminated (the maximum TTL value for the traceroute probe)                                                                                                                                                                                                                                                             | 1..255                                                                                                                                    | 30                                                    |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| force-explicit-null | Forces an unsolicited explicit null label to be added to the MPLS label stack and allows LSP ping to be used to detect LSP breakages at the penultimate hop.                                                                                                                                                                                                                       | \-                                                                                                                                        | \-                                                    |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| ddmap               | Forces the Downstream Detailed Mapping TLV instead of the deprecated DSMAP TLV.                                                                                                                                                                                                                                                                                                    | \-                                                                                                                                        | -                                                     |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| detail              | Prints a detailed output for every reply received.                                                                                                                                                                                                                                                                                                                                 |                                                                                                                                           |                                                       |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------+

**Example**
::


  dnRouter# run traceroute mpls bgp-lu 1.2.3.4/32
  Tracing MPLS LSP, target ipv4-address: 1.2.3.4/32
  Timeout is 2 seconds:

  Legend:
  '!' - success, '.' - timeout, 'Q' - request not sent, 'L' - labeled output interface, 'M' - malformed echo request, 'm' - TLVs not understood, 'F' - no FEC mapping, 'D' - downstream Mapping Mismatch, 'I' - upstream Interface Index Unknown, 'B' - unlabeled output interface, 'f' - FEC mismatch, 'N' - no label entry, 'P' - no receive interface label protocol, 'p' - premature termination of the LSP, 'l' - label switched with FEC stack change, 'd' - see DDMAP for return code, 'X' - undefined return code, 'x' - no return code

  Type ctrl+c to abort

   output interface ge100-0/0/5 nexthop 10.1.17.7
   source 1.1.1.1 destination 127.0.0.1
    0 1.1.1.1 10.1.17.7 MPLS-MTU 1500 [Labels: 24002 Exp: 0]
  L 1 10.1.17.7 10.1.75.5 MPLS-MTU 1500 [Labels: implicit-null Exp: 0] round-trip-delay 3 msec
  ! 2 10.1.75.5 round-trip-delay 4 msec


  dnRouter# run traceroute mpls bgp-lu 2.2.2.2/32 multipath
  Tracing MPLS LSP, target ipv4-address: 2.2.2.2/32
  Timeout is 2 seconds:

  Legend:
  '!' - success, '.' - timeout, 'Q' - request not sent, 'L' - labeled output interface, 'M' - malformed echo request, 'm' - TLVs not understood, 'F' - no FEC mapping, 'D' - downstream Mapping Mismatch, 'I' - upstream Interface Index Unknown, 'B' - unlabeled output interface, 'f' - FEC mismatch, 'N' - no label entry, 'P' - no receive interface label protocol, 'p' - premature termination of the LSP, 'l' - label switched with FEC stack change, 'd' - see DDMAP for return code, 'X' - undefined return code, 'x' - no return code

  Type ctrl+c to abort

  LL....
  Path 1 Unexplorable,
   output interface ge100-0/0/0 nexthop 10.1.1.13
   source 10.1.1.2 destination 127.0.0.64
    0 10.1.1.2 10.1.1.13 MPLS-MTU 1500 [Labels: 24023 Exp: 0] multipaths 0
  L 1 10.1.1.13 10.1.1.10 MPLS-MTU 1500 [Labels: 18809 Exp: 0] multipaths 1 round-trip-delay 2 msec
  L 2 10.1.1.10 10.1.91.10 MPLS-MTU 1500 [Labels: 802809 Exp: 0] multipaths 3 round-trip-delay 4 msec

  LL!
  Path 2 Found,
   output interface ge100-0/0/2 nexthop 10.1.1.1
   source 10.1.1.17 destination 127.0.1.64
    0 10.1.1.2 10.1.1.1 MPLS-MTU 1500 [Labels: 24023 Exp: 0] multipaths 0
  L 1 10.1.1.1 10.1.1.10 MPLS-MTU 1500 [Labels: 18809 Exp: 0] multipaths 1 round-trip-delay 2 msec
  L 2 10.1.1.10 0.1.91.6 MPLS-MTU 1500 [Labels: 802809 Exp: 0] multipaths 3 round-trip-delay 4 msec
  ! 3 10.1.64.5 multipaths 0 round-trip-delay 5 msec

  B
  Path 3 Broken,
   output interface ge100-0/0/2 nexthop 10.1.1.1
   source 10.1.1.17 destination 127.0.1.66
    0 10.1.1.17 10.1.1.22 MPLS-MTU 1500 [Labels: 24023 Exp: 0] multipaths 0
  B 1 10.1.1.22 10.1.1.10 MPLS-MTU 1500 [Labels: 18809 Exp: 0] multipaths 1 round-trip-delay 2 msec

  Paths (found/broken/unexplored) (1/1/1)
   Echo Request (sent/fail) (10/0)
   Echo Reply (received/timeout) (6/4)
   Total Time Elapsed 34 ms


  dnRouter# run traceroute mpls bgp-lu 1.2.3.4/32 multipath detail
  Tracing MPLS LSP, target ipv4-address: 1.2.3.4/32
  Timeout is 2 seconds:

  Legend:
  '!' - success, '.' - timeout, 'Q' - request not sent, 'L' - labeled output interface, 'M' - malformed echo request, 'm' - TLVs not understood, 'F' - no FEC mapping, 'D' - downstream Mapping Mismatch, 'I' - upstream Interface Index Unknown, 'B' - unlabeled output interface, 'f' - FEC mismatch, 'N' - no label entry, 'P' - no receive interface label protocol, 'p' - premature termination of the LSP, 'l' - label switched with FEC stack change, 'd' - see DDMAP for return code, 'X' - undefined return code, 'x' - no return code

  Type ctrl+c to abort

  L!
  Path 1 Found,
   output interface ge100-0/0/5 nexthop 10.1.17.7
   source 1.1.1.1 destination 127.0.0.64
    0 1.1.1.1 10.1.17.7 MPLS-MTU 1500 [Labels: 24002 Exp: 0] multipaths 0
      Multipath type: bit-masked IP, base address: 127.0.0.64, mask: FFFFFFFF
  L 1 10.1.17.7 10.1.75.5 MPLS-MTU 1500 [Labels: implicit-null Exp: 0] multipaths 1 round-trip-delay 3 msec
      Target FEC stack sent: [0] BGP-LU 1.2.3.4
      FEC-change received: push-RSVP (2.2.2.2)
      Multipath type: bit-masked IP, base address: 127.0.0.64, mask: FFFFFFFF
  ! 2 10.1.75.5 round-trip-delay 4 msec

  L!
  Path 2 Found,
   output interface ge100-0/0/6 nexthop 10.1.18.8
   source 1.1.1.1 destination 127.0.0.64
    0 1.1.1.1 10.1.18.8 MPLS-MTU 1500 [Labels: 24002 Exp: 0] multipaths 0
      Multipath type: bit-masked IP, base address: 127.0.0.64, mask: FFFFFFFF
  L 1 10.1.18.8 10.1.85.5 MPLS-MTU 1500 [Labels: implicit-null Exp: 0] multipaths 2 round-trip-delay 8 msec
      Target FEC stack sent: [0] BGP-LU 1.2.3.4
      FEC-change received: push-RSVP (2.2.2.2)
      Multipath type: bit-masked IP, base address: 127.0.0.64, mask: FFFFFFFF
  ! 2 10.1.85.5 round-trip-delay 20 msec

  !
  Path 3 Found,
   output interface ge100-0/0/6 nexthop 10.1.18.8
   source 1.1.1.1 destination 127.0.0.66
    0 1.1.1.1 10.1.18.8 MPLS-MTU 1500 [Labels: 24002 Exp: 0] multipaths 0
      Multipath type: bit-masked IP, base address: 127.0.0.64, mask: FFFFFFFF
  L 1 10.1.18.8 10.1.58.5 MPLS-MTU 1500 [Labels: implicit-null Exp: 0] multipaths 2 round-trip-delay 20 msec
      Target FEC stack sent: [0] BGP-LU 1.2.3.4
      FEC-change received: push-RSVP (2.2.2.2)
      Multipath type: bit-masked IP, base address: 127.0.0.64, mask: FFFFFFFF
  ! 2 10.1.58.5 round-trip-delay 43 msec

  Paths (found/broken/unexplored) (3/0/0)
   Echo Request (sent/fail) (5/0)
   Echo Reply (received/timeout) (5/0)
   Total Time Elapsed 67 ms


**Command History**

+---------+-----------------------------------------------------------+
| Release | Modification                                              |
+=========+===========================================================+
| 11.0    | Command introduced                                        |
+---------+-----------------------------------------------------------+
| 15.0    | Updated command syntax to support 'multipath' and 'ddmap' |
+---------+-----------------------------------------------------------+
| 15.1    | Updated command syntax to support detailed output         |
+---------+-----------------------------------------------------------+
| 18.2    | Added support for IPv6                                    |
+---------+-----------------------------------------------------------+
