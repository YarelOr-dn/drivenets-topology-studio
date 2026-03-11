show evpn database
-------------------

**Minimum user role:** operator

To show the detailed information of an EVPN database.

**Command syntax: show evpn database** instance [evpn-name]

**Command mode:** operational

**Parameter table:**

+--------------------+-----------------------------------------+-------------------+---------------+
| Parameter          | Description                             | Values            | Default value |
+====================+=========================================+===================+===============+
| evpn-name          | The name of the EVPN instance           | String | all      | \-            |
+--------------------+-----------------------------------------+-------------------+---------------+

**Note:**

- Specifying an evpn-name  will display the information of the specified EVPN instance.

- If no instance is specified, this will result in the listing of the detailed information for all the EVPN instances.


**Example**
::

    dnRouter# show evpn database

    Codes: L - Local route, B - BGP route, P - Suppressed,
       I - Suppressed Indefinitely, s - Sticky, si - Sticky Interface, M - Only MAC-IP received
       > - Selected route, S - Stale route

    EVPN: evpn1
     EVI ID : 1

      ETH TAG: 0

        Inclusive-Multicast database:
        Flags     | Originator IP   | Source          | Label     | Timestamp
        --------------------------------------------------------------------------------
        L>        | Local           | Local           | 991999    | 17-May-2023-10:18:54
        B>        | 7.7.7.7         | 52.52.52.52     | 1032382   | 17-May-2023-10:29:50
        B>        | 55.55.55.55     | 55.55.55.55     | 17        | 17-May-2023-10:29:37

        MAC database:
        Flags     | MAC address          | ESI                           | IP Address      | Source               | Label     | Timestamp
        --------------------------------------------------------------------------------------------------------------------------------------------
        L>        | 00:10:10:00:00:53    | 00:11:22:33:44:55:66:77:88:99 | ::              | ge400-0/0/3.101      | 107468    | 17-May-2023-10:21:25
        Ls>       | 86:12:10:a0:01:ac    | 00:00:00:00:00:00:00:00:00:00 | ::              | bundle-23.12         | 234876    | 16-Jun-2023-12:23:43

    EVPN: evpn2
      EVI ID : 2

      ETH TAG: 0

        Inclusive-Multicast database:
        Flags     | Originator IP   | Source          | Label     | Timestamp
        --------------------------------------------------------------------------------
        L>        | Local           | Local           | 992000    | 17-May-2023-10:18:54
        B>        | 7.7.7.7         | 52.52.52.52     | 1032384   | 17-May-2023-10:29:50
         

.. **Help line:** show the database information of the EVPN instances

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 18.2    | Command introduced                  |
+---------+-------------------------------------+