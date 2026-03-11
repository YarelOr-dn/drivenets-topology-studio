show ospfv3 database
--------------------

**Minimum user role:** viewer

The show ospfv3 database is a group of commands that display lists of information related to the OSPFv3 database.



**Command syntax: show ospfv3 database** { [lsa-type] | [lsa-type] link-state-id [link-state-id] } {adv-router [adv-address] | link-state-id [link-state-id] | self-originate}

**Command mode:** operational



..
    **Internal Note**

    - The vertical bar (|) indicates that only one of the parameters can appear in the command.

.. - self-originate is optional

**Parameter table**

+-------------------+--------------------------+
| Argument          | Description              |
+===================+==========================+
| external          | External link states     |
+-------------------+--------------------------+
| network           | Network link states      |
+-------------------+--------------------------+
| router            | Router link states       |
+-------------------+--------------------------+
| nssa-external     | NSSA external link state |
+-------------------+--------------------------+
| inter-area-prefix | Inter-Area-Prefix LSA    |
+-------------------+--------------------------+
| inter-area-router | Inter-Area-Router LSA    |
+-------------------+--------------------------+
| link              | Link LSA                 |
+-------------------+--------------------------+
| intra-area-prefix | Intra-Area-Prefix LSA    |
+-------------------+--------------------------+
| grace             | Grace LSA                |
+-------------------+--------------------------+

These arguments can appear in several combinations:

+---------------------------------------------------------+---------------------------+
| Command                                                 | Example                   |
+=========================================================+===========================+
| show ospfv3 database                                    | show ospf database        |
+---------------------------------------------------------+---------------------------+
| show ospf database (external|network|router|link\grace) | show ospf database router |
+---------------------------------------------------------+---------------------------+

**Example**
::

    dnRouter# show ospfv3 database
    OSPFv3 Router with ID (8.8.8.8)

    Router Link States (Area 0.0.0.0)

    ADV Router      Age         Seq#       Fragment ID  Link count  Bits
    4.4.4.4         120         0x80000002 0            1           None
    8.8.8.8         119         0x80000002 0            1           None

        Link (Type-8) Link States (Area 0.0.0.0)

    ADV Router      Age         Seq#       Link ID    Interface
    4.4.4.4         197         0x80000001 13         ge100-0/0/0.123
    8.8.8.8         124         0x80000001 16         ge400-0/2/1.123

        Intra Area Prefix Link States (Area 0.0.0.0)

    ADV Router      Age         Seq#       Link ID    Ref-lstype  Ref-LSID
    4.4.4.4         180         0x80000002 0          0x2001      0
    8.8.8.8         124         0x80000001 0          0x2001      0

        Grace (Type-11) Link States (Area 0)

    ADV Router      Age         Seq#       Link ID    Interface
    4.4.4.4         2           0x80000001 13         Gi0/0/0/3
    4.4.4.4         2           0x80000001 16         Gi0/0/0/6


    dnRouter# show ospfv3 database router

    OSPFv3 Router with ID (8.8.8.8)

        Router Link States (Area 0)

      LS age: 1353
      Options: (V6-Bit E-Bit R-Bit DC-Bit)
      LS Type: Router Links
      Link State ID: 0
      Advertising Router: 4.4.4.4
      LS Seq Number: 80000002
      Checksum: 0x10a1
      Length: 40
      Number of Links: 1

        Link connected to: another Router (point-to-point)
        Link Metric: 1
        Local Interface ID: 13
          Neighbor Interface ID: 16
          Neighbor Router ID: 8.8.8.8

      LS age: 1352
      Options: (V6-Bit E-Bit R-Bit DC-Bit)
      LS Type: Router Links
      Link State ID: 0
      Advertising Router: 8.8.8.8
      LS Seq Number: 80000002
      Checksum: 0x426f
      Length: 40
      Number of Links: 1

        Link connected to: another Router (point-to-point)
        Link Metric: 1
        Local Interface ID: 16
          Neighbor Interface ID: 13
          Neighbor Router ID: 4.4.4.4

    dnRouter# show ospfv3 database external

    OSPFv3 Router with ID (8.8.8.8)

    Type-5 AS External Link States

    LS age: 243
    LS Type: AS External Link
    Link State ID: 9
    Advertising Router: 3.3.3.3
    LS Seq Number: 80000004
    Checksum: 0xd204
    Length: 36
    Prefix Address: 2000::
    Prefix length: 56, Options: None
    Metric Type: 2
    Metric: 20
    External Route Tag: 0

    dnRouter# show ospfv3 database link-stste-id 9

    OSPFv3 Router with ID (8.8.8.8)

    Type-5 AS External Link States

    LS age: 243
    LS Type: AS External Link
    Link State ID: 9
    Advertising Router: 3.3.3.3
    LS Seq Number: 80000004
    Checksum: 0xd204
    Length: 36
    Prefix Address: 2000::
    Prefix length: 56, Options: None
    Metric Type: 2
    Metric: 20
    External Route Tag: 0


    dnRouter# show ospfv3 database grace

    OSPFv3 Router with ID (8.8.8.8)

    Grace (Type-11) Link States (Area 0)

    LS age: 5
    LS Type: Grace Links (Interface: Gi0/0/0/3)
    Link State ID: 13
    Advertising Router: 4.4.4.4
    LS Seq Number: 80000001
    Checksum: 0xefc7
    Length: 36
        Grace Period : 240
        Graceful Restart Reason : Software reload/crash

    LS age: 5
    LS Type: Grace Links (Interface: Gi0/0/0/6)
    Link State ID: 16
    Advertising Router: 4.4.4.4
    LS Seq Number: 80000001
    Checksum: 0xd1e2
    Length: 36
        Grace Period : 240
        Graceful Restart Reason : Software reload/crash

.. **Help line:** Displays the link state database for OSPFv3

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


