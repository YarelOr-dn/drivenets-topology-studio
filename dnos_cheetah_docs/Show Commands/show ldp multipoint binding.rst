show ldp multipoint binding
---------------------------

**Minimum user role:** viewer

To display the content of the label information base (LIB) for mLDP bindings:



**Command syntax: show ldp multipoint binding** [binding-type] {root-address [root-address] | opaque-value [opaque-value] | in-label [mpls-label]}

**Command mode:** operational



.. **Note**


**Parameter table**

+----------------+----------------------------------------------------------------------------------------------+------------+
| Parameter      | Description                                                                                  | Range      |
+================+==============================================================================================+============+
| binding-type   | Optionally filters output per the specified binding type                                     | p2mp       |
+----------------+----------------------------------------------------------------------------------------------+------------+
| root-address   | Optionally filters output per the specified root node IP address                             | A.B.C.D    |
+----------------+----------------------------------------------------------------------------------------------+------------+
| opaque-value   | Optionally filters output per the specified opaque value                                     |            |
|                | root-address + opaque-value filters used together can be used to match to mLDP FEC           |            |
+----------------+----------------------------------------------------------------------------------------------+------------+
| mpls-label     | Optionally filters the output to a matching ingress label                                    | 0..1048575 |
+----------------+----------------------------------------------------------------------------------------------+------------+

**Example**
::

    dnRouter# show ldp multipoint binding p2mp

    Root: 10.10.10.10    Root type: IPv4    LSP type: P2MP
        Opaque length: 4 bytes, Opaque value: 01 0004 0A0B0C0D
        Opaque decoded: [Generic LSP Id: 168496141]
        Upstream session(s):
            6.6.6.6 [Active]
                In label: 26001, Binding uptime: 00:00:08
        Downstream:
            LDP Peer    Forwarding Interface    Nexthop          Label          Uptime
            --------    --------------------    -------          -----          ------
            3.3.3.3     ge100-1/0/1             13.1.1.3         57236          00:00:08 (installed)

    Root: 10.10.10.10   Root type: IPv4   LSP type: P2MP
        Opaque length: 8 bytes, Opaque value: 03 0008 0A0B0C0D1A1B1C1D
        Opaque decoded: [IPv4 Source: Source: 10.11.12.13  Group: 26.27.28.29]
        Upstream session(s):
            1.1.1.1/32      [Active]
                In label: 26002, Binding uptime: 00:00:03
            2.2.2.2/32      [MBB candidate]
                In label: 26003
        Downstream:
            LDP Peer      Forwarding Interface          Nexthop          Label         Uptime
            --------      --------------------          -------          -----         ------
            5.5.5.5          ge100-1/0/1                56.0.0.5         57254         00:00:04 (installed)
            6.6.6.6          ge100-2/0/1                16.0.0.10        57267         00:00:29 (installed, stale)

    Root: 20.20.20.20   Root type: IPv4   LSP type: P2MP
        Opaque length: 32 bytes, Opaque value: 04 0020 220102030405060708090A0B0C0D0E0F33111213141E1F
        Opaque decoded: [IPv6 Source: Source: 2201:203:405:607:809:a0b:c0d:e0f Group: 3311:1213:1415:1617:1819:1a1b:1c1d:1e1f]
        Upstream session(s):
            1.1.1.1/32      [Active]
                In label: 26004, Binding uptime: 00:00:03
            2.2.2.2/32      [candidate]
                In label: 26005
        Downstream:
            LDP Peer      Forwarding Interface          Nexthop          Label         Uptime
            --------      --------------------          -------          -----         ------
            5.5.5.5          ge100-1/0/1                56.0.0.5         57454         00:00:04 (installed)
            6.6.6.6          ge100-2/0/1                16.0.0.10        57467         00:00:29 (installed)


    dnRouter# show ldp multipoint binding p2mp root-address 20.20.20.20

    Root: 20.20.20.20   Root type: IPv4   LSP type: P2MP
        Opaque length: 32 bytes, Opaque value: 04 0020 220102030405060708090A0B0C0D0E0F33111213141E1F
        Opaque decoded: [IPv6 Source: Source: 2201:203:405:607:809:a0b:c0d:e0f Group: 3311:1213:1415:1617:1819:1a1b:1c1d:1e1f]
        Upstream session(s):
            1.1.1.1/32      [Active]
                In label: 26004, Binding uptime: 00:00:03
            2.2.2.2/32      [candidate]
                In label: 26005
        Downstream:
            LDP Peer      Forwarding Interface          Nexthop          Label         Uptime
            --------      --------------------          -------          -----         ------
            5.5.5.5          ge100-1/0/1                56.0.0.5         57454         00:00:04 (installed)
            6.6.6.6          ge100-2/0/1                16.0.0.10        57467         00:00:29 (installed)


    dnRouter# show ldp multipoint binding p2mp in-label 26001

    Root: 10.10.10.10    Root type: IPv4    LSP type: P2MP
        Opaque length: 4 bytes, Opaque value: 01 0004 0A0B0C0D
        Opaque decoded: [Generic LSP Id: 168496141]
        Upstream session(s):
            6.6.6.6 [Active]
                In label: 26001, Binding uptime: 00:00:08
        Downstream:
            LDP Peer    Forwarding Interface    Nexthop          Label          Uptime
            --------    --------------------    -------          -----          ------
            3.3.3.3     ge100-1/0/1             13.1.1.3         57236          00:00:08 (installed)


    dnRouter# show ldp multipoint binding p2mp root-address 10.10.10.10 opaque-value 0300080A0B0C0D1A1B1C1D

    Root: 10.10.10.10   Root type: IPv4   LSP type: P2MP
        Opaque length: 8 bytes, Opaque value: 03 0008 0A0B0C0D1A1B1C1D
        Opaque decoded: [IPv4 Source: Source: 10.11.12.13  Group: 26.27.28.29]
        Upstream session(s):
            1.1.1.1/32      [Active]
                In label: 26002, Binding uptime: 00:00:03
            2.2.2.2/32      [MBB candidate]
                In label: 26003
        Downstream:
            LDP Peer      Forwarding Interface          Nexthop          Label         Uptime
            --------      --------------------          -------          -----         ------
            5.5.5.5          ge100-1/0/1                56.0.0.5         57254         00:00:04 (installed)
            6.6.6.6          ge100-2/0/1                16.0.0.10        57267         00:00:29 (installed, stale)


.. **Help line:** Displays the contents of the LIB

**Command History**

+---------+-------------------------------------------------------------------------+
| Release | Modification                                                            |
+=========+=========================================================================+
| 17.1    | Command introduced                                                      |
+---------+-------------------------------------------------------------------------+
