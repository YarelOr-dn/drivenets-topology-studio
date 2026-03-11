show qppb policy rules
------------------------

**Minimum user role:** viewer

The command shall present detailed information and QPPB counters for the installed policy.

To display the QPPB policy rules:



**Command syntax: show qppb policy rules** [rule-id]

**Command mode:** operational



**Note**

- The counters are the total for each rule of the per interface per rule counters displayed with the show QPPB interfaces counters.


**Parameter table**

+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------+
|    Parameter   |                                                                  Description                                                                  |                Range               |
+================+===============================================================================================================================================+====================================+
| rule-id        | The id of the rule for which you want to display the QoS policy. If you do not specify a rule, all rules will be displayed.                   | 1..128                             |
|                |                                                                                                                                               |                                    |
+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------+


The following are the fields displayed:

+------------------------+-------------------------------------------------------------------------------------------+
| Field                  | Description                                                                               |
+========================+===========================================================================================+
| Policy name            | The name of the policy                                                                    |
+------------------------+-------------------------------------------------------------------------------------------+
| Rule                   | The rule ID                                                                               |
+------------------------+-------------------------------------------------------------------------------------------+
| src-class              | The Source Class                                                                          |
+------------------------+-------------------------------------------------------------------------------------------+
| dest-class             | The Destination Class                                                                     |
+------------------------+-------------------------------------------------------------------------------------------+
| applicable-vrf         | The VRF upon which the rule is applied                                                    |
+------------------------+-------------------------------------------------------------------------------------------+
| ip-version             | The ip-version: ipv4/ipv6/both upon which the rule is applied                             |
+------------------------+-------------------------------------------------------------------------------------------+
| qos-tag                | The qos tag to be applied                                                                 |
+------------------------+-------------------------------------------------------------------------------------------+
| drop-tag               | The drop-tag to be applied                                                                |
+------------------------+-------------------------------------------------------------------------------------------+
| rate-limit             | The rate limit (per core) that shall be applied to the matching traffic                   |
+------------------------+-------------------------------------------------------------------------------------------+
| burst-size             | The burst-size that shall be alloed                                                       |
+------------------------+-------------------------------------------------------------------------------------------+
| redirect-to vrf        | The vrf to which the traffic should be handled                                            |
+------------------------+-------------------------------------------------------------------------------------------+
| nexthop-ipv4           | The ipv4 address that the traffic should be forwarded to                                  |
+------------------------+-------------------------------------------------------------------------------------------+
| nexthop-ipv6           | The ipv6 address that the traffic should be forwarded to                                  |
+------------------------+-------------------------------------------------------------------------------------------+
| Matched                | The number of packets/octets that matched the rule                                        |
+------------------------+-------------------------------------------------------------------------------------------+
| Dropped                | The number of packets/octetst that were dropped                                           |
+------------------------+-------------------------------------------------------------------------------------------+
| Transmitted            | The number of packets/octets that were transmitted                                        |
+------------------------+-------------------------------------------------------------------------------------------+

**Example**
::

    dnRouter# show qppb policy rules

    Policy Name: policy-1

    Rule Id: 10

        src-class: 20  dest-class: 25  applicable-vrf: default ip-version: any

        qos-tag: 5  drop-tag: green
        rate-limit: 10000 kbit/s burst-size: 200000 kbytes
        redirect-to-vrf: vrf-1
        nexthop-ipv4: none
        nexthop-ipv6: none

        Matched packets:                                       500   (           2 pps /       1.5 Mpps )
        Matched octets:                                        52435 (           0 bps /       0 Mbps   )
        Transmitted packets:                                   500   (           2 pps /       1.5 Mpps )
        Transmitted octets:                                    52435 (           0 bps /       0 Mbps   )
        Dropped packets:                                       0     (           0 pps /       0 Mpps   )
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



    dnRouter# show qppb policy rules 10

    QPPB Interface and Rule counters:

    Policy: Policy-1

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



.. **Help line:** show QPPB policy


**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
