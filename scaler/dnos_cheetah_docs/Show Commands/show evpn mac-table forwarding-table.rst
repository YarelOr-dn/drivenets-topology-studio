show evpn mac-table forwarding-table
------------------------------------

**Minimum user role:** operator

To show the mac-table forwarding-table for an EVPN instance.

**Command syntax: show evpn mac-table forwarding-table** instance [evpn-name]
**Command syntax: show evpn mac-table forwarding-table** ncp [ncp-id]
**Command syntax: show evpn mac-table forwarding-table** instance [evpn-name] interface [interface-name]
**Command syntax: show evpn mac-table forwarding-table** instance [evpn-name] mac [mac-address]
**Command syntax: show evpn mac-table forwarding-table** flags [flag-code]


**Command mode:** operational

**Parameter table:**

+--------------------+--------------------------------------------------------+-----------------------------------+---------------+
| Parameter          | Description                                            | Values                            | Default value |
+====================+========================================================+===================================+===============+
| evpn-name          | The name of the EVPN instance                          | String                            | \-            |
+--------------------+--------------------------------------------------------+-----------------------------------+---------------+
| interface-name     | The name of the interface                              | String                            | \-            |
+--------------------+--------------------------------------------------------+-----------------------------------+---------------+
| ncp-id             | Displays information from a specific NCP.              |  0..max # NCP per cluster type -1 | \-            |
+--------------------+--------------------------------------------------------+-----------------------------------+---------------+
| mac-address        | Provide information for the specified mac table entry  | xx:xx:xx:xx:xx:xx                 | \-            |
+--------------------+--------------------------------------------------------+-----------------------------------+---------------+
| flag-code          | Display entries with the requested flag-code           | String - one or more of the codes | \-            |
+--------------------+--------------------------------------------------------+-----------------------------------+---------------+

**Note:**

- Specifying an evpn-name will display the information of the specified EVPN instance.

- If no instance is specified, this will result in the listing of the information for all the EVPN instances.

- If detail is specified then detailed information will be provided.


