show qos interfaces counters
----------------------------

**Minimum user role:** viewer

You can view the different policies that are attached to interfaces with selected counters. To view additional details on a specific policy, see show qos interfaces.

To display the QoS interface counters:



**Command syntax: show qos interfaces counters** [interface-name] [direction]

**Command mode:** operational



**Note**

- The counters are only available for the interfaces to which the policy is attached. That is, counters are available for a bundle interface, not for the bundle members.

- The "total packet drops" counter displays the sum of all the Tail and WRED drops and all green and yellow packet drop counters. Similarly, the total octet drop counter is the sum of all individual octet drop counters.

**Parameter table**

+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------+
|    Parameter   |                                                                  Description                                                                  |                Range               |
+================+===============================================================================================================================================+====================================+
| interface-name | The name of the interface for which you want to display the QoS policy. If you do not specify an interface, all interfaces will be displayed. | ge<interface speed>-<A>/<B>/<C>    |
|                |                                                                                                                                               |                                    |
|                |                                                                                                                                               |                                    |
|                |                                                                                                                                               | bundle-<bundle-id>                 |
|                |                                                                                                                                               |                                    |
|                |                                                                                                                                               |                                    |
|                |                                                                                                                                               | geX-<f>/<n>/<n>.<sub-interface-id> |
+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------+
| direction      | Filter the displayed information to the specified direction                                                                                   | in out                             |
+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------+

The following are the fields displayed for each interface:

+------------------------+-------------------------------------------------------------------------------------------+
| Field                  | Description                                                                               |
+========================+===========================================================================================+
| Interface              | The name of the interface                                                                 |
+------------------------+-------------------------------------------------------------------------------------------+
| Direction              | The direction of the traffic to which the QoS policy applies (in - ingress; out - egress) |
+------------------------+-------------------------------------------------------------------------------------------+
| Policy name            | The name of the policy                                                                    |
+------------------------+-------------------------------------------------------------------------------------------+
| Rule                   | The rule ID                                                                               |
+------------------------+-------------------------------------------------------------------------------------------+
| Matched packets/octets | The number of packets/octets that matched the rule                                        |
+------------------------+-------------------------------------------------------------------------------------------+
| Queue counters         | The number of packets/octets that were dropped due to queue limits                        |
+------------------------+-------------------------------------------------------------------------------------------+

