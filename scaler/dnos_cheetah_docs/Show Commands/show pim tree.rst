show pim tree
-------------

**Minimum user role:** viewer

You can use this command to display the PIM Tree Information Database entries. If no parameter is entered, all PIM tree information base entries will be displayed. Optionally, a group address may be provided. If only the Group address is provided, all relevant (\*,G) and (S,G) entries with the same Group will be displayed. When both Group and Source are provided, either a single (S,G) SSM entry will be displayed or a single entry for (S,G,RPT) and (S,G,SPT) will be displayed. Entring only a source (Unicast IP address) will display no entry.



**Command syntax: show pim tree** group [group] source [source]

**Command mode:** operational



**Note**

- When the group address is specified, all PIM tree entries with this group address will be displayed.

- The Source address is optionally expected when a group address is entered. The Source address cannot be provided alone.

- (S, G) [SM /SSM] : Entry state. Source address, Group address, the tree mode [SM or SSM] and in case of SM: per interface indication if inherited from shared RP tree (SPT) or if moved to SPT. Entry Uptime: [Hours:Min:sec]. How long does the entry exist.

- RP address (If the Entry is SM).

- Upstream Join/Prune state (+ time [Hours:Min:Sec] or "Not Sent") + RPF interface + previous hop IP address.

- Per PIM Tree entry information / flags: KA - Keep Alive Time [Hours:Min:Sec] for PIM (S,G) SM entry (S,G, RPT) that are data driven or (S,G ,SPT) entries on routers that moved from RPT to SPT after timeout.

.. - When group address is specified all the PIM tree entries with this group address shall be displayed.

  - Source address is optionally expected when a group address is written. Source address may not be provided alone.

  - (S, G) [SM /SSM] : Entry state. Source address, group address, the tree mode [SM or SSM] and in case of SM: per interface indication if inherited from shared RP tree (SPT) or if moved to SPT. Entry Uptime: [Hours:Min:sec]. How long does the entry exist.

  - RP address (If the Entry is SM).

  - Upstream Join/Prune state (+ time [Hours:Min:Sec] or "Not Sent") + RPF interface + previous hop IP address.  

  - Per PIM Tree entry information / flags: KA - Keep Alive Time [Hours:Min:Sec] for PIM (S,G) SM entry (S,G, RPT) that are data driven or (S,G ,SPT) entries on routers that moved from RPT to SPT after timeout.

**Parameter table**

+-----------+--------------------------------------------------------------------------------------+--------------+----------+
| Parameter | Description                                                                          | Range        | Default  |
+===========+======================================================================================+==============+==========+
| group     | Filters output for a specific group address (only IPv4 family address is supported)  | A.B.C.D      | \-       |
+-----------+--------------------------------------------------------------------------------------+--------------+----------+
| source    | Filters output for a specific source address (only IPv4 family address is supported) | A.B.C.D      | \-       |
+-----------+--------------------------------------------------------------------------------------+--------------+----------+

The following describes the PIM entry flags:

