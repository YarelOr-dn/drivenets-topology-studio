show multicast route
--------------------

**Minimum user role:** viewer

You can use this command to display the multicast routing table. The Multicast Route table includes IP Multicast route entries created by PIM, IGMP and various Group Range configurations such as RP ranges and SSM range.

**Command syntax: show multicast route** group-range [group-range] source [source]

**Command mode:** operational



**Note**

- MoFRR Standby Multicast Counters: The MoFRR Standby counters are used by the operator to obtain indication of (S,G) traffic reception via the standby upstream multicast hop (UMH).

- For group-range parameter output shall be displayed for exact match. If a prefix is not specified then by default output shall be filtered for /32 group prefix.

Multicast Route Flags:

  - Per Entry Flags:

  - I - Inform about (S.G) packet arrival on incoming interfaces with flag I

  - R - Generate Wrong RPF events (Count the RPF events for (S.G)

  - D - Drop packets coming to this group on incoming interface(s)

  - P - Punt packets arriving on Incoming interfaces from Directly-Connected Check to CPU for sending PIM Reg

  - F - Failed to install this Multicast (S,G) state due to reaching configured limitation or due to lack of resources

  - FR - MoFRR protected multicast entry.

  - Per Interface flags:

  - A - Accept and forward packets arriving on the incoming interfaces to the OIL (Outgoing Interface List)

  - I - Inform the NCP for packet arriving on a this incoming interface

  - F - Forward a copy on the incoming packet to this OIL interface member

  - D - Drop packets arriving on this incoming interface

  - P - Punt packets arriving on the interface to CPU e.g. for sending PIM Reg

  - SB - Standby MoFRR interface

  - FSB - Failed to install standby MoFRR interface due to reaching configured limitation or due to lack of resources

**Parameter table**

+-------------+--------------------------------------------------------------------------------------+------------------------------+---------+
| Parameter   | Description                                                                          | Range                        | Default |
+=============+======================================================================================+==============================+=========+
| group-range | Displays a specific group or various group address ranges, such as RP and SSM ranges | A.B.C.D                      | \-      |
|             |                                                                                      | A.B.C.D/M                    |         |
+-------------+--------------------------------------------------------------------------------------+------------------------------+---------+
| source      | Displays a specific source various group address ranges, such as RP and SSM ranges   | A.B.C.D                      | \-      |
+-------------+--------------------------------------------------------------------------------------+------------------------------+---------+

**Example**
::

  dnRouter# show multicast route

  IP Multicast Routing Information Base
  Legend: Entry flags: I - Inform about (S.G) packet arrival on incoming interfaces with flag I,
                       R - Generate Wrong RPF events (Count the RPF events for (S.G),
                       D - Drop packets coming to this group on incoming interface(s).
                       P - Punt packets arriving on Incoming interfaces from Directly-Connected Check to CPU for sending PIM Reg
                       F - Failed to install this Multicast (S,G) state due to reaching configured limitation or due to lack of resources
                       FR - MoFRR protected multicast route entry
          Interface flags: A - Accept and forward packets arriving on the incoming interfaces to the OIL (Outgoing Interface List)
                           I - Inform the NCP for packet arriving on a this incoming interface.
                           F - Forward a copy on the incoming packet to this OIL interface member
                           D - Drop packets arriving on this incoming interface.
                           P - Punt packets arriving on the interface to CPU e.g. for sending PIM Reg
                           SB - Standby MoFRR interface
                           FSB - Failed to install standby MoFRR interface due to reaching configured limitation or due to lack of resources

  ( *, 224.0.0.0/4) RPF neighbor: 12.2.61.1 Flags: P
    Uptime: 01:09:40
    Incoming Interfaces:
      Any,        Flags: P
    Outgoing Interfaces:
    Counters:
      Forwarded octets: 0, (0 bps / 0 Mbps)
      Forwarded frames: 0, (0 fps / 0 Mfps)
      Punted packets: 0
      Wrong RPF packets: 0

  ( *, 224.0.0.0/24) Flags: D
    Uptime: 01:09:44
    Incoming Interfaces:
      Any,        Flags: D
    Outgoing Interfaces:
    Counters:
      Forwarded octets: 0, (0 bps / 0 Mbps)
      Forwarded frames: 0, (0 fps / 0 Mfps)
      Punted packets: 0
      Wrong RPF packets: 0

  ( *, 224.0.1.39) Flags: P
    Uptime: 01:09:44
    Incoming Interfaces:
      Any,        Flags: P
    Outgoing Interfaces:
    Counters:
      Forwarded octets: 0, (0 bps / 0 Mbps)
      Forwarded frames: 0, (0 fps / 0 Mfps)
      Punted packets: 0
      Wrong RPF packets: 0

  ( *, 227.0.0.0/8) RPF neighbor: 61.61.61.61 Flags: P
    Uptime: 01:09:40
    Incoming Interfaces:
      Any,        Flags: P
    Outgoing Interfaces:
    Counters:
      Forwarded octets: 0, (0 bps / 0 Mbps)
      Forwarded frames: 0, (0 fps / 0 Mfps)
      Punted packets: 0
      Wrong RPF packets: 0

  ( *, 227.1.1.1) RPF neighbor: 61.61.61.61 Flags: I
    Uptime: 01:09:33
    Incoming Interfaces:
      Any,        Flags: A, I
    Outgoing Interfaces:
      bundle-12,  Flags: F
      bundle-13,  Flags: F
      bundle-14,  Flags: F
      bundle-15,  Flags: F
    Counters:
      Forwarded octets: 0, (0 bps / 0 Mbps)
      Forwarded frames: 0, (0 fps / 0 Mfps)
      Punted packets: 0
      Wrong RPF packets: 0

  ( 1.1.1.1, 227.1.1.1) RPF neighbor: 12.1.61.1 Flags: R, I
    Uptime: 00:00:30
    Incoming Interfaces:
      bundle-10,  Flags: A
      bundle-13,  Flags: I
    Outgoing Interface List
      bundle-12,  Flags: F
      bundle-15,  Flags: F
    Counters:
      Forwarded octets: 0, (0 bps / 0 Mbps)
      Forwarded frames: 0, (0 fps / 0 Mfps)
      Punted packets: 0
      Wrong RPF packets: 0

  ( *, 229.0.0.0/8) RPF neighbor: 12.61.62.2 Flags: P
    Uptime: 01:09:40
    Incoming Interfaces:
      Any,        Flags: P
    Outgoing Interfaces:
    Counters:
      Forwarded octets: 0, (0 bps / 0 Mbps)
      Forwarded frames: 0, (0 fps / 0 Mfps)
      Punted packets: 0
      Wrong RPF packets: 0

  ( *, 229.1.1.1) RPF neighbor: 12.61.62.2 Flags: I, R
    Uptime: 01:09:30
    Incoming Interfaces:
      bundle-12,   Flags: A, I
    Outgoing Interface List
      bundle-15,   Flags: F
    Counters:
      Forwarded octets: 0, (0 bps / 0 Mbps)
      Forwarded frames: 0, (0 fps / 0 Mfps)
      Punted packets: 0
      Wrong RPF packets: 0

  ( *, 230.0.0.0/8) RPF neighbor: 12.61.62.2 Flags: P
    Uptime: 01:09:40
    Incoming Interfaces:
      Any,        Flags: P
    Outgoing Interfaces:
    Counters:
      Forwarded octets: 0, (0 bps / 0 Mbps)
      Forwarded frames: 0, (0 fps / 0 Mfps)
      Punted packets: 0
      Wrong RPF packets: 0

  ( *, 230.1.1.1) RPF neighbor: 12.61.62.2 Flags: I
    Uptime: 01:09:30
    Incoming Interfaces:
      bundle-12,        Flags: A, I
    Outgoing Interfaces:
      bundle-15,        Flags: F
    Counters:
      Forwarded octets: 0, (0 bps / 0 Mbps)
      Forwarded frames: 0, (0 fps / 0 Mfps)
      Punted packets: 0
      Wrong RPF packets: 0

  ( *, 232.0.0.0/8) Flags: D
    Uptime: 01:09:43
    Incoming Interfaces:
      Any,        Flags: D
    Outgoing Interfaces:
    Counters:
      Forwarded octets: 0, (0 bps / 0 Mbps)
      Forwarded frames: 0, (0 fps / 0 Mfps)
      Punted packets: 0
      Wrong RPF packets: 0

  ( 1.1.1.1, 232.1.1.1) RPF neighbor: 12.1.61.1 Flags: R
    Uptime: 01:09:30
    Incoming Interfaces:
      bundle-13,        Flags: A
    Outgoing Interfaces:
      bundle-12,        Flags: F
    Counters:
      Forwarded octets: 0, (0 bps / 0 Mbps)
      Forwarded frames: 0, (0 fps / 0 Mfps)
      Punted packets: 0
      Wrong RPF packets: 0

  ( 1.2.3.4, 232.3.2.1) RPF neighbor: 12.1.61.1 Flags: R, FR
    Uptime: 01:09:30
    Incoming Interfaces:
      bundle-23,        Flags: A
      bundle-32,        Flags: A, SB
    Outgoing Interfaces:
      bundle-102,        Flags: F
      bundle-103,        Flags: F
      bundle-104,        Flags: F
    Counters:
       Forwarded octets: 3456234212, (2312321 bps / 0 Mbps)
       Forwarded frames: 123231, ( 212fps / 0 Mfps)
       Punted packets: 0
       Wrong RPF packets: 0
       MoFRR Standby counters
         Received octets: 345623421, (2312321 bps / 54322 Mbps)
         Received frames: 123231, ( 212fps / 0 Mfps)

  ( 4.4.4.4, 225.3.2.1) RPF neighbor: 12.1.61.1 Flags: R, FR
    Uptime: 01:09:30
    Incoming Interfaces:
      bundle-23,        Flags: A
      bundle-32,        Flags: A, SB
    Outgoing Interfaces:
      bundle-102,        Flags: F
      bundle-103,        Flags: F
      bundle-104,        Flags: F
    Counters:
       Forwarded octets: 3456234212, (2312321 bps / 0 Mbps)
       Forwarded frames: 123231, ( 212fps / 0 Mfps)
       Punted packets: 0
       Wrong RPF packets: 0
       MoFRR Standby counters
         Received octets: 345623421, (2312321 bps / 54322 Mbps)
         Received frames: 123231, ( 212fps / 0 Mfps)


  dnRouter# show multicast route group-range 227.0.0.0/8

  IP Multicast Routing Information Base
  Legend: Entry flags: I - Inform about (S.G) packet arrival on incoming interfaces with flag I,
                       R - Generate Wrong RPF events (Count the RPF events for (S.G),
                       D - Drop packets coming to this group on incoming interface(s).
                       P - Punt packets arriving on Incoming interfaces from Directly-Connected Check to CPU for sending PIM Reg
                       F - Failed to install this Multicast (S,G) state due to reaching configured limitation or due to lack of resources
                       FR - MoFRR protected multicast route entry
          Interface flags: A - Accept and forward packets arriving on the incoming interfaces to the OIL (Outgoing Interface List)
                           I - Inform the NCP for packet arriving on a this incoming interface.
                           F - Forward a copy on the incoming packet to this OIL interface member
                           D - Drop packets arriving on this incoming interface.
                           P - Punt packets arriving on the interface to CPU e.g. for sending PIM Reg
                           SB - Standby MoFRR interface
                           FSB - Failed to install standby MoFRR interface due to reaching configured limitation or due to lack of resources

  ( *, 227.0.0.0/8) RPF neighbor: 61.61.61.61 Flags: P
    Uptime: 01:09:40
    Incoming Interfaces:
      Any,        Flags: P
    Outgoing Interfaces:
    Counters:
      Forwarded octets: 0, (0 bps / 0 Mbps)
      Forwarded frames: 0, (0 fps / 0 Mfps)
      Punted packets: 0
      Wrong RPF packets: 0


  dnRouter# show multicast route group-range 227.1.1.1

  IP Multicast Routing Information Base
  Legend: Entry flags: I - Inform about (S.G) packet arrival on incoming interfaces with flag I,
                       R - Generate Wrong RPF events (Count the RPF events for (S.G),
                       D - Drop packets coming to this group on incoming interface(s).
                       P - Punt packets arriving on Incoming interfaces from Directly-Connected Check to CPU for sending PIM Reg
                       F - Failed to install this Multicast (S,G) state due to reaching configured limitation or due to lack of resources
                       FR - MoFRR protected multicast route entry
          Interface flags: A - Accept and forward packets arriving on the incoming interfaces to the OIL (Outgoing Interface List)
                           I - Inform the NCP for packet arriving on a this incoming interface.
                           F - Forward a copy on the incoming packet to this OIL interface member
                           D - Drop packets arriving on this incoming interface.
                           P - Punt packets arriving on the interface to CPU e.g. for sending PIM Reg
                           SB - Standby MoFRR interface
                           FSB - Failed to install standby MoFRR interface due to reaching configured limitation or due to lack of resources

  ( *, 227.1.1.1) RPF neighbor: 61.61.61.61 Flags: I
    Uptime: 01:09:33
    Incoming Interfaces:
      Any,        Flags: A, I
    Outgoing Interfaces:
      bundle-12,  Flags: F
      bundle-13,  Flags: F
      bundle-14,  Flags: F
      bundle-15,  Flags: F
    Counters:
      Forwarded octets: 0, (0 bps / 0 Mbps)
      Forwarded frames: 0, (0 fps / 0 Mfps)
      Punted packets: 0
      Wrong RPF packets: 0

  ( 1.1.1.1, 227.1.1.1) RPF neighbor: 12.1.61.1 Flags: R, I
    Uptime: 00:00:30
    Incoming Interfaces:
      bundle-10,  Flags: A
      bundle-13,  Flags: I
    Outgoing Interface List
      bundle-12,  Flags: F
      bundle-15,  Flags: F
    Counters:
      Forwarded octets: 0, (0 bps / 0 Mbps)
      Forwarded frames: 0, (0 fps / 0 Mfps)
      Punted packets: 0
      Wrong RPF packets: 0


  dnRouter# show multicast route group-range 227.1.1.1 source 1.1.1.1

  IP Multicast Routing Information Base
  Legend: Entry flags: I - Inform about (S.G) packet arrival on incoming interfaces with flag I,
                       R - Generate Wrong RPF events (Count the RPF events for (S.G),
                       D - Drop packets coming to this group on incoming interface(s).
                       P - Punt packets arriving on Incoming interfaces from Directly-Connected Check to CPU for sending PIM Reg
                       F - Failed to install this Multicast (S,G) state due to reaching configured limitation or due to lack of resources
                       FR - MoFRR protected multicast route entry
          Interface flags: A - Accept and forward packets arriving on the incoming interfaces to the OIL (Outgoing Interface List)
                           I - Inform the NCP for packet arriving on a this incoming interface.
                           F - Forward a copy on the incoming packet to this OIL interface member
                           D - Drop packets arriving on this incoming interface.
                           P - Punt packets arriving on the interface to CPU e.g. for sending PIM Reg
                           SB - Standby MoFRR interface
                           FSB - Failed to install standby MoFRR interface due to reaching configured limitation or due to lack of resources

  ( 1.1.1.1, 227.1.1.1) RPF neighbor: 12.1.61.1 Flags: R, I
    Uptime: 00:00:30
    Incoming Interfaces:
      bundle-10,  Flags: A
      bundle-13,  Flags: I
    Outgoing Interface List
      bundle-12,  Flags: F
      bundle-15,  Flags: F
    Counters:
      Forwarded octets: 0, (0 bps / 0 Mbps)
      Forwarded frames: 0, (0 fps / 0 Mfps)
      Punted packets: 0
      Wrong RPF packets: 0


.. **Help line:** Show Multicast Route table

**Command History**

+---------+------------------------------------------------------------------------------+
| Release | Modification                                                                 |
+=========+==============================================================================+
| 12.0    | Command introduced                                                           |
+---------+------------------------------------------------------------------------------+
| 14.0    | Updated MoFRR support                                                        |
+---------+------------------------------------------------------------------------------+
| 16.1    | Added source address filter                                                  |
+---------+------------------------------------------------------------------------------+
| 19.1    | Added a new flag to indicate installation failure of standby MoFRR interface |
+---------+------------------------------------------------------------------------------+
