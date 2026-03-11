show evpn mac-table
-------------------

**Minimum user role:** operator

To show the mac-table for an EVPN instance.

**Command syntax: show evpn mac-table** instance [evpn-name]
**Command syntax: show evpn mac-table** detail
**Command syntax: show evpn mac-table** instance [evpn-name] mac [mac-address]


**Command mode:** operational

**Parameter table:**

+--------------------+--------------------------------------------------------+-------------------+---------------+
| Parameter          | Description                                            | Values            | Default value |
+====================+========================================================+===================+===============+
| evpn-name          | The name of the EVPN instance                          | String | all      | \-            |
+--------------------+--------------------------------------------------------+-------------------+---------------+
| mac-address        | Provide information for the specified mac table entry  | String | all      | \-            |
+--------------------+--------------------------------------------------------+-------------------+---------------+

**Note:**

- Specifying an evpn-name will display the information of the specified EVPN instance.

- If no instance is specified, this will result in the listing of the inclusive-multicast-table information for all the EVPN instances.

- If detail is specified then detailed information will be provided.


**Example**
::


    dnRouter# show evpn mac-table


        Codes: L - Local route, B - BGP route, P - Suppressed,
            I - Suppressed Indefinitely, s - Sticky, si - Sticky Interface, M - Only MAC-IP received
            > - Selected route, S - Stale route

        EVPN: evpn1
            EVI ID : 1

            ETH TAG: 0
                Flags     | MAC address          | ESI                           | Source               | Label     | Resolution
                ------------------------------------------------------------------------------------------------------------------------
                L>        | 00:10:10:00:00:53    | 00:11:22:33:44:55:66:77:88:99 | ge400-0/0/3.101      | 107468    |
                Ls>       | 00:10:10:a1:c9:67    | 00:00:00:00:00:00:00:00:00:00 | ge400-0/0/2.32       | 321636    |
                Lsi>      | b3:12:85:17:06:9a    | 00:00:00:00:00:00:00:00:00:00 | bundle-1854.53       | 895478    |   


    dnrouter# show evpn mac-table instance esi-scale_1997 mac e8:c5:7a:b0:ae:d6

    EVPN    : esi-scale_1997
    EVI ID  : 17
    ETH TAG : 0
    MAC address: e8:c5:7a:b0:ae:d6
    (1) Protocol: Local
      ESI: 00:00:00:00:00:00:00:00:19:97
      Interface: ge400-0/0/21
      MAC label: 4294967295 (local label of type 2)
      Timestamp: 13-Jul-2023-13:45:58
      Sticky: None          
      Sequence Number: 11
      
      Loop Prevention 
      ----------------
      Suppression State: Suppressed
      Expected Suppression Release Time:  13-Jul-2023-13:19:11
      Number of Completed Suppression Cycles: 1
      
      Move History
      ------------
      
      Time                     |   Interface   | Sequence Number 
      -------------------------+---------------+-----------------
      13-Jul-2023-13:02:21     | ge400-0/0/21  |         0
      13-Jul-2023-13:03:35     | 192.168.17.24 |         1
      13-Jul-2023-13:03:50     | ge400-0/0/21  |         2
      13-Jul-2023-13:03:55     | 192.168.17.24 |         3 
      13-Jul-2023-13:04:01     | ge400-0/0/21  |         4
      13-Jul-2023-13:05:11     | 192.168.17.24 |         5
      13-Jul-2023-13:05:11     | Suppressed    |         
      13-Jul-2023-13:10:11     | Released      |         
      13-Jul-2023-13:13:43     | ge400-0/0/21  |         6
      13-Jul-2023-13:13:45     | 192.168.17.24 |         7
      13-Jul-2023-13:13:50     | ge400-0/0/21  |         8
      13-Jul-2023-13:13:55     | 192.168.17.24 |         9 
      13-Jul-2023-13:14:07     | ge400-0/0/21  |         10
      13-Jul-2023-13:14:11     | 192.168.17.24 |         11
      13-Jul-2023-13:14:11     | Suppressed    |         
      
    
    dnrouter# show evpn mac-table detail instance esi-scale_1997


    EVPN    : esi-scale_1997
    EVI ID  : 5428
        ETH TAG : 0

    MAC Table
        Aging Time     : 320 seconds
        Limit          : 50000 entries
        Loop Prevention:
             admin-state: enabled
             loop-detection-window: 180 seconds
             mac-move-threshold: 5
             mac-restore: 300 seconds
             Number of restore-cycles: 3

    MAC address: e8:c5:7a:b0:ae:d6
        (1) Protocol: Local
            ESI: 00:00:00:00:00:00:00:00:19:97
            Interface: ge400-0/0/21
            MAC label: 4294967295 (local label of type 2)
            Timestamp: 13-Jul-2023-13:45:58
            Sticky: None          
            Sequence Number: 11
      
            Loop Prevention 
            ----------------
            Suppression State: Suppressed
            Expected Suppression Release Time:  13-Jul-2023-13:19:11
            Number of Completed Suppression Cycles: 1
      
            Move History
            ------------
      
            Time                     |   Interface   | Sequence Number 
            -------------------------+---------------+-----------------
            13-Jul-2023-13:02:21     | ge400-0/0/21  |         0
            13-Jul-2023-13:03:35     | 192.168.17.24 |         1
            13-Jul-2023-13:03:50     | ge400-0/0/21  |         2
            13-Jul-2023-13:03:55     | 192.168.17.24 |         3 
            13-Jul-2023-13:04:01     | ge400-0/0/21  |         4
            13-Jul-2023-13:05:11     | 192.168.17.24 |         5
            13-Jul-2023-13:05:11     | Suppressed    |         
            13-Jul-2023-13:10:11     | Released      |         
            13-Jul-2023-13:13:43     | ge400-0/0/21  |         6
            13-Jul-2023-13:13:45     | 192.168.17.24 |         7
            13-Jul-2023-13:13:50     | ge400-0/0/21  |         8
            13-Jul-2023-13:13:55     | 192.168.17.24 |         9 
            13-Jul-2023-13:14:07     | ge400-0/0/21  |         10
            13-Jul-2023-13:14:11     | 192.168.17.24 |         11
            13-Jul-2023-13:14:11     | Suppressed    |
      
    MAC address: e8:c5:7a:c8:d1:a4
        (1) Protocol: Local
            ESI: 00:00:00:00:00:00:00:00:19:97
            Interface: ge400-0/0/21
            MAC label: 4294967295 (local label of type 2)
            Timestamp: 13-Jul-2023-13:45:58
            Sticky: None         
            Sequence Number: 1
      
            Loop Prevention 
            ----------------
            Suppression State: None 
            Expected Suppression Release Time:  N/A
            Number of Completed Suppression Cycles: 0
      
            Move History
            ------------
      
            Time                     |   Interface   | Sequence Number 
            -------------------------+---------------+-----------------
            13-Jul-2023-13:05:27     | ge400-0/0/21  |         0
            13-Jul-2023-13:15:34     | 192.168.17.24 |         1
      
      

    MAC address: e8:c5:7a:a1:b3:25
        (1) Protocol: Local
            ESI: 00:00:00:00:00:00:00:00:23:54
            Interface: ge400-0/0/21
            MAC label: 113443 (local label of type 2)
            Timestamp: 13-Jul-2023-08:31:49
            Sticky: None          
            Sequence Number: 0
      
            Loop Prevention 
            ----------------
            Suppression State: None 
            Expected Suppression Release Time:  N/A
            Number of Completed Suppression Cycles: 0
      
            Move History
            ------------
      
            Time                     |   Interface   | Sequence Number 
            -------------------------+---------------+-----------------
            13-Jul-2023-13:05:27     | bundle-10.12  |         0

.. **Help line:** show information of the MAC Table of the EVPN instances

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 18.2    | Command introduced                  |
+---------+-------------------------------------+