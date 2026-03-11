show mpls exact-path
--------------------

**Minimum user role:** viewer

This command displays the exact path that will be selected from a number of possible paths in the MPLS routing-table for an incoming unicast packet flow, according to the specified attributes. For a bundle interface, it displays the load-balancing hash result.

**Command syntax: show mpls exact-path** **{labels [label]**, [label],  **}** **payload [ipv4 | ipv6] src-ip [src-ip] dest-ip [dest-ip] protocol [{udp | tcp} {src-port [src-port] dest-port [dest-port]} | any-host]** mpls-exp [exp] payload-dscp [dscp] ncp [ncp-id] detail

**Command mode:** operational



**Note**

- Only active ECMP, CBTS, or LAG group members, are counted in the (1 of n) CLI output. If only 3 links are active out of 4 configured members of a LAG group, the output indicates (1 of 3) and not (1 of 4).

- The path information may not be accurate for dest-ports 2152 and 2123, used by GTP, and dest-port 4789, used by VXLAN, as the hash calculation may take the GTP Tunnel Identifer and VXLAN's encapsulated Ethernet and IP headers into account.

- Does not support 7 MPLS label stack

..
   - Support 3-tuple IP flows over any-host(61) ip protocol and 5-tuple IP flows over udp or tcp.

   - Support up to 7 mpls labels.

   - All (terminated and non-terminated labels) incoming labels must be specified. First label to the left is the outermost (top) label on the label stack.

   - Support unicast flows only. No support for hash resolution of multicast flows.

   - Only the active members of the ECMP, CBTS or LAG group are counted in the (1 of n) CLI output. In particular, if only 3 links are active out of 4 configured members of a LAG group, the output would indicate (1 of 3).

   - The path information may not be accurate for dest-port 2152 and 2123, used by GTP, and dest-port 4789, used by VXLAN, as the hash calculation may take the GTP Tunnel Identifer and VXLAN's encapsulated Ethernet and IP headers into account.

**Parameter table**

All incoming labels must be specified (terminated and non-terminated labels) . First label to the left is the outermost (top) label on the label stack.

+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| Parameter | Description                                                                                                                                                         | Range                           | Default                |
+===========+=====================================================================================================================================================================+=================================+========================+
| label     | The flow labels for which to display exact-path                                                                                                                     | 0..1048575                      | \-                     |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| ipv4/ipv6 | Address-family for the flow for which to display exact-path                                                                                                         | IPv4                            | \-                     |
|           |                                                                                                                                                                     | IPv6                            |                        |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| src-ip    | The source address in the IP header of the packets                                                                                                                  | A.B.C.D/xx:xx::xx:xx            | \-                     |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| dest-ip   | The destination address in the IP header of the packets                                                                                                             | A.B.C.D/xx:xx::xx:xx            | \-                     |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| protocol  | The protocol used for the flow                                                                                                                                      | TCP - for 5-tuple IP flows      |                        |
|           |                                                                                                                                                                     | UDP - for 5-tuple IP flows      | \-                     |
|           |                                                                                                                                                                     | any-host - for 3-tuple IP flows |                        |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| src-port  | The source port of the UDP/TCP flows                                                                                                                                | 0..65535                        | \-                     |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| dest-port | The destination port of the UDP/TCP flows                                                                                                                           | 0..65535                        | \-                     |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| exp       | Filters the display to the specified EXP field value                                                                                                                | 0..7                            | 0                      |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| dscp      | Filters the display to a specific DSCP value                                                                                                                        | 0..63                           | 0                      |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| ncp-id    | Filters the display to a specific NCP                                                                                                                               | 0..255                          | NCP with the lowest ID |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| detail    | Displays detailed information (e.g. information about up to two ECMP levels, Class Based Tunnel Selection (CBTS), and Link Aggregation (LAG) on the displayed path. | \-                              | \-                     |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+



**Example**
::

    dnRouter# show mpls exact-path labels 6612, 433 payload ipv4 src-address 10.1.1.123 dest-ip 10.1.2.133 protocol udp src-port 2040 dest-port 808 mpls-exp 3 payload-dscp 3

    interface: ge100-2/0/3 (1 of 4 in bundle-3.200)
    next-hop: 13.0.1.1
    mpls labels: 100(top), 1001


    dnRouter# show mpls exact-path labels 6612, 433 payload ipv4 src-ip 10.1.1.123 dest-ip 10.1.2.133 protocol udp src-port 2040 dest-port 808 mpls-exp 3 payload-dscp 3 detail

    NCP-ID: 3
    Path Forwarding Information:
    next-hop: 2.2.2.2 (1 of 2)
    mpls labels: 1001
    hash: 0xDF34
       te-class 5 carries cos 3 (1 of 2)
          next-hop: 13.0.1.1 (1 of 4)
          mpls labels: 100
          interface: bundle-3.200
          via tunnel_18 tunnel oid 224
          hash: 0x6672
             interface:  ge100-2/0/3 (1 of 4)
             hash: 0x0672D

.. **Help line:** show mpls load-balancing hash result

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 11.2    | Command introduced                  |
+---------+-------------------------------------+
| 11.5    | Replaced "host-any" with "any-host" |
+---------+-------------------------------------+
