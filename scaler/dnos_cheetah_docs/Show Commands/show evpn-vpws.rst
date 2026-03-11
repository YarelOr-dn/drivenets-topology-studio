show evpn-vpws
--------------

**Minimum user role:** operator

To show the detailed information of an EVPN-VPWS instance.

**Command syntax: show evpn-vpws** instance [evpn-vpws-name]  

**Command mode:** operational

**Parameter table:**

+--------------------+-----------------------------------------+-------------------+---------------+
| Parameter          | Description                             | Values            | Default value |
+====================+=========================================+===================+===============+
| evpn-vpws-name     | The name of the EVPN-VPWS instance      | String | all      | \-            |
+--------------------+-----------------------------------------+-------------------+---------------+

**Note:**

- Specifying an evpn-vpws-name will display the information of the specified EVPN-VPWS instance.

- If no instance is specified, this will result in the listing of the information for all the EVPN-VPWS instances.


**Example**
::


    dnRouter# show evpn-vpws

    EVPN-VPWS: MH_TEST2501
        Type                  : multi-homed-all-active
        Local AC Interface    : ge100-0/0/75.2501 (up / forwarding-all)
        Local-ESI             : 00:33:22:33:22:33:22:33:22:33
        Local VPWS-ID         : 25013
        Remote-ESI            : 00:00:00:00:00:00:00:00:00:00
        Remote VPWS-ID        : 25018
        State                 : up
        Uptime                : 0 days, 6:55:36

        Number of neighbors : 1

        Flags codes: P - primary, B - backup, ND - non-DF,
               F - FAT-label, C - control-word, I - installed,
               A - all-active, S - single-active, s - stale


        | IP Address        | Flags        | Time in state       | Failed reason              |
        +-------------------+--------------+---------------------+----------------------------+
        | 101.8.8.8         | ND/I         | 0 days, 0:05:25     |                            |


        EVPN-VPWS: test_2505
        Type                  : single-homed
        Local AC Interface    : ge100-0/0/75.2505 (up / forwarding-all)
        Local-ESI             : 00:00:00:00:00:00:00:00:00:00
        Local VPWS-ID         : 25053
        Remote-ESI            : 00:11:22:33:44:55:66:77:88:99
        Remote VPWS-ID        : 25058
        State                 : up
        Uptime                : 0 days, 6:55:36

        Number of neighbors : 2

        Flags codes: P - primary, B - backup, ND - non-DF,
               F - FAT-label, C - control-word, I - installed,
               A - all-active, S - single-active, s - stale


        | IP Address        | Flags        | Time in state       | Failed reason              |
        +-------------------+--------------+---------------------+----------------------------+
        | 101.6.6.6         | B/C/F/S      | 0 days, 0:02:16     |                            |
        | 101.8.8.8         | P/C/F/I/S    | 0 days, 0:02:16     |                            |


    EVPN-VPWS: test_2506
        Type                  : single-homed
        Local AC Interface    : ge100-0/0/75.2506 (up / forwarding-all)
        Local-ESI             : 00:00:00:00:00:00:00:00:00:00
        Local VPWS-ID         : 25063
        Remote-ESI            : N/A
        Remote VPWS-ID        : 25068
        State                 : None
        Uptime                : 0 days, 0:00:05
    
    

.. **Help line:** show detailed information for EVPN instances

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 18.2    | Command introduced                  |
+---------+-------------------------------------+