**Example**
::

    dnRouter# show qos interfaces counters bundle-1
    No QoS policy configured


    dnRouter# show qos interfaces counters ge100-1/0/1

    Interface ge100-1/1/1:
    Policy name: ingress-policy   Direction: in

      Rule 1   Traffic-class Class-A
        Matched packets:                                  300000 (        4233 pps /       0 Mpps )
        Matched octets:                                 11100000 (     3223800 bps /     0.3 Mbps )
        Transmitted packets:                              295000 (          13 pps /       0 Mpps )
        Transmitted octets:                              6100000 (       26000 bps /       0 Mbps )
        Dropped packets:                                    5000 (          13 pps /       0 Mpps )
        Dropped octets:                                  5000000 (       26000 bps /       0 Mbps )

        Police                                            sr2cm, share rule 2
        Conformed packets:                                300000 (        4233 pps /       0 Mpps )
        Conformed octets:                               11100000 (     3223800 bps /     0.3 Mbps )
        Exceeded packets:                                 295000 (          13 pps /       0 Mpps )
        Exceeded octets:                                 6100000 (       26000 bps /       0 Mbps )
        Violated packet drops:                              5000 (          13 pps /       0 Mpps )
        Violated octet drops:                            5000000 (       26000 bps /       0 Mbps )

      Rule 2   Traffic-class Class-B
        Matched packets:                                  300000 (        4233 pps /       0 Mpps )
        Matched octets:                                 11100000 (     3223800 bps /     0.3 Mbps )
        Transmitted packets:                              295000 (          13 pps /       0 Mpps )
        Transmitted octets:                              6100000 (       26000 bps /       0 Mbps )
        Dropped packets:                                    5000 (          13 pps /       0 Mpps )
        Dropped octets:                                  5000000 (       26000 bps /       0 Mbps )

        Police                                            sr2cm, share rule 1
        Conformed packets:                                300000 (        4233 pps /       0 Mpps )
        Conformed octets:                               11100000 (     3223800 bps /     0.3 Mbps )
        Exceeded packets:                                 295000 (          13 pps /       0 Mpps )
        Exceeded octets:                                 6100000 (       26000 bps /       0 Mbps )
        Violated packet drops:                              5000 (          13 pps /       0 Mpps )
        Violated octet drops:                            5000000 (       26000 bps /       0 Mbps )

      Rule default
        Matched packets:                                  300000 (        4233 pps /       0 Mpps )
        Matched octets:                                 11100000 (     3223800 bps /     0.3 Mbps )
        Transmitted packets:                              295000 (          13 pps /       0 Mpps )
        Transmitted octets:                              6100000 (       26000 bps /       0 Mbps )
        Dropped packets:                                    5000 (          13 pps /       0 Mpps )
        Dropped octets:                                  5000000 (       26000 bps /       0 Mbps )

        Police                                            t3cm, share none
        Conformed packets:                                300000 (        4233 pps /       0 Mpps )
        Conformed octets:                               11100000 (     3223800 bps /     0.3 Mbps )
        Exceeded packets:                                 295000 (          13 pps /       0 Mpps )
        Exceeded octets:                                 6100000 (       26000 bps /       0 Mbps )
        Violated packet drops:                              5000 (          13 pps /       0 Mpps )
        Violated octet drops:                            5000000 (       26000 bps /       0 Mbps )

    Policy name: egress-policy   Direction: out

      Rule 1   Traffic-class RealTime
        Matched packets:                                  300000 (        4233 pps /       0 Mpps )
        Matched octets:                                 11100000 (     3223800 bps /     0.3 Mbps )
        Transmitted packets:                              295000 (          13 pps /       0 Mpps )
        Transmitted octets:                              6100000 (       26000 bps /       0 Mbps )
        Dropped packets:                                    5000 (          13 pps /       0 Mpps )
        Dropped octets:                                  5000000 (       26000 bps /       0 Mbps )

        Queue statistics:
          Current queue size (kbytes):                      80000 (           15 ms )
          Average queue size (kbytes):                      80000 (           15 ms )

          Tail green packet drops:                           5000
          Tail green octet drops:                         5000000
          Tail yellow packet drops:                          5000
          Tail yellow octet drops:                        5000000
          WRED green packet drops:                           5000
          WRED green octet drops:                         5000000
          WRED yellow packet drops:                          5000
          WRED yellow octet drops:                        5000000

      Rule default
        Matched packets:                                  300000 (        4233 pps /       0 Mpps )
        Matched octets:                                 11100000 (     3223800 bps /     0.3 Mbps )
        Transmitted packets:                              295000 (          13 pps /       0 Mpps )
        Transmitted octets:                              6100000 (       26000 bps /       0 Mbps )
        Dropped packets:                                    5000 (          13 pps /       0 Mpps )
        Dropped octets:                                  5000000 (       26000 bps /       0 Mbps )

        Queue statistics:
          Current queue size (kbytes):                      80000 (           15 ms )
          Average queue size (kbytes):                      80000 (           15 ms )

          Tail green packet drops:                           5000
          Tail green octet drops:                         5000000
          Tail yellow packet drops:                          5000
          Tail yellow octet drops:                        5000000
          WRED green packet drops:                           5000
          WRED green octet drops:                         5000000
          WRED yellow packet drops:                          5000
          WRED yellow octet drops:                        5000000

    dnRouter# show qos interfaces counters ge100-1/0/1 in

    Interface ge100-1/1/1:
    Policy name: ingress-policy   Direction: in

      Rule 1   Traffic-class Class4
        Matched packets:                                  300000 (        4233 pps /       0 Mpps )
        Matched octets:                                 11100000 (     3223800 bps /     0.3 Mbps )

      Rule default
        Matched packets:                                  300000 (        4233 pps /       0 Mpps )
        Matched octets:                                 11100000 (     3223800 bps /     0.3 Mbps )


    dnRouter# show qos interfaces counters bundle-3 out

    Interface bundle-3:
    Policy name: egress-policy   Direction: out

      Rule 1   Traffic-class RealTime
        Matched packets:                                  300000 (        4233 pps /       0 Mpps )
        Matched octets:                                 11100000 (     3223800 bps /     0.3 Mbps )
        Transmitted packets:                              295000 (          13 pps /       0 Mpps )
        Transmitted octets:                              6100000 (       26000 bps /       0 Mbps )
        Dropped packets:                                    5000 (          13 pps /       0 Mpps )
        Dropped octets:                                  5000000 (       26000 bps /       0 Mbps )

        Queue statistics:
          Current queue size (kbytes):                      80000 (           15 ms )
          Average queue size (kbytes):                      80000 (           15 ms )

          Tail green packet drops:                           5000
          Tail green octet drops:                         5000000
          Tail yellow packet drops:                          5000
          Tail yellow octet drops:                        5000000
          WRED green packet drops:                           5000
          WRED green octet drops:                         5000000
          WRED yellow packet drops:                          5000
          WRED yellow octet drops:                        5000000

      Rule default
        Matched packets:                                  300000 (        4233 pps /       0 Mpps )
        Matched octets:                                 11100000 (     3223800 bps /     0.3 Mbps )
        Transmitted packets:                              295000 (          13 pps /       0 Mpps )
        Transmitted octets:                              6100000 (       26000 bps /       0 Mbps )
        Dropped packets:                                    5000 (          13 pps /       0 Mpps )
        Dropped octets:                                  5000000 (       26000 bps /       0 Mbps )

        Queue statistics:
          Current queue size (kbytes):                      80000 (           15 ms )
          Average queue size (kbytes):                      80000 (           15 ms )

          Tail green packet drops:                           5000
          Tail green octet drops:                         5000000
          Tail yellow packet drops:                          5000
          Tail yellow octet drops:                        5000000
          WRED green packet drops:                           5000
          WRED green octet drops:                         5000000
          WRED yellow packet drops:                          5000
          WRED yellow octet drops:                        5000000


    dnRouter# show qos interfaces counters ge100-1/0/1 out

    Interface ge100-1/0/1:
    Policy name: egress-policy   Direction: out

      Rule 1   Traffic-class RealTime
        Matched packets:                                  300000 (        4233 pps /       0 Mpps )
        Matched octets:                                 11100000 (     3223800 bps /     0.3 Mbps )
        Transmitted packets:                              295000 (          13 pps /       0 Mpps )
        Transmitted octets:                              6100000 (       26000 bps /       0 Mbps )
        Dropped packets:                                    5000 (          13 pps /       0 Mpps )
        Dropped octets:                                  5000000 (       26000 bps /       0 Mbps )

        Queue statistics:
          Current queue size (kbytes):                      80000 (           15 ms )
          Average queue size (kbytes):                      80000 (           15 ms )

          Tail green packet drops:                           5000
          Tail green octet drops:                         5000000
          Tail yellow packet drops:                          5000
          Tail yellow octet drops:                        5000000
          WRED green packet drops:                            N/A
          WRED green octet drops:                             N/A
          WRED yellow packet drops:                           N/A
          WRED yellow octet drops:                            N/A
          ECN marked packets:                                5000
          ECN marked octets:                              5000000

      Rule default
        Matched packets:                                  300000 (        4233 pps /       0 Mpps )
        Matched octets:                                 11100000 (     3223800 bps /     0.3 Mbps )
        Transmitted packets:                              295000 (          13 pps /       0 Mpps )
        Transmitted octets:                              6100000 (       26000 bps /       0 Mbps )
        Dropped packets:                                    5000 (          13 pps /       0 Mpps )
        Dropped octets:                                  5000000 (       26000 bps /       0 Mbps )

        Queue statistics:
          Current queue size (kbytes):                      80000 (           15 ms )
          Average queue size (kbytes):                      80000 (           15 ms )

          Tail green packet drops:                           5000
          Tail green octet drops:                         5000000
          Tail yellow packet drops:                          5000
          Tail yellow octet drops:                        5000000
          WRED green packet drops:                            N/A
          WRED green octet drops:                             N/A
          WRED yellow packet drops:                           N/A
          WRED yellow octet drops:                            N/A
          ECN marked packets:                                5000
          ECN marked octets:                              5000000

.. **Help line:** show QoS counters


**Command History**

+---------+------------------------+
| Release | Modification           |
+=========+========================+
| 5.1.0   | Command introduced     |
+---------+------------------------+
| 9.0     | QoS not supported      |
+---------+------------------------+
| 11.2    | Command re-introduced  |
+---------+------------------------+
| 11.4    | Added support for WRED |
+---------+------------------------+
