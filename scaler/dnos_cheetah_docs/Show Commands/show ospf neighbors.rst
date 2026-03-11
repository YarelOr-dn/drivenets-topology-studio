show ospf neighbors
-------------------

**Minimum user role:** viewer

The show ospf neighbors command displays OSPF neighbors information. You can display details on the neighbors and you can filter by interface.

To display neighbor information, use the following command:

**Command syntax: show ospf** instance [ospf-instance-name] **neighbors** { address [neighbor-address] \| interface [interface-name] detail }

**Command mode:** operational



**Note**

- The "Uptime" in the output displays the amount of time the OSPF/OSPFv3 neighbor was in UP state.

..  - Table view order: The show ospf neighbors table view should be ordered by neighbor id in ascending order.

    - use "instance [ospf-instance-name]" to display information from a specific OSPF instance, when not specified, display information from all OSPF instances

**Parameter table**

+--------------------+----------------------------------------------------------------+---------------------------------------------------+---------------+
| Parameter          | Description                                                    | Values                                            | Default value |
+====================+================================================================+===================================================+===============+
| No parameter       | Displays all the neighbors                                     |                                                   | \-            |
+--------------------+----------------------------------------------------------------+---------------------------------------------------+---------------+
| neighbor-address   | The neighbor's IP address to filter the information            | A.B.C.D                                           | \-            |
+--------------------+----------------------------------------------------------------+---------------------------------------------------+---------------+
| interface-name     | Filters the displayed information for a specified interface    | ge<interface speed>-<A>/<B>/<C>                   | \-            |
|                    |                                                                | ge<interface speed>-<A>/<B>/<C>.<sub-interface id>|               |
|                    |                                                                | bundle-<bundle id>                                |               |
|                    |                                                                | bundle-<bundle id>.<sub-interface id>             |               |
+--------------------+----------------------------------------------------------------+---------------------------------------------------+---------------+
| ospf-instance-name | Filters the displayed information to a specific OSPF instance. | configured instances names                        | all           |
+--------------------+----------------------------------------------------------------+---------------------------------------------------+---------------+

**Example**
::

    dnRouter# show ospf neighbors

    Ospf Instance instance1

    Neighbor ID      Pri State           Dead Time Address         Interface                   Uptime        RXmtL RqstL DBsmL
    2.2.2.2           1 Full              36.483s 12.12.4.2       ge100-0/0/4:12.12.4.1        2m47s         0     0     0
    4.4.4.4           1 Full              30.203s 84.1.1.1        ge100-0/0/2:84.1.1.2         2d04h40m      0     0     0
    5.5.5.5           1 Full              39.199s 13.13.1.2       ge100-0/0/1:13.13.1.1        3d01h56m      0     0     0


    dnRouter# show ospf instance instance1 neighbors

    Ospf Instance instance1

    Neighbor ID      Pri State           Dead Time Address         Interface                   Uptime        RXmtL RqstL DBsmL
    2.2.2.2           1 Full              36.483s 12.12.4.2       ge100-0/0/4:12.12.4.1        2m47s         0     0     0
    4.4.4.4           1 Full              30.203s 84.1.1.1        ge100-0/0/2:84.1.1.2         2d04h40m      0     0     0
    5.5.5.5           1 Full              39.199s 13.13.1.2       ge100-0/0/1:13.13.1.1        3d01h56m      0     0     0


    dnRouter(cfg 22-Apr-2020-09:44:49)# show ospf neighbors address 5.5.5.5

    Ospf Instance instance1

    Neighbor ID      Pri State           Dead Time Address         Interface                   Uptime        RXmtL RqstL DBsmL
    5.5.5.5           1 Full              39.199s 13.13.1.2       ge100-0/0/1:13.13.1.1        3d01h56m      0     0     0


    dnRouter(cfg 22-Apr-2020-09:44:49)# show ospf instance instance1 neighbors address 5.5.5.5

    Ospf Instance instance1

    Neighbor ID      Pri State           Dead Time Address         Interface                   Uptime        RXmtL RqstL DBsmL
    5.5.5.5           1 Full              39.199s 13.13.1.2       ge100-0/0/1:13.13.1.1        3d01h56m      0     0     0


    dnRouter# show ospf neighbors interface ge100-0/0/4

    Ospf Instance instance1

    Neighbor ID      Pri State           Dead Time Address         Interface                   Uptime        RXmtL RqstL DBsmL
    2.2.2.2           1 Full              36.483s 12.12.4.2       ge100-0/0/4:12.12.4.1        2m47s         0     0     0


    dnRouter# show ospf instance instance1 neighbors interface ge100-0/0/4

    Ospf Instance instance1

    Neighbor ID      Pri State           Dead Time Address         Interface                   Uptime        RXmtL RqstL DBsmL
    2.2.2.2           1 Full              36.483s 12.12.4.2       ge100-0/0/4:12.12.4.1        2m47s         0     0     0


    dnRouter# show ospf neighbors interface ge100-0/0/4 detail

    Ospf Instance instance1

    Neighbor 2.2.2.2, interface address 12.12.4.2
        In the area 0.0.0.0 via interface ge100-0/0/4
        Neighbor State is Full, for 2m47s, 5 state changes
        Most recent state change statistics:
        Progressive change 2m47s ago
        Neighbor priority is 1
        DR is 0.0.0.0, BDR is 0.0.0.0
        Options 82 *|-|O|-|EA|-|-|E|-|*  (O, LLS Data block, External Routing)
        Dead timer due in 32.408s
        Database Summary List 0
        Link State Request List 0
        Link State Retransmission List 0
        Thread Inactivity Timer on
        Thread Database Description Retransmission off
        Thread Link State Request Retransmission on
        Thread Link State Update Retransmission on
        BFD: Disabled
        BFD min-rx: 300 min-tx: 300 multiplier: 3


    dnRouter# show ospf instance instance1 neighbors interface ge100-0/0/4 detail

    Ospf Instance instance1

    Neighbor 2.2.2.2, interface address 12.12.4.2
        In the area 0.0.0.0 via interface ge100-0/0/4
        Neighbor State is Full, for 2m47s, 5 state changes
        Most recent state change statistics:
        Progressive change 2m47s ago
        Neighbor priority is 1
        DR is 0.0.0.0, BDR is 0.0.0.0
        Options 82 *|-|O|-|EA|-|-|E|-|*  (O, LLS Data block, External Routing)
        Dead timer due in 32.408s
        Database Summary List 0
        Link State Request List 0
        Link State Retransmission List 0
        Thread Inactivity Timer on
        Thread Database Description Retransmission off
        Thread Link State Request Retransmission on
        Thread Link State Update Retransmission on
        BFD: Disabled
        BFD min-rx: 300 min-tx: 300 multiplier: 3

.. **Help line:** Displays OSPF neighbors information

**Command History**

+---------+----------------------------------------------------+
| Release | Modification                                       |
+=========+====================================================+
| 11.6    | Command introduced                                 |
+---------+----------------------------------------------------+
| 15.0    | Added support for added "uptime" in command output |
+---------+----------------------------------------------------+
| 18.2    | Added instance parameter                           |
+---------+----------------------------------------------------+
