show route exact-path
---------------------

**Minimum user role:** viewer

This command displays the exact path that will be selected from a number of possible paths in the forwarding-table for an incoming packet flow, according to the specified attributes. For a bundle interface, it displays the load-balancing hash result.

To display exact path for a specific flow:

**Command syntax: show route exact-path** **[ipv4 | ipv6] src-ip [src-ip] dest-ip [dest-ip] protocol [{udp | tcp} {src-port [src-port] dest-port [dest-port]} | any-host]** dscp [dscp] vrf [vrf-name] ncp [ncp-id] detail

**Command mode:** operational



**Note**

- Only active ECMP, CBTS, or LAG group members, are counted in the (1 of n) CLI output. If only 3 links are active out of 4 configured members of a LAG group, the output indicates (1 of 3) and not (1 of 4).

- The path information may not be accurate for dest-ports 2152 and 2123, used by GTP, and dest-port 4789, used by VXLAN, as the hash calculation may take the GTP Tunnel Identifer and VXLAN's encapsulated Ethernet and IP headers into account.

.. - Support 3-tuple IP flows over any-host(61) ip protocol and 5-tuple IP flows over udp or tcp.

    - Support unicast flows only. No support for hash resolution of multicast flows.

    - Only the active members of the ECMP, CBTS or LAG group are counted in the (1 of n) CLI output. In particular, if only 3 links are active out of 4 configured members of a LAG group, the output would indicate (1 of 3).

    - The path information may not be accurate for dest-port 2152 and 2123, used by GTP, and dest-port 4789, used by VXLAN, as the hash calculation may take the GTP Tunnel Identifer and VXLAN's encapsulated Ethernet and IP headers into account.

**Parameter table**

+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| Parameter | Description                                                                                                                                                         | Range                           | Default                |
+===========+=====================================================================================================================================================================+=================================+========================+
| ipv4/ipv6 | Address-family for the flow for which to display exact-path                                                                                                         | IPv4                            | \-                     |
|           |                                                                                                                                                                     | IPv6                            |                        |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| src-ip    | The source address in the IP header of the packets                                                                                                                  | A.B.C.D/xx:xx::xx:xx            | \-                     |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| dest-ip   | The destination address in the IP header of the packets                                                                                                             | A.B.C.D/xx:xx::xx:xx            | \-                     |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| protocol  | The protocol used for the flow                                                                                                                                      | TCP - for 5-tuple IP flows      | \-                     |
|           |                                                                                                                                                                     | UDP - for 5-tuple IP flows      |                        |
|           |                                                                                                                                                                     | any-host - for 3-tuple IP flows |                        |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| src-port  | The source port of the UDP/TCP flows                                                                                                                                | 0..65535                        | \-                     |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| dest-port | The destination port of the UDP/TCP flows                                                                                                                           | 0..65535                        | \-                     |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| dscp      | Filters the display to a specific DSCP value                                                                                                                        | 0..63                           | 0                      |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| vrf       | Filters the display to a specific VRF                                                                                                                               | an existing VRF instance        | default                |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| ncp-id    | Filters the display to a specific NCP                                                                                                                               | 0..255                          | NCP with the lowest ID |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+
| detail    | Displays detailed information (e.g. information about up to two ECMP levels, Class Based Tunnel Selection (CBTS), and Link Aggregation (LAG) on the displayed path. | \-                              | \-                     |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+------------------------+

**Example**
::

    dnRouter#show route exact-path ipv4 src-ip 1.1.1.1 dest-ip 2.2.2.2 protocol any-host

    interface: ge100-2/0/3 (1 of 4 in bundle-1)
    next-hop: connected
    mpls labels: N/A


    dnRouter#show route exact-path ipv4 src-ip 10.1.1.1 dest-ip 10.2.2.2 protocol any-host vrf customer1 detail

    NCP-ID: 1
    VRF: customer1
    Path Forwarding Information:
    next-hop: 4.4.4.4 (1 of 2)
    mpls labels: 1001
    hash: 0xDF34
       next-hop: 3.3.3.3 (1 of 2)
       mpls labels:  8156(top), 4332
       via tunnel_18 tunnel bypass tunnel oid 603
       via bypass_3 oid 703
       interface: bundle-3
       hash: 0x3221
         interface: ge100-2/0/3 (1 of 4)
         hash: 0x7358

.. **Help line:** show route load-balancing hash result

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 11.2    | Command introduced                  |
+---------+-------------------------------------+
| 11.5    | Replaced "host-any" with "any-host" |
+---------+-------------------------------------+