+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter                    | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
+==============================+==========================================================================================================================================================================================================================================================================================================================================================================================================================================================================================+
| KA                           | The keepalive timer is set for Data driven traffic PIM Tree entries (e.g. (S,G, RPT) entries. The KA timer tracks whether the related data driven PIM Tree (S,G) entry traffic is still flowing. The PIM tree entry does not time out as long as the keep alive timer is running. It runs for 3 minutes than probed for 2 minutes for traffic. If during the probing time no traffic is seen than the PIM tree entry is removed as there is no longer any reason to keep the Tree entry. |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| AL - Alive                   | Indicates whether the data driven PIM Tree is still alive or after a few rate calculation rounds, in which no traffic increase is measured, it is still assumed alive (AS).                                                                                                                                                                                                                                                                                                              |
| AS - Assumed Alive           |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| RR - Register Received       | Indication whether a PIM register was received and answered  for the relevant (S,G).                                                                                                                                                                                                                                                                                                                                                                                                     |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| MSA - MSDP-SA                | Received Indicates whether an MSDP SA message was received for the specific (S,G) entry                                                                                                                                                                                                                                                                                                                                                                                                  |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| LH - Last hop Flag           | Indicates that this Router is the last hop on this tree  (I.e. this router serves as a last hop for the entry. If the (S, G) outgoing interface list is inherited from a (\*,G) route, the LH flag is set on the (\*,G) outgoing LH interface as well)                                                                                                                                                                                                                                   |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| SR - Sending Register        | Indication whether a PIM register was sent for the relevant (S,G).                                                                                                                                                                                                                                                                                                                                                                                                                       |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Per Ingress Interface Information                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Uptime                       | Uptime (Days X, HH:MM:SS)                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Status                       | Interface status Receiving (Rcv) traffic for forwarding or Waiting for (S,G) traffic from RFP(s) in case of transition.                                                                                                                                                                                                                                                                                                                                                                  |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Joined state                 | Join/Prune (Holdtime: HH:MM:SS)                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Per Ingress Interface Flags                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| R                            | Joined towards RPF(RP)                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| S                            | Joined towards RPF(S)                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| AB - Administrative Boundary | Indicates that forwarding on this interface is blocked by a configured administrative boundary for this entry’s group range. This means that Join( \*S, G) was not sent upstream.                                                                                                                                                                                                                                                                                                        |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Per Outgoing Interface Information                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Uptime                       | Uptime (Days X, HH:MM:SS)                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Status                       | Status forwarding (Fwd) traffic / NotForwarding (NoFwd)                                                                                                                                                                                                                                                                                                                                                                                                                                  |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Joined state                 | Join/Prune (Holdtime: HH:MM:SS)                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Per OIL Interface Flags                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| I                            | Inherited from (\*,G)                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| AB - Administrative Boundary | Indicates that forwarding on this interface is blocked by a configured administrative boundary for this entry’s group range. This will be applicable for received Join( \*S, G).                                                                                                                                                                                                                                                                                                         |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| T                            | Turnaround proxy behavior. The turn around router transmits the S,G traffic received from the sender to this port (which Join(\*,G)) on behalf of the RP.                                                                                                                                                                                                                                                                                                                                |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| LH - Last hop Flag           | indicates that this Router is the last hop on this tree  (I.e. this router serves as a last hop for the entry. If the (S, G) outgoing interface list is inherited from a (\*,G) route, the LH flag is set on the (\*,G) outgoing LH interface as well)                                                                                                                                                                                                                                   |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| AS - Assert seen             | A PIM assert message was seen on this interface, i.e. an active PIM assert state exists                                                                                                                                                                                                                                                                                                                                                                                                  |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| L - Local Receiver           | Indicates that there are local receivers for this entry on the related interface                                                                                                                                                                                                                                                                                                                                                                                                         |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

  dnRouter# show pim tree

  IP PIM Tree Information Base

   Legend: PIM Entry: (\*/S,G)SM/SSM / State Uptime / RP address
          PIM Entry Types: SM-Sparse Mode, RPT SM - Shared tree, SSM - Source specific Mode,
          PIM Entry Flags:
            I - Inherited from (\*,G), KA - Keep Alive Timer(Time),
            AL - Currently Alive, As - Assumed to be Alive,
            RR - Register Received(Time), MSA - MSDP-SA Received,
            LH - Last Hop, SR - Sending Registers,
            FR - MoFRR enabled entry
          Out/In Interface state: Interface Name, Uptime(Time), status: OutIf: Fwd/NoFwd InIf:Rcv/Listen, JoinPrune(Time) or NotJoined or IgmpRep(Time)
          In Interface flags: R - Joined towards RPF(RP), S - Joined towards RPF(S), AB - Admin Boundary, F - Failed RPF, P - Prune Pending Timer(Time), FR(P) - MoFRR primary interface, FR(SB) - MoFRR Standby interface
          Out Interface flags: I - inherited from (*,G), AB - Admin Boundary, T - Turnaround, LH - Last Hop, AS - Assert

  ( *, 227.1.1.1) SM, Uptime: 0 days, 01:09:57, RP-Address: 61.61.61.61
  Upstream Join/Prune: None, RPF: 61.61.61.61, Flags:
  Incoming Interface:
    lo0,             Uptime: 0 days, 03:00:55,  status: Rcv, RP(G),                    Flags:
  Output Interface List:
    bundle-12,       Uptime: 0 days, 01:09:57,  status: Fwd, Join(HoldTime: 00:02:30), Flags:
    bundle-13,       Uptime: 0 days, 01:09:55,  status: Fwd, Join(HoldTime: 00:02:34), Flags:
    bundle-14,       Uptime: 0 days, 01:09:57,  status: Fwd, Join(HoldTime: 00:02:46), Flags:
    bundle-15,       Uptime: 0 days, 01:09:57,  status: Fwd, Join(HoldTime: 00:02:32), Flags:

  ( 1.1.1.1, 227.1.1.1) SM, Uptime: 0 days, 00:00:55, RP-Address: 61.61.61.61
  Upstream Join/Prune: Join(HoldTime: 00:03:15), RPF: 12.1.61.1, Flags: KA(00:02:47), AL, RR(00:03:51)
  Incoming Interface:
    bundle-23,      Uptime: 0 days, 00:00:45,  status: Rcv,    Join(HoldTime: 00:03:15),  Flags: S
  Output Interface List:
    bundle-12,      Uptime: 0 days, 00:00:55,  status: NoFwd,  Prune(HoldTime: 00:02:34), Flags:
    bundle-13,      Uptime: 0 days, 00:00:43,  status: Fwd,    Join(HoldTime: 00:02:46),  Flags:
    bundle-14,      Uptime: 0 days, 00:00:14,  status: Fwd,    Join(HoldTime: 00:03:15),  Flags: I
    bundle-15,      Uptime: 0 days, 00:00:43,  status: Fwd,    Join(HoldTime: 00:02:46),  Flags: I

  ( *, 229.1.1.1) SM, Uptime: 0 days, 01:09:54, RP-Address: 5.5.5.5
  Upstream Join/Prune: Join(Time 00:00:13), RPF: 12.61.62.2, Flags:
  Incoming Interface:
    bundle-102,     Uptime: 0 days, 00:00:45,  status: Rcv, Join(HoldTime: 00:03:15), Flags: R, F
  Output Interface List:
    bundle-25,      Uptime: 0 days, 01:09:54,  status: Fwd,    Join(HoldTime: 00:02:32), Flags:
    bundle-12,      Uptime: 0 days, 00:00:55,  status: Fwd,    Join(HoldTime: 00:02:34), Flags:
    bundle-14,      Uptime: 0 days, 00:00:14,  status: Fwd,    Join(HoldTime: 00:03:15),  Flags:
    bundle-15,      Uptime: 0 days, 00:00:43,  status: Fwd,    Join(HoldTime: 00:02:46),  Flags:

  ( 1.1.1.1, 229.1.1.1) SM, Uptime: 0 days, 00:00:55, RP-Address: 5.5.5.5
  Upstream Join/Prune: Join(HoldTime: 00:03:15), RPF: 12.61.62.2, Flags: KA(00:02:47), AL
  Incoming Interface:
    bundle-13,      Uptime: 0 days, 00:00:45,  status: Lsn,    Join(HoldTime: 00:00:03),  Flags: S, P(00:09:59)
    bundle-23,      Uptime: 0 days, 00:00:45,  status: Rcv,    Join(HoldTime: 00:03:15),  Flags: R
  Output Interface List:
    bundle-25,      Uptime: 0 days, 01:09:54,  status: NoFwd,  Prune(HoldTime: 00:02:32), Flags:
    bundle-12,      Uptime: 0 days, 00:00:55,  status: NoFwd,  Prune(HoldTime: 00:02:34), Flags:
    bundle-14,      Uptime: 0 days, 00:00:14,  status: Fwd,    Join(HoldTime: 00:03:15),  Flags: I T
    bundle-15,      Uptime: 0 days, 00:00:43,  status: Fwd,    Join(HoldTime: 00:02:46),  Flags:

  ( 1.1.1.1, 232.1.1.1)SSM Uptime: 0 days, 01:09:54
  Upstream Join/Prune: Join(HoldTime 00:00:13), RPF: 12.1.61.1, Flags:
  Incoming Interface:
    bundle-23,      Uptime: 0 days, 01:10:45,  status: Rcv, Join(HoldTime: 00:03:15), Flags: S
  Output Interface List:
    bundle-102,     Uptime: 0 days, 01:09:54,  status: Fwd, Join(HoldTime: 00:02:40), Flags:

  ( 1.2.3.4, 232.3.2.1)SSM Uptime: 0 days, 01:09:54
  Upstream Join/Prune: Join(HoldTime 00:00:13), RPF: 12.1.61.1, Flags: FR
  Incoming Interface:
    bundle-23,      Uptime: 0 days, 01:10:45,  status: Rcv, Join(HoldTime: 00:03:15), Flags: S, FR(P)
    bundle-32,      Uptime: 0 days, 01:10:42,  status: Lsn, Join(HoldTime: 00:03:15), Flags: S, FR(SB)
  Output Interface List:
    bundle-102,     Uptime: 0 days, 01:09:54,  status: Fwd, Join(HoldTime: 00:02:40), Flags:
    bundle-103,     Uptime: 0 days, 01:09:54,  status: Fwd, Join(HoldTime: 00:02:40), Flags:
    bundle-104,     Uptime: 0 days, 01:09:54,  status: Fwd, Join(HoldTime: 00:02:40), Flags:

  dnRouter#

  dnRouter# show pim tree group 227.1.1.1 source 1.1.1.1

  IP PIM Tree Information Base for Group: 227.1.1.1, Source 1.1.1.1

   Legend: PIM Entry: (\*/S,G)SM/SSM / State Uptime / RP address
          PIM Entry Types: SM-Sparse Mode, RPT SM - Shared tree, SSM - Source specific Mode,
          PIM Entry Flags:
            I - Inherited from (\*,G), KA - Keep Alive Timer(Time),
            AL - Currently Alive, As - Assumed to be Alive,
            RR - Register Received(Time), MSA - MSDP-SA Received,
            LH - Last Hop, SR - Sending Registers,
            FR - MoFRR enabled entry
          Out/In Interface state: Interface Name, Uptime(Time), status: OutIf: Fwd/NoFwd InIf:Rcv/Listen, JoinPrune(Time) or NotJoined or IgmpRep(Time)
          In Interface flags: R - Joined towards RPF(RP), S - Joined towards RPF(S), AB - Admin Boundary, F - Failed RPF, P - Prune Pending Timer(Time), FR(P) - MoFRR primary interface, FR(SB) - MoFRR Standby interface
          Out Interface flags: I - inherited from (\*,G), AB - Admin Boundary, T - Turnaround, LH - Last Hop, AS - Assert


  ( 1.1.1.1, 227.1.1.1) SM, Uptime: 0 days, 00:00:55, RP-Address: 61.61.61.61
  Upstream Join/Prune: Join(HoldTime: 00:03:15), RPF: 12.1.61.1, Flags: KA(00:02:47), AL, RR(00:03:51)
  Incoming Interface:
    bundle-23,      Uptime: 0 days, 00:00:45,  status: Rcv,    Join(HoldTime: 00:03:15),  Flags: S
  Output Interface List:
    bundle-12,      Uptime: 0 days, 00:00:55,  status: NoFwd,  Prune(HoldTime: 00:02:34), Flags:
    bundle-13,      Uptime: 0 days, 00:00:43,  status: Fwd,    Prune(HoldTime: 00:02:46), Flags:
    bundle-14,      Uptime: 0 days, 00:00:14,  status: Fwd,    Join(HoldTime: 00:03:15),  Flags: I T
    bundle-15,      Uptime: 0 days, 00:00:43,  status: Fwd,    Join(HoldTime: 00:02:46),  Flags:

  dnRouter#

  dnRouter# show pim tree group 227.1.1.1

  IP PIM Tree Information Base for Group: 227.1.1.1

   Legend: PIM Entry: (\*/S,G)SM/SSM / State Uptime / RP address
          PIM Entry Types: SM-Sparse Mode, RPT SM - Shared tree, SSM - Source specific Mode,
          PIM Entry Flags:
            I - Inherited from (\*,G), KA - Keep Alive Timer(Time),
            AL - Currently Alive, As - Assumed to be Alive,
            RR - Register Received(Time), MSA - MSDP-SA Received,
            LH - Last Hop, SR - Sending Registers,
            FR - MoFRR enabled entry
          Out/In Interface state: Interface Name, Uptime(Time), status: OutIf: Fwd/NoFwd InIf:Rcv/Listen, JoinPrune(Time) or NotJoined or IgmpRep(Time)
          In Interface flags: R - Joined towards RPF(RP), S - Joined towards RPF(S), AB - Admin Boundary, F - Failed RPF, P - Prune Pending Timer(Time), FR(P) - MoFRR primary interface, FR(SB) - MoFRR Standby interface
          Out Interface flags: I - inherited from (\*,G), AB - Admin Boundary, T - Turnaround, LH - Last Hop, AS - Assert

  ( \*, 227.1.1.1) SM, Uptime: 0 days, 01:09:57, RP-Address: 61.61.61.61
  Upstream Join/Prune: None, RPF: 61.61.61.61, Flags:
  Incoming Interface:
    lo0,             Uptime: 0 days, 03:00:55,  status: Rcv, RP(G),                    Flags:
  Output Interface List:
    bundle-12,       Uptime: 0 days, 01:09:57,  status: Fwd, Join(HoldTime: 00:02:30), Flags:
    bundle-13,       Uptime: 0 days, 01:09:55,  status: Fwd, Join(HoldTime: 00:02:34), Flags:
    bundle-14,       Uptime: 0 days, 01:09:57,  status: Fwd, Join(HoldTime: 00:02:46), Flags:
    bundle-15,       Uptime: 0 days, 01:09:57,  status: Fwd, Join(HoldTime: 00:02:32), Flags:

  ( 1.1.1.1, 227.1.1.1) SM, Uptime: 0 days, 00:00:55, RP-Address: 61.61.61.61
  Upstream Join/Prune: Join(HoldTime: 00:03:15), RPF: 12.1.61.1, Flags: KA(00:02:47), AL, RR(00:03:51)
  Incoming Interface:
    bundle-23,      Uptime: 0 days, 00:00:45,  status: Rcv,    Join(HoldTime: 00:03:15),  Flags: S
  Output Interface List:
    bundle-12,      Uptime: 0 days, 00:00:55,  status: NoFwd,  Prune(HoldTime: 00:02:34), Flags:
    bundle-13,      Uptime: 0 days, 00:00:43,  status: Fwd,    Prune(HoldTime: 00:02:46), Flags:
    bundle-14,      Uptime: 0 days, 00:00:14,  status: Fwd,    Join(HoldTime: 00:03:15),  Flags: I T
    bundle-15,      Uptime: 0 days, 00:00:43,  status: Fwd,    Join(HoldTime: 00:02:46),  Flags:

  ( 2.2.2.2, 227.1.1.1) SM, Uptime: 0 days, 00:11:17, RP-Address: 61.61.61.61
  Upstream Join/Prune: Prune(never), RPF: 61.61.61.61, Flags: I, KA(00:02:27), AL, RR(00:03:31)
  Incoming Interface:
    lo0,             Uptime: 0 days, 03:00:55,  status: Rcv,    RP(G),                     Flags:
  Output Interface List:
    bundle-12,       Uptime: 0 days, 00:10:27,  status: NoFwd,  Prune(HoldTime: 00:03:01), Flags:
    bundle-13,       Uptime: 0 days, 00:11:05,  status: NoFwd,  Prune(HoldTime: 00:02:48), Flags:
    bundle-14,       Uptime: 0 days, 00:11:17,  status: NoFwd,  Prune(HoldTime: 00:03:18), Flags:
    bundle-15,       Uptime: 0 days, 00:10:27,  status: NoFwd,  Prune(HoldTime: 00:02:49), Flags:

 ( 3.3.3.3, 227.1.1.1) SM, Uptime: 0 days, 00:11:17, RP-Address: 61.61.61.61
  Upstream Join/Prune: Join(HoldTime: 00:03:15), RPF: 12.1.61.1, Flags: KA(00:02:59), AL
  Incoming Interface:
    bundle-23,      Uptime: 0 days, 00:00:45,   status: Rcv,    Join(HoldTime: 00:03:15),  Flags: S
  Output Interface List:
    bundle-15,       Uptime: 0 days, 00:01:13,  status: Fwd,    Join(HoldTime: 00:03:17),  Flags:
    bundle-12,       Uptime: 0 days, 00:10:27,  status: NoFwd,  Prune(HoldTime: 00:03:01), Flags:
    bundle-14,       Uptime: 0 days, 00:11:17,  status: NoFwd,  Prune(HoldTime: 00:03:18), Flags:


.. **Help line:** Show PIM Tree

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
