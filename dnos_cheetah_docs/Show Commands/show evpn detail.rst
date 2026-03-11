show evpn detail
-------------------

**Minimum user role:** operator

To show the detailed information of an EVPN instance.

**Command syntax: show evpn detail** instance [evpn-name]

**Command mode:** operational

**Parameter table:**

+--------------------+-----------------------------------------+-------------------+---------------+
| Parameter          | Description                             | Values            | Default value |
+====================+=========================================+===================+===============+
| evpn-name          | The name of the EVPN instance           | String | all      | \-            |
+--------------------+-----------------------------------------+-------------------+---------------+

**Note:**

- Specifying an evpn-name will display the information of the specified EVPN instance.

- If no instance is specified, this will result in the listing of the detailed information for all the EVPN instances.


**Example**
::

    dnRouter# sh evpn instance evpn1 detail

    EVPN: evpn1
        EVI ID : 1
        Route Distinguisher            : 53:1
        Transport protocol             : mpls
        Fat label                      : disabled
        Control word                   : enabled
        MAC learning                   : enabled
        Allocated unicast label        : 107468
        Allocated IM label             : 991999

        MAC Table
        =========
        MAC table limit                : 64000
        MAC table aging time           : 320s
        Number of local entries        : 1
        Number of remote entries       : 0
        Number of moved events         : 0
        Total entries                  : 1

        MAC IP Table
        ============
        Number of local entries        : 0
        Number of remote entries       : 0
        Total entries                  : 0

        MAC Mobility
        ============
        Loop Prevention                : enabled
        Loop Prevention Action         : suppress
        Loop Detection Threshold       : 5
        Loop Detection Window          : 180s
        Mac Restore Timer              : 300s
        Mac Restore Max Cycles         : infinite
        Mac Restore Reset Interval     : 24h
        Number of suppressed entries   : 0

        Traffic counters
        ================
        RX Octets                      : 0
        RX Packets                     : 0
        RX Rate                        : 0 Mbps
        RX Known Unicast Packets       : 0
        RX BUM Packets                 : 0
        TX Octets                      : 2904946
        TX Packets                     : 2904946
        TX Rate                        : 2.39 Mbps
        TX Known Unicast Packets       : 0
        TX BUM Packets                 : 19365

        Number of neighbors : 2
        | IP Address   | IM Type-3   | MAC Type-2   | MAC/IP Type-2   |
        |--------------+-------------+--------------+-----------------|
        | 52.52.52.52  | 1           | 0            | 0               |
        | 55.55.55.55  | 1           | 0            | 0               |

        Number of interfaces : 1

        | Associated interfaces   | State      | Uptime              | Actual LocalHoming Type  | Learned MACs   |
        |-------------------------+------------+---------------------+--------------------------+----------------|
        | ge400-0/0/3.101         | enabled    | 0 days, 0:20:13     | single-homed             | 0              |

        (I) - DF Election Highest Preference, Invert Preference is enabled for this interface.

         Number of local multihomed ACs (ethernet segments): 0

      ESI: 00:11:22:33:44:55:11:22:33:44
        AC: ge100-0/0/74.2222 State: up / forwarding-all
        Requested Homing Type       : multi-homed-single-active
        Actual Homing Type          : multi-homed-single-active
        Role                        : designated-forwarder
        No-Preemption               : enabled
        Service label               : 118671
        Designated Forwarder        : 101.3.3.3
        Backup Designated Forwarder : 102.102.102.102
        Don't preempt               : enabled
        Time of Last DF Election    : 0 days, 0:19:01
        Requested Algorithm         : highest-preference (1000)
        Actual Algorithm            : mod

.. **Help line:** show detailed information for EVPN instances

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 18.2    | Command introduced                  |
+---------+-------------------------------------+