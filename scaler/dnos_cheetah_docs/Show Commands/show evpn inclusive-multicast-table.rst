show evpn inclusive-multicast-table
-----------------------------------

**Minimum user role:** operator

To show the inclusive-multicast-table for an EVPN instance.

**Command syntax: show evpn inclusive-multicast-table** instance [evpn-name]

**Command mode:** operational

**Parameter table:**

+--------------------+-----------------------------------------+-------------------+---------------+
| Parameter          | Description                             | Values            | Default value |
+====================+=========================================+===================+===============+
| evpn-name          | The name of the EVPN instance           | String | all      | \-            |
+--------------------+-----------------------------------------+-------------------+---------------+

**Note:**

- Specifying an evpn-name will display the information of the specified EVPN instance.

- If no instance is specified, this will result in the listing of the inclusive-multicast-table information for all the EVPN instances.


**Example**
::


    dnRouter# show evpn inclusive-multicast-table

        Codes: L - Local route, B - BGP route,
             > - Selected route, S - Stale route

        EVPN: evpn1
            EVI ID : 1

            ETH TAG : 0
                Flags     | Originator IP   | Source          | Label     | Timestamp
                --------------------------------------------------------------------------------
                L>        | Local           | Local           | 991999    | 17-May-2023-10:18:54
                B>        | 7.7.7.7         | 52.52.52.52     | 1032382   | 17-May-2023-10:29:50
                B>        | 55.55.55.55     | 55.55.55.55     | 17        | 17-May-2023-10:29:37


.. **Help line:** show the information of the EVPN Inclusive Multicast Table of the EVPN instances

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 18.2    | Command introduced                  |
+---------+-------------------------------------+