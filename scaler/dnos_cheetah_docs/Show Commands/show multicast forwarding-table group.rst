show multicast forwarding-table group
-------------------------------------

**Minimum user role:** viewer

You can use this command to display the multicast forwarding-table (MFIB) information. Information can be displayed from a specific NCP. By default, information is displayed from an active NCP with a minimum ID.

**Command syntax: show multicast forwarding-table group [group]** source [source] ncp [ncp-id]

**Command mode:** operational



**Note**

- Specifying the group or group prefix will display all MFIB entries with the indicated group.

- Specifying the group and source will display all MFIB entries for the specified (S,G).

- Specifying the source only will display all MFIB entries whose source IP is the given one.

- MFIB entry flags:

- P - Punt to CPU received packets on any incoming interface

- D - Drop received packets

- I - Inform the Control plane about (S,G) packet Rx event

- R - Entry with RPF check, i.e. (S,G,*), RPF(in-if)

- An MFIB entry that relates to a dual incoming interface Route (MRIB) Transition entry FR(P) - MoFRR primary entry FR(SB) - MoFRR standby entry

.. - Specifying the group or group prefix will display all MFIB entries with the indicated group.

  - Specifying group and source will display all MFIB entries for the specified (S,G)

  - Specifying source only will display all MFIB entries whose source IP is the given one.

  - MFIB entry flags:

     P - Punt to CPU received packets on any incoming interface,

     D - Drop received packets,

     I - Inform the Control plane about (S,G) packet Rx event,

     R - Entry with RPF check i.e. (S,G,*), RPF(in-if)

     * - An MFIB entry that relates to a dual incoming interface Route (MRIB) Transition entry

     FR(P) - MoFRR primary entry

     FR(SB) - MoFRR standby entry

**Parameter table**

+-----------+-------------------------------------+---------+---------------+
| Parameter | Description                         | Range   | Default       |
+===========+=====================================+=========+===============+
| group     | The IP address of the group         | A.B.C.D | \-            |
+-----------+-------------------------------------+---------+---------------+
| source    | The IP address of the source        | A.B.C.D | \-            |
+-----------+-------------------------------------+---------+---------------+
| ncp-id    | The ID of the specific NCP (string) | 0..191  | Lowest NCP ID |
+-----------+-------------------------------------+---------+---------------+

**Example**
::

 dnRouter# show multicast forwarding-table group 232.1.1.1 source 1.1.1.1

  IP Multicast Forwarding Information Base:
  NCP-ID: 0
  Legend:  Entry flags:
              P - Punt to CPU received packets on any incoming interface, D - Drop received packets,
              I - Inform the Control plane about (S,G) packet Rx event, R - Entry with RPF check
              * - A dual incoming interface entry, FR(P) - MoFRR primary entry, FR(SB) - MoFRR standby entry

  (Source: 1.1.1.1, Group: 232.1.1.1, in-if: Any), RPF(Bundle-23), Priority: High, Flags: R
    Uptime: 01:09:44
  Output interface list:
    Bundle-22, Uptime: 01:09:44
    Bundle-26, Uptime: 01:09:44



  dnRouter# show multicast forwarding-table group 227.1.1.1 source 1.1.1.1 ncp 3

  IP Multicast Forwarding Information Base:
  NCP-ID: 3
  Legend:  Entry flags:
              P - Punt to CPU received packets on any incoming interface, D - Drop received packets,
              I - Inform the Control plane about (S,G) packet Rx event, R - Entry with RPF check
              * - A dual incoming interface entry, FR(P) - MoFRR primary entry, FR(SB) - MoFRR standby entry

  (Source: 1.1.1.1, Group: 227.1.1.1, in-if: Any), RPF(Bundle-23), Priority: High, Flags: R, *
    Uptime: 02:00:44
  Output interface list:
    Bundle-22, Uptime: 02:00:44
    Bundle-24, Uptime: 01:09:47
    Bundle-25, Uptime: 01:09:46

  (Source: 1.1.1.1, Group: 227.1.1.1, in-if: bundle-25), Priority: High, Flags: I, *
    Uptime: 01:09:47
  Output interface list:
    NCP-CPU,   Uptime: 01:09:47


  dnRouter# show multicast forwarding-table group 232.3.2.1 source 1.2.3.4 ncp 5

  IP Multicast Forwarding Information Base:
  NCP-ID: 5
  Legend:  Entry flags:
              P - Punt to CPU received packets on any incoming interface, D - Drop received packets,
              I - Inform the Control plane about (S,G) packet Rx event, R - Entry with RPF check
              * - A dual incoming interface entry, FR(P) - MoFRR primary entry, FR(SB) - MoFRR standby entry

  (Source: 1.2.3.4, Group: 232.3.2.1, in-if: Any), RPF(Bundle-23), Priority: High, Flags: R, FR(P)
    Uptime: 01:09:44
  Output interface list:
    Bundle-102, Uptime: 01:09:44
    Bundle-103, Uptime: 01:09:44
    Bundle-104, Uptime: 01:09:44

  (Source: 1.2.3.4, Group: 232.3.2.1, in-if: Bundle-32), Priority: High, Flags: FR(SB)
    Uptime: 01:09:44
  Output interface list:
    Count-and-drop, Uptime: 01:09:47

.. **Help line:**

**Command History**

+---------+-----------------------+
| Release | Modification          |
+=========+=======================+
| 12.0    | Command introduced    |
+---------+-----------------------+
| 13.0    | Updated ncp-id range  |
+---------+-----------------------+
| 14.0    | Updated MoFRR support |
+---------+-----------------------+
