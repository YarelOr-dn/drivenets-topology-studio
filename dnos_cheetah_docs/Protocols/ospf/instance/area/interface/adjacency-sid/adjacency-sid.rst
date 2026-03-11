protocols ospf instance area interface adjacency-sid
----------------------------------------------------

**Minimum user role:** operator

When OSPF forms an adjacency over a given link, it is advertised by the Adj-SID Sub-TLVs of the Extended Link TLV.
Segment-routing adjacency-sid allocates a specific SID, e.g label, to forward incoming matching mpls traffic over the adjacency. I.e to forward traffic over a specific egress interface to a known next-hop
A configured adjacency-sid will be persistent, and will hold the SID value for as long as it is configured, including system reboot. The persistent adjacency-sid is advertised with P-flag set (RFC8667)
To configure a persistent adjacency-sid:

**Command syntax: adjacency-sid [SID type] [sid-index/sid-label]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface

**Note**
- Configured SID value (i.e expected label value) must be within the configured SRLB range
- Configured SID value (i.e expected label value) must be unique on the OSPF interface (due to combination of type & value)
- Configured SID value (i.e expected label value) must be unique between all OSPF interfaces
- Support up to two configured adjacency-sids per interface.

**Parameter table**

+---------------------+----------------------------------------------------------------------------------+---------------------------+---------+
| Parameter           | Description                                                                      | Range                     | Default |
+=====================+==================================================================================+===========================+=========+
| SID type            | Sid type absolute or index                                                       | | index                   | \-      |
|                     |                                                                                  | | label                   |         |
+---------------------+----------------------------------------------------------------------------------+---------------------------+---------+
| sid-index/sid-label | sid-index: Assigns the adjacency-sid label according to the index of the         | | sid-index: 0-7999       | \-      |
|                     | Segment-Routing Local Block used by OSPF. The value must be within the SRLB      | | sid-label: 8000-15999   |         |
|                     | range.                                                                           |                           |         |
|                     | sid-label: Assigns the adjacency-sid label as an absolute value. The value must  |                           |         |
|                     | be within the SRLB range.                                                        |                           |         |
+---------------------+----------------------------------------------------------------------------------+---------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# instance ospf1
    dnRouter(cfg-protocols-ospf-inst)# area 0
    dnRouter(cfg-ospf-inst-area)# interface bundle-1
    dnRouter(cfg-inst-area-if)# adjacency-sid index 10
    dnRouter(cfg-area-if-adj-sid)#

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# instance ospf1
    dnRouter(cfg-protocols-ospf-inst)# area 0
    dnRouter(cfg-ospf-inst-area)# interface bundle-1
    dnRouter(cfg-inst-area-if)# adjacency-sid label 8500
    dnRouter(cfg-area-if-adj-sid)#



**Removing Configuration**

To remove configured adjacency-sid:
::

    dnRouter(cfg-inst-area-if)# no adjacency-sid label 8500

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
