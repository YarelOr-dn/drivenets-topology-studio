show qppb interfaces counters
------------------------------

**Minimum user role:** viewer

The per interface, per rule counters view for the installed QPPB policy.

To display the QPPB interfaces counters:



**Command syntax: show qqpb interfaces counters** [interface-name]

**Command mode:** operational



**Note**

- The counters are only available for the interfaces to which the policy is attached. That is, counters are available for a bundle interface, not for the bundle members.


**Parameter table**

+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+
|    Parameter   |                                                                  Description                                                                  |                Range                               |
+================+===============================================================================================================================================+====================================================+
| interface-name | The name of the interface for which you want to display the QoS policy. If you do not specify an interface, all interfaces will be displayed. | ge<interface speed>-<A>/<B>/<C>                    |
|                |                                                                                                                                               |                                                    |
|                |                                                                                                                                               |                                                    |
|                |                                                                                                                                               | bundle-<bundle-id>                                 |
|                |                                                                                                                                               |                                                    |
|                |                                                                                                                                               |                                                    |
|                |                                                                                                                                               | ge<interface speed>-<A>/<B>/<C>.<sub-interface-id> |
+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+


The following are the fields displayed for each interface:

+------------------------+-------------------------------------------------------------------------------------------+
| Field                  | Description                                                                               |
+========================+===========================================================================================+
| Policy name            | The name of the policy                                                                    |
+------------------------+-------------------------------------------------------------------------------------------+
| Interface              | The name of the interface                                                                 |
+------------------------+-------------------------------------------------------------------------------------------+
| Rule                   | The rule ID                                                                               |
+------------------------+-------------------------------------------------------------------------------------------+
| Match                  | The number of packets that matched the rule                                               |
+------------------------+-------------------------------------------------------------------------------------------+
| Drop                   | The number of packets that were dropped.                                                  |
+------------------------+-------------------------------------------------------------------------------------------+
| Tx                     | The number of packets that were transmitted.                                              |
+------------------------+-------------------------------------------------------------------------------------------+

**Example**
::

    dnRouter# show qppb interfaces counters

    QPPB Interface and Rule counters:

    Policy: policy-name


    | Interface          | Rule Id  | Match [Mbps] | Drop [Mbps]| TX[Mbps] | Match [pkts] | Drop [pkts] | TX[pkts] |
    +--------------------+----------+--------------+------------+----------+--------------+-------------+----------+
    | bundle-10.10       | 10       | 20           | 0          | 20       | 500          | 0.          | 500      |
    | bundle-10.10       | 20       | 30           | 0          | 30       | 57680        | 0           | 57680    |
    | bundle-258.1050    | 10       | 10           | 1          | 9        | 56           | 11          | 45       |
    | bundle-258.1050    | 20       | 50           | 0          | 50       | 8091         | 8           | 8083     |



    dnRouter# show qppb interfaces counters bundle-10.10

    QPPB Interface and Rule counters:

    Policy: policy-name
    Interface Name: bundle-10.10

    Rule Id: 10

        src-class: 20  dest-class: 25  applicable-vrf: default

        qos-tag: 5  drop-tag: green
        rate-limit: 10000 kbit/s burst-size: 200000 kbytes
        redirect-to-vrf: vrf-1
        nexthop-ipv4: none
        nexthop-ipv6: none

        Matched packets:                                       500   (           2 pps /       1.5 Mbps )
        Matched octets:                                        52435 (           0 bps /       0 Mbps   )
        Transmitted packets:                                   500   (           2 pps /       1.5 Mbps )
        Transmitted octets:                                    52435 (           0 bps /       0 Mbps   )
        Dropped packets:                                       0     (           0 pps /       0 Mbps   )
        Dropped octets:                                        0     (           0 bps /       0 Mbps   )

    Rule Id: 20

        src-class: 29  dest-class: 17  applicable-vrf: vrf-1

        qos-tag: 5  drop-tag: yellow
        rate-limit: 50000 kbit/s burst-size: 220000 kbytes
        redirect-to-vrf: vrf-2
        nexthop-ipv4: none
        nexthop-ipv6: none

        Matched packets:                                       57680   (           3 pps /       2.2 Mpps )
        Matched octets:                                        152634  (           0 bps /       0 Mbps   )
        Transmitted packets:                                   57680   (           2 pps /       1.5 Mpps )
        Transmitted octets:                                    152634  (           0 bps /       0 Mbps   )
        Dropped packets:                                       0       (           0 pps /       0 Mpps   )
        Dropped octets:                                        0       (           0 bps /       0 Mbps   )


    Rule Id: 30

        src-class: 31  dest-class: 15  applicable-vrf: default

        qos-tag: 3  drop-tag: yellow
        rate-limit: 50000 kbit/s burst-size: 220000 kbytes
        redirect-to-vrf: none
        nexthop-ipv4: none
        nexthop-ipv6: 1200:22::10:22

        Matched packets:                                       57680   (           3 pps /       2.2 Mpps )
        Matched octets:                                        152634  (           0 bps /       0 Mbps   )
        Transmitted packets:                                   57680   (           2 pps /       1.5 Mpps )
        Transmitted octets:                                    152634  (           0 bps /       0 Mbps   )
        Dropped packets:                                       0       (           0 pps /       0 Mpps   )
        Dropped octets:                                        0       (           0 bps /       0 Mbps   )


    Rule Id: 50

        src-class: 39  dest-class: 75  applicable-vrf: default

        qos-tag: none  drop-tag: none
        rate-limit: none burst-size: none
        redirect-to-vrf: none
        nexthop-ipv4: 168.77.5.21
        nexthop-ipv6: none

        Matched packets:                                       57680   (           3 pps /       2.2 Mpps )
        Matched octets:                                        152634  (           0 bps /       0 Mbps   )
        Transmitted packets:                                   57680   (           2 pps /       1.5 Mpps )
        Transmitted octets:                                    152634  (           0 bps /       0 Mbps   )
        Dropped packets:                                       0       (           0 pps /       0 Mpps   )
        Dropped octets:                                        0       (           0 bps /       0 Mbps   )

    Rule Id: 100

        src-class: any  dest-class: 25  applicable-vrf: default

        qos-tag: 6  drop-tag: green
        rate-limit: 10000 kbit/s burst-size: 200000 kbytes
        redirect-to-vrf: vrf-5
        nexthop-ipv4: none
        nexthop-ipv6: none


        Matched packets:                                       57680   (           3 pps /       2.2 Mpps )
        Matched octets:                                        152634  (           0 bps /       0 Mbps   )
        Transmitted packets:                                   57680   (           2 pps /       1.5 Mpps )
        Transmitted octets:                                    152634  (           0 bps /       0 Mbps   )
        Dropped packets:                                       0       (           0 pps /       0 Mpps   )
        Dropped octets:                                        0       (           0 bps /       0 Mbps   )

.. **Help line:** show QPPB interfaces counters


**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