**Example**
::

    dev-dnRouter# show evpn mac-table forwarding-table

        Legend: R - Remote, L - Local, P - Pending-Installation, si - Sticky-Interface, S - Sticky, F - Leaf, ri - Router-Interface, fl - Flood, bh - Black-Hole
        
        NCP-ID 0
            EVPN: evpn1
                Total MAC Entries: 6

                | MacAddress         | Interface              | MPLS                         | Timestamp              | Flags            |
                +--------------------+------------------------+------------------------------+------------------------+------------------+
                | 00:00:00:00:00:01  | ge100-0/0/0.100        |                              | 31-Mar-2024-11:23:57   | L                |
                | 00:00:00:00:00:02  | ge100-0/0/0.100        |                              | 31-Mar-2024-11:23:57   | L                |
                | 00:00:00:00:00:10  | ge100-0/0/0.101        |                              | 31-Mar-2024-11:23:57   | LF               |
                | 00:00:00:00:20:01  | ge100-0/0/1            | 1000, 1001, 1002, 100        | 31-Mar-2024-11:24:06   | R                |
                |                    | ge100-0/0/1            | 1010, 1011, 1012, 100        | 31-Mar-2024-11:24:06   | R                |
                | 00:00:00:00:20:02  | ge100-0/0/1            | 2000, 2001, 2002, 200        | 31-Mar-2024-11:24:06   | R                |
                |                    | ge100-0/0/2            | 2010, 2011, 2012, 200        | 31-Mar-2024-11:24:06   | R                |
                |                    | ge100-0/0/2            | 2020, 2021, 2022, 2023, 200  | 31-Mar-2024-11:24:06   | R                |
                | 00:00:00:00:20:03  | ge100-0/0/2            | 4000, 300                    | 31-Mar-2024-11:24:07   | RF               |
                |                    | ge100-0/0/3            | 4001, 300                    | 31-Mar-2024-11:24:07   | RF               |
                |                    | ge100-0/0/3            | 4002, 300                    | 31-Mar-2024-11:24:07   | RF               |

            EVPN: evpn2
                Total MAC Entries: 6
                | MacAddress         | Interface              | MPLS                         | Timestamp              | Flags            |
                +--------------------+------------------------+------------------------------+------------------------+------------------+
                | 00:00:00:00:00:20  | ge100-0/0/0.200        |                              | 31-Mar-2024-11:23:58   | L                |
                | 00:00:00:00:00:30  | ge100-0/0/0.201        |                              | 31-Mar-2024-11:23:58   | Lsi              |
                | 00:00:00:00:21:01  | ge100-0/0/0.201        |                              | 31-Mar-2024-11:24:07   | R                |
                | 00:00:00:00:21:02  | N/A                    |                              | 31-Mar-2024-11:24:07   | Rfl              |
                | 00:00:00:00:21:03  | N/A                    |                              | 31-Mar-2024-11:24:08   | RFfl             |
                | 00:00:00:00:40:00  | irb1                   |                              | 31-Mar-2024-11:23:54   | ri               |

            EVPN: evpn3
                Total MAC Entries: 3
                | MacAddress         | Interface              | MPLS                         | Timestamp              | Flags            |
                +--------------------+------------------------+------------------------------+------------------------+------------------+
                | 00:00:00:00:00:40  | ge100-0/0/0.300        |                              | 31-Mar-2024-11:23:58   | L                |
                | 00:00:00:00:22:01  | ge100-0/0/4            | 5000, 700                    | 31-Mar-2024-11:24:08   | R                |
                | 00:00:00:00:30:01  | Null0                  |                              | 31-Mar-2024-11:24:08   | Rbh              |

 
    dev-dnRouter# show evpn mac-table forwarding-table ncp 0

        Legend: R - Remote, L - Local, P - Pending-Installation, si - Sticky-Interface, S - Sticky, F - Leaf, ri - Router-Interface, fl - Flood, bh - Black-Hole

        NCP-ID 0
            EVPN: evpn1
                Total MAC Entries: 6
                | MacAddress         | Interface              | MPLS                         | Timestamp              | Flags            |
                +--------------------+------------------------+------------------------------+------------------------+------------------+
                | 00:00:00:00:00:01  | ge100-0/0/0.100        |                              | 31-Mar-2024-11:23:57   | L                |
                | 00:00:00:00:00:02  | ge100-0/0/0.100        |                              | 31-Mar-2024-11:23:57   | L                |
                | 00:00:00:00:00:10  | ge100-0/0/0.101        |                              | 31-Mar-2024-11:23:57   | LF               |
                | 00:00:00:00:20:01  | ge100-0/0/1            | 1000, 1001, 1002, 100        | 31-Mar-2024-11:24:06   | R                |
                |                    | ge100-0/0/1            | 1010, 1011, 1012, 100        | 31-Mar-2024-11:24:06   | R                |
                | 00:00:00:00:20:02  | ge100-0/0/1            | 2000, 2001, 2002, 200        | 31-Mar-2024-11:24:06   | R                |
                |                    | ge100-0/0/2            | 2010, 2011, 2012, 200        | 31-Mar-2024-11:24:06   | R                |
                |                    | ge100-0/0/2            | 2020, 2021, 2022, 2023, 200  | 31-Mar-2024-11:24:06   | R                |
                | 00:00:00:00:20:03  | ge100-0/0/2            | 4000, 300                    | 31-Mar-2024-11:24:07   | RF               |
                |                    | ge100-0/0/3            | 4001, 300                    | 31-Mar-2024-11:24:07   | RF               |
                |                    | ge100-0/0/3            | 4002, 300                    | 31-Mar-2024-11:24:07   | RF               |

            EVPN: evpn2
                Total MAC Entries: 6
                | MacAddress         | Interface              | MPLS                         | Timestamp              | Flags            |
                +--------------------+------------------------+------------------------------+------------------------+------------------+
                | 00:00:00:00:00:20  | ge100-0/0/0.200        |                              | 31-Mar-2024-11:23:58   | L                |
                | 00:00:00:00:00:30  | ge100-0/0/0.201        |                              | 31-Mar-2024-11:23:58   | Lsi              |
                | 00:00:00:00:21:01  | ge100-0/0/0.201        |                              | 31-Mar-2024-11:24:07   | R                |
                | 00:00:00:00:21:02  | N/A                    |                              | 31-Mar-2024-11:24:07   | Rfl              |
                | 00:00:00:00:21:03  | N/A                    |                              | 31-Mar-2024-11:24:08   | RFfl             |
                | 00:00:00:00:40:00  | irb1                   |                              | 31-Mar-2024-11:23:54   | ri               |

            EVPN: evpn3
                Total MAC Entries: 3
                | MacAddress         | Interface              | MPLS                         | Timestamp              | Flags            |
                +--------------------+------------------------+------------------------------+------------------------+------------------+
                | 00:00:00:00:00:40  | ge100-0/0/0.300        |                              | 31-Mar-2024-11:23:58   | L                |
                | 00:00:00:00:22:01  | ge100-0/0/4            | 5000, 700                    | 31-Mar-2024-11:24:08   | R                |
                | 00:00:00:00:30:01  | Null0                  |                              | 31-Mar-2024-11:24:08   | Rbh              |


    dev-dnRouter# show evpn mac-table forwarding-table instance evpn1

        Legend: R - Remote, L - Local, P - Pending-Installation, si - Sticky-Interface, S - Sticky, F - Leaf, ri - Router-Interface, fl - Flood, bh - Black-Hole
        
        NCP-ID 0
            EVPN: evpn1
                Total MAC Entries: 6
                | MacAddress         | Interface              | MPLS                         | Timestamp              | Flags            |
                +--------------------+------------------------+------------------------------+------------------------+------------------+
                | 00:00:00:00:00:01  | ge100-0/0/0.100        |                              | 31-Mar-2024-11:23:57   | L                |
                | 00:00:00:00:00:02  | ge100-0/0/0.100        |                              | 31-Mar-2024-11:23:57   | L                |
                | 00:00:00:00:00:10  | ge100-0/0/0.101        |                              | 31-Mar-2024-11:23:57   | LF               |
                | 00:00:00:00:20:01  | ge100-0/0/1            | 1000, 1001, 1002, 100        | 31-Mar-2024-11:24:06   | R                |
                |                    | ge100-0/0/1            | 1010, 1011, 1012, 100        | 31-Mar-2024-11:24:06   | R                |
                | 00:00:00:00:20:02  | ge100-0/0/1            | 2000, 2001, 2002, 200        | 31-Mar-2024-11:24:06   | R                |
                |                    | ge100-0/0/2            | 2010, 2011, 2012, 200        | 31-Mar-2024-11:24:06   | R                |
                |                    | ge100-0/0/2            | 2020, 2021, 2022, 2023, 200  | 31-Mar-2024-11:24:06   | R                |
                | 00:00:00:00:20:03  | ge100-0/0/2            | 4000, 300                    | 31-Mar-2024-11:24:07   | RF               |
                |                    | ge100-0/0/3            | 4001, 300                    | 31-Mar-2024-11:24:07   | RF               |
                |                    | ge100-0/0/3            | 4002, 300                    | 31-Mar-2024-11:24:07   | RF               |

    dev-dnRouter# show evpn mac-table forwarding-table instance evpn1 interface ge100-0/0/0.100

        Legend: R - Remote, L - Local, P - Pending-Installation, si - Sticky-Interface, S - Sticky, F - Leaf, ri - Router-Interface, fl - Flood, bh - Black-Hole

        NCP-ID 0
            EVPN: evpn1
        Total MAC Entries: 2
            | MacAddress         | Interface              | MPLS                         | Timestamp              | Flags            |
            +--------------------+------------------------+------------------------------+------------------------+------------------+
            | 00:00:00:00:00:01  | ge100-0/0/0.100        |                              | 31-Mar-2024-11:23:57   | L                |
            | 00:00:00:00:00:02  | ge100-0/0/0.100        |                              | 31-Mar-2024-11:23:57   | L                |

    dev-dnRouter# show evpn mac-table forwarding-table instance evpn1 interface ge100-0/0/0.100 mac 00:00:00:00:00:01

        NCP-ID 0
        EVPN: evpn1
        MAC: 00:00:00:00:00:01
        Timestamp: 31-Mar-2024-11:23:57
        Flags: Local
        Interface: ge100-0/0/0.100

    dev-dnRouter# show evpn mac-table forwarding-table instance evpn1 mac 00:00:00:00:20:02

        NCP-ID 0
        EVPN: evpn1
            MAC: 00:00:00:00:20:02
            Timestamp: 31-Mar-2024-11:24:06
            Flags: Remote
                next-hop(1): 2.2.2.2 Recursive, Active
                EVPN label: 200
                next-hop(1,1): 10.10.10.4 Active
                mpls labels: 2000(top),2001,2002
                interface: ge100-0/0/1
                next-hop(1,2): 10.10.11.2 Active
                mpls labels: 2010(top),2011,2012
                interface: ge100-0/0/2
                next-hop(1,3): 10.10.11.3 Active
                mpls labels: 2020(top),2021,2022,2023
                interface: ge100-0/0/2


.. **Help line:** show information of the MAC Table Forwarding-Table of the EVPN instances

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 19.1    | Command introduced                  |
+---------+-------------------------------------+