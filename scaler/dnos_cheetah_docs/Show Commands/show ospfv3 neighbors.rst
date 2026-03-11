show ospfv3 neighbors
---------------------

**Minimum user role:** viewer

The show ospf neighbors command displays OSPF neighbors information. You can display details on the neighbors and you can filter by interface.

To display neighbor information, use the following command:

**Command syntax: show ospfv3 neighbors** { address [neighbor-address] \| interface [interface-name] detail }

**Command mode:** operational



**Note**

- The "Uptime" in the output displays the amount of time the OSPF/OSPFv3 neighbor was in UP state.

.. - Table view order: The show ospf neighbors table view should be ordered by neighbor id in ascend

**Parameter table**

+------------------+-------------------------------------------------------------+----------------------------------------------------+---------------+
| Parameter        | Description                                                 | Range                                              | Default       |
+==================+=============================================================+====================================================+===============+
| No parameter     | Displays all the neighbors                                  |                                                    | \-            |
+------------------+-------------------------------------------------------------+----------------------------------------------------+---------------+
| neighbor-address | The neighbor's IP address to filter the information         | A.B.C.D                                            | \-            |
+------------------+-------------------------------------------------------------+----------------------------------------------------+---------------+
| interface-name   | Filters the displayed information for a specified interface | ge<interface speed>-<A>/<B>/<C>                    | \-            |
|                  |                                                             | ge<interface speed>-<A>/<B>/<C>.<sub-interface id> |               |
|                  |                                                             | bundle-<bundle id>                                 |               |
|                  |                                                             | bundle-<bundle id>.<sub-interface id>              |               |
+------------------+-------------------------------------------------------------+----------------------------------------------------+---------------+

**Example**
::

    dnRouter# show ospfv3 neighbors

    Neighbor ID     Pri State      DeadTime      Address                             Interface                                      Uptime      RXmtL RqstL DBsmL
    1.2.3.4           1 Full       00:00:40      fe80::18d0:93ff:fe7b:5b25           ge100-0/0/1 fe80::5c69:6bff:fe3e:55ae          00:02:34        0     0     0
    4.3.2.1           1 Full       00:00:31      fe80::1cb1:f7ff:fee1:2392           ge100-0/0/2 fe80::e068:3bff:fe81:4e2a          00:03:08        0     0     0


    dnRouter# show ospfv3 neighbors address 1.2.3.4

    Neighbor ID     Pri State      DeadTime      Address                             Interface                                      Uptime      RXmtL RqstL DBsmL
    1.2.3.4           1 Full       00:00:35      fe80::18d0:93ff:fe7b:5b25           ge100-0/0/1 fe80::5c69:6bff:fe3e:55ae          00:03:18        0     0     0


    dnRouter# show ospfv3 neighbors interface ge100-0/0/1

    Neighbor ID     Pri State      DeadTime      Address                             Interface                                      Uptime      RXmtL RqstL DBsmL
    1.2.3.4           1 Full       00:00:35      fe80::18d0:93ff:fe7b:5b25           ge100-0/0/1 fe80::5c69:6bff:fe3e:55ae          00:04:09        0     0     0


    dnRouter# show ospfv3 neighbors interface ge100-0/0/1 detail

    Neighbor 1.2.3.4, ge100-0/0/1
        Area 0.0.0.0 via interface ge100-0/0/1 (ifindex 7)
        His IfIndex: 7 Link-local address: fe80::5c69:6bff:fe3e:55ae
        State Full for a duration of 05m28s, 0 state changes
        His choice of DR/BDR 0.0.0.0/0.0.0.0, Priority 1
        DbDesc status: Slave SeqNum: 0x95380800
        Summary-List: 0 LSAs
        Request-List: 0 LSAs
        Retrans-List: 0 LSAs
        0 Pending LSAs for DbDesc in Time 00:00:00 [thread off]
        0 Pending LSAs for LSReq in Time 00:00:00 [thread off]
        0 Pending LSAs for LSUpdate in Time 00:00:00 [thread off]
        0 Pending LSAs for LSAck in Time 00:00:00 [thread off]
        BFD: Disabled
        BFD min-rx: 300 min-tx: 300 multiplier: 3

.. **Help line:** Displays OSPFv3 neighbors information

**Command History**

+---------+----------------------------------------------------+
| Release | Modification                                       |
+=========+====================================================+
| 11.6    | Command introduced                                 |
+---------+----------------------------------------------------+
| 15.0    | Added support for added "uptime" in command output |
+---------+----------------------------------------------------+
