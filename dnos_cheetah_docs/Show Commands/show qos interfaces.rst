show qos interfaces
-------------------

**Minimum user role:** viewer

This command displays all the details related to the QoS policy that is attached to the specified interface, including counters.

To view the detailed QoS policy attached to a specific interface:



**Command syntax: show qos interfaces** [interface-name] [direction]

**Command mode:** operational



**Note**

- For a bundle interface, the displayed max-size, yellow-threshold, guaranteed rate and max-bandwidth is for the total of the operational bundle members.

.. -  bundle interface max-size, yellow-threshold, guaranteed rate and max-bandwidth, policer rates and bursts indicate the total of the operational bundle members. The information is not dependent on the operational state of the members, i.e. are not updated if the member operational state is down.

**Parameter table**

+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+
| Parameter      | Description                                                                                                                                   | Range                                              |
+================+===============================================================================================================================================+====================================================+
| interface-name | The name of the interface for which you want to display the QoS policy. If you do not specify an interface, all interfaces will be displayed. | ge<interface speed>-<A>/<B>/<C>                    |
|                |                                                                                                                                               |                                                    |
|                |                                                                                                                                               | bundle-<bundle-id>                                 |
|                |                                                                                                                                               |                                                    |
|                |                                                                                                                                               | ge<interface speed>-<A>/<B>/<C>.<sub-interface-id> |
+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+
| direction      | Filter the displayed information to the specified direction                                                                                   | in                                                 |
|                |                                                                                                                                               | out                                                |
+----------------+-----------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+

**Example**
::

    dnRouter# show qos interfaces ge100-1/0/1

    Interface ge100-1/0/1:
    ip-marking: trusted

    Policy name: ingress-policy    Direction: in

      Rule 1
        Traffic-class:                            my_traffic_class
          Match                                   any
          Dscp                                    4, 5, 6, af11
        Set configuration:
          Qos-tag                                 4

      Rule 2
        Traffic-class:                            my_traffic_class1
          Match                                   any
          Mpls-exp                                4, 5, 6
          Precedence                              4, 5, 6
        Set configuration:
          Qos-tag                                 6
          Drop-tag                                yellow

      Rule default
        Set configuration:
          Qos-tag                                 0
          Drop-tag                                green
          Mpls-exp                                0

    Policy name: egress-policy    Direction: out

      Rule 1
        Traffic-class:                            my_traffic_class2
          Match                                   any
          Qos-tag                                 4, 5, 6
        Queue Configuration:
          Type                                    af
          Max-size                                80000                         kbytes (15 ms)
          Yellow-threshold                        40000                         kbytes (7500 us)
          Bandwidth                               10 %
          Guaranteed rate                         900000                        kbps
          Max-bandwidth                           n/a
          Shaper Burst                            n/a
          Wred-profile                            my_wred_profile
            Green-min-threshold                   26000                         kbytes (5 ms)
            Green-max-threshold                   80000                         kbytes (15 ms)
            Green-max-drop                        10 %
            Yellow-min-threshold                  13000                         kbytes (2500 us)
            Yellow-max-threshold                  40000                         kbytes (7500 us)
            Yellow-max-drop                       10 %
          Ecn-profile                             n/a

     Rule 2
       Traffic-class:                             my_traffic_class3
         Match any
         Qos-tag                                  7
       Queue Configuration:
         Type                          ef
         Max-size                      80,000                      kbytes (15 ms)
         Yellow-threshold              80,000                      kbytes (15 ms)
         Bandwidth                     n/a
         Guaranteed rate               1,000,000                   kbps
         Max-bandwidth                 1,000,000 (10 %)            kbps
         Shaper Burst                  25,000                      kbytes (4 ms)
         Wred-profile                  n/a
         Ecn-profile                   my_ecn_profile
            Min-threshold              26000                       kbytes (5 ms)
            Max-threshold              80000                       kbytes (15 ms)
            Max-probability            10 %

     Rule default
       Queue Configuration:
         Type                          df
         Max-size                      80,000                     kbytes (15 ms)
         Yellow-threshold              40,000                     kbytes (7500 us)
         Bandwidth                     10 %
         Guaranteed rate               900,000                    kbps
         Max-bandwidth                 n/a
         Shaper Burst                  n/a
         Wred-profile                  n/a
         Ecn-profile                   n/a

   dnRouter# show qos interfaces ge10-1/0/1/2 out

     Interface ge10-1/0/1/2:
     ip-marking: untrusted

     Policy name: egress-peering   Direction: out

     Rule 1
       Traffic-class:                 my_traffic_class1
         Match                         any
         Qos-tag                       6
       Set configuration:
         Pcp
           qos-tag all drop-tag all     3
         Dscp
           qos-tag all drop-tag all    cs1
       Queue Configuration:
         Type                          af
         Max-size                      80,000                     kbytes (15 ms)
         Yellow-threshold              40,000                     kbytes (7500 us)
         Bandwidth                     10 %
         Guaranteed rate               900,000                    kbps
         Max-bandwidth                 n/a
         Shaper Burst                  n/a
         Wred-profile                  my_wred_profile
           Green-min-threshold         26,000                     kbytes (5 ms)
           Green-max-threshold         80,000                     kbytes (15 ms)
           Yellow-min-threshold        13,000                     kbytes (2500 us)
           Yellow-max-threshold        40,000                     kbytes (7500 us)

     Rule default
       Set configuration:
         Dscp
           qos-tag all drop-tag all    cs1
       Queue Configuration:
         Type                                     ef
         Max-size                                 80000                         kbytes (15 ms)
         Yellow-threshold                         8000                          kbytes (15 ms)
         Bandwidth                                n/a
         Guaranteed rate                          1000000                       kbps
         Max-bandwidth                            1000000 (10 %)                kbps
         Shaper Burst                             25000                         kbytes (4 ms)
         Wred-profile                             n/a

      Rule default
        Queue Configuration:
          Type                                    df
          Max-size                                80000                         kbytes (15 ms)
          Yellow-threshold                        40000                         kbytes (7500 us)
          Bandwidth                               10 %
          Guaranteed rate                         900000                        kbps
          Max-bandwidth                           n/a
          Shaper Burst                            n/a
          Wred-profile                            none

    dnRouter# show qos interfaces ge10-1/0/1/2 out

    Interface ge10-1/0/1/2:
    ip-marking: untrusted

    Policy name: egress-peering    Direction: out

      Rule 1
        Traffic-class:                            my_traffic_class1
          Match                                   any
          Qos-tag                                 6
        Set configuration:
          Pcp                                     3
          Dscp
            qos-tag all drop-tag all              cs1
        Queue Configuration:
          Type                                    af
          Max-size                                80000                         kbytes (15 ms)
          Yellow-threshold                        40000                         kbytes (7500 us)
          Bandwidth                               10 %
          Guaranteed rate                         900000                        kbps
          Max-bandwidth                           n/a
          Shaper Burst                            n/a
          Wred-profile                            my_wred_profile
            Green-min-threshold                   26000                         kbytes (5 ms)
            Green-max-threshold                   80000                         kbytes (15 ms)
            Green-max-drop                        10 %
            Yellow-min-threshold                  13000                         kbytes (2500 us)
            Yellow-max-threshold                  40000                         kbytes (7500 us)
            Yellow-max-drop                       10 %

      Rule default
        Set configuration:
          Pcp                                     3
          Dscp
            qos-tag all drop-tag all              cs1
        Queue Configuration:
          Type                                    df
          Max-size                                80000                         kbytes (15 ms)
          Yellow-threshold                        40000                         kbytes (7500 us)
          Bandwidth                               10 %
          Guaranteed rate                         900000                        kbps
          Max-bandwidth                           n/a
          Shaper Burst                            n/a
          Wred-profile                            none

    dnRouter# show qos interfaces ge10-1/0/1/2 in

    Interface ge10-1/0/1/2:
    ip-marking: untrusted

    Policy name: ingress-peering  Direction: in

      Rule default
        Set configuration:
          Qos-tag                                 1
          Drop-tag                                green
          Dscp                                    cs1 (implicit)

    dnRouter# show qos interfaces bundle-1 out

    Interface bundle-1:
    ip-marking: trusted

    Policy name: egress-policy    Direction: out

      Rule 1
        Traffic-class:                            my_traffic_class2
          Match                                   any
          Qos-tag                                 4, 5, 6
        Queue Configuration:
          Type                                    af
          Max-size                                160000                        kbytes (15 ms)
          Yellow-threshold                        80000                         kbytes (7500 us)
          Bandwidth                               10 %
          Guaranteed rate                         1800000                       kbps
          Max-bandwidth                           n/a
          Shaper Burst                            n/a
          Wred-profile                            my_wred_profile
            Green-min-threshold                   52000                         kbytes (5 ms)
            Green-max-threshold                   160000                        kbytes (15 ms)
            Green-max-drop                        10 %
            Yellow-min-threshold                  26000                         kbytes (2500 us)
            Yellow-max-threshold                  80000                         kbytes (7500 us)
            Yellow-max-drop                       10 %

      Rule 2
        Traffic-class:                             my_traffic_class3
          Match any
          Qos-tag                                  7
        Queue Configuration:
          Type                                     ef
          Max-size                                 160000                        kbytes (15 ms)
          Yellow-threshold                         16000                         kbytes (15 ms)
          Bandwidth                                n/a
          Guaranteed rate                          2000000                       kbps
          Max-bandwidth                            2000000 (10 %)                kbps
          Shaper Burst                             250000                        kbytes (4 ms)
          Wred-profile                             n/a

      Rule default
        Queue Configuration:
          Type                                    df
          Max-size                                160000                        kbytes (15 ms)
          Yellow-threshold                        80000                         kbytes (7500 us)
          Bandwidth                               10 %
          Guaranteed rate                         1800000                       kbps
          Max-bandwidth                           n/a
          Shaper Burst                            n/a
          Wred-profile                            none


    Interface ge100-0/0/1:
    ip-marking: trusted

    Policy name: egress-policy    Direction: out

      Rule 1
        Traffic-class:                            my_traffic_class2
          Match                                   any
          Qos-tag                                 4, 5, 6
        Queue Configuration:
          Type                                    af
          Max-size                                80000                         kbytes (15 ms)
          Yellow-threshold                        40000                         kbytes (7500 us)
          Bandwidth                               10 %
          Guaranteed rate                         900000                        kbps
          Max-bandwidth                           n/a
          Shaper Burst                            n/a
          Wred-profile                            my_wred_profile
            Green-min-threshold                   26000                         kbytes (5 ms)
            Green-max-threshold                   80000                         kbytes (15 ms)
            Yellow-min-threshold                  13000                         kbytes (2500 us)
            Yellow-max-threshold                  40000                         kbytes (7500 us)

      Rule 2
        Traffic-class:                             my_traffic_class3
          Match any
          Qos-tag                                  7
        Queue Configuration:
          Type                                     ef
          Max-size                                 80000                         kbytes (15 ms)
          Yellow-threshold                         8000                          kbytes (15 ms)
          Bandwidth                                n/a
          Guaranteed rate                          1000000                       kbps
          Max-bandwidth                            1000000 (10 %)                kbps
          Shaper Burst                             25000                         kbytes (4 ms)
          Wred-profile                             n/a

       Rule default
         Queue Configuration:
           Type                                    df
           Max-size                                80000                         kbytes (15 ms)
           Yellow-threshold                        40000                         kbytes (7500 us)
           Bandwidth                               10 %
           Guaranteed rate                         900000                        kbps
           Max-bandwidth                           n/a
           Shaper Burst                            n/a
           Wred-profile                            none

    Interface ge100-1/0/2:
    ip-marking: trusted

    Policy name: egress-policy   Direction: out

     ...

    dnRouter# show qos interfaces ge100-1/0/1

    Interface ge100-1/0/1:
    ip-marking: trusted

    Policy name: ingress-policy    Direction: in

      Rule 1
        Traffic-class:                            my_traffic_class
          Match                                   any
          Dscp                                    4, 5, 6, af11
        Set configuration:
          Qos-tag                                 4
        Policer configuration:
          Marker                                  tr3cm
          Committed rate                          32000000 (32%)                kbps
          Excess rate                             2000000 (2%)                  kbps
          Committed burst                         20000                         kbytes (5 ms)
          Excess burst                            1250 (auto)                   kbytes (625 us)
          Color mode                              color-aware
          Rank                                    none

      Rule 2
        Traffic-class:                            my_traffic_class1
          Match                                   any
          Mpls-exp                                4, 5, 6
          Precedence                              4, 5, 6
        Set configuration:
          Qos-tag                                 4
          Drop-tag                                yellow
        Policer configuration:
          Marker                                  implicit shared
          Rule                                    1

      Rule default
        Set configuration:
          Qos-tag                                 0
          Drop-tag                                green
       Policer configuration:
          Marker                                  sr3cm
          Committed rate                          32,000,000 (32%)              kbps
          Excess rate                             2,000,000 (2%)                kbps
          Committed burst                         40,000                        kbytes (10 ms)
          Color mode                              color-blind
          Rank                                    none

    dnRouter# show qos interfaces bundle-5 in

    Interface bundle-5:
    ip-marking: trusted

    Policy name: ingress-policy    Direction: in

      Rule default
        Set configuration:
          Qos-tag                                 0
          Drop-tag                                green
        Policer configuration:
          Marker                                  sr3cm
          Total committed rate                    160000000 (32%)               kbps
          Total excess rate                       10000000 (2%)                 kbps
          Committed burst                         200000                        kbytes (10 ms)
          Color mode                              color-blind

          NCP Core information
            NCP 0 Core 0                          300000000                     kbps
              Committed rate                      96000000 (32%)                kbps
              Excess rate                         6000000 (2%)                  kbps
              Committed burst                     120000                        kbytes (10 ms)
              Interfaces:
                ge100-0/0/1
                ge100-0/0/22
                ge100-0/0/23
            NCP 0 Core 1                          100000000                     kbps
              Committed rate                      32000000 (32%)                kbps
              Excess rate                         2000000 (2%)                  kbps
              Committed burst                     40000                         kbytes (10 ms)
              Interfaces:
                ge100-0/0/12
            NCP 1 Core 0                          100000000                     kbps
              Committed rate                      32000000 (32%)                kbps
              Excess rate                         2000000 (2%)                  kbps
              Committed burst                     40000                         kbytes (10 ms)
              Interfaces:
                ge100-1/0/7

    Interface ge100-0/0/1:
    ip-marking: trusted

      Rule default
        Set configuration:
          Qos-tag                                 0
          Drop-tag                                green
        Policer configuration:
          NCP Core information                    NCP 0 Core 0

    Interface ge100-0/0/22:
    ip-marking: trusted

      Rule default
        Set configuration:
          Qos-tag                                 0
          Drop-tag                                green
        Policer configuration:
          NCP Core information                    NCP 0 Core 0

     dnRouter# show qos interfaces ge100-1/0/1

    Interface ge100-1/0/1:
    ip-marking: trusted

    Policy name: ingress-policy   Direction: in
    Scope: remaining traffic
    ....

   **Help line:** show configured policies attached to an interface


    # Policy defined on an interface with sub-interface policies
    # with added indication that the scope is limited to 'remaining'
    # traffic

    Policy_name: egress-peering   Direction: out

      Rule 1
        Traffic-class:                            my_traffic_class2
          Match                                   any
          Qos-tag                                 4, 5, 6
        Queue Configuration:
          Type                                    af
          Max-size                                8000                          kbytes (15 ms)
          Yellow-threshold                        4000                          kbytes (7500 us)
          Bandwidth                               10 %
          Guaranteed rate                         90000                         kbps
          Max-bandwidth                           n/a
          Shaper Burst                            n/a
          Wred-profile                            my_wred_profile
            Green-min-threshold                   2600                          kbytes (5 ms)
            Green-max-threshold                   8000                          kbytes (15 ms)
            Yellow-min-threshold                  1300                          kbytes (2500 us)
            Yellow-max-threshold                  4000                          kbytes (7500 us)

      Rule default
        Queue Configuration:
          Type                                    df
          Max-size                                8000                          kbytes (15 ms)
          Yellow-threshold                        4000                          kbytes (7500 us)
          Bandwidth                               10 %
          Guaranteed rate                         90000                         kbps
          Max-bandwidth                           n/a
          Shaper Burst                            n/a
          Wred-profile                            none


    # Hierarchical policy: LAG physical policy.
    # Parent policy relative shaping setting.
    # Per NCP information is shown at parent.

    dnRouter# show qos interfaces bundle-3.100 out

    Interface: bundle.100
    ip-marking: trusted

    Policy_name: egressP-parent   Direction: out

    Rule default
      Shape configuration:
        Total Average Rate                      160000000 (32%)               kbps
        Total Shaper Burst                      1864                          kbytes (150 us)
        NCP Core information
          NCP 0 Core 0                          300000000                     kbps
            Average Rate                        96000000 (32%)                kbps
            Interfaces:
              ge100-0/0/1
              ge100-0/0/22
              ge100-0/0/23
          NCP 0 Core 1                          100000000                     kbps
            Average rate                        32000000 (32%)                kbps
            Interfaces:
              ge100-0/0/12
          NCP 1 Core 0                          100000000                     kbps
            Average rate                        32000000 (32%)                kbps
            Interfaces:
              ge100-1/0/7
      Child-policy: egressP

    Policy_name: egressP   Direction: out

    Rule 1
      Traffic-class:                 my_traffic_class1
    ...

    # Hierarchical policy: LAG logical policy.
    # Parent policy absolute shaping setting of 320mbps.
    # Per NCP information is shown at parent.
    # Total is twice the configured (!)

    dnRouter# show qos interfaces bundle-3.100 out

     Interface: bundle.100
     ip-marking: trusted

     Policy_name: egressP-parent   Direction: out

     Rule default
        Shape configuration:
          Total Average Rate                      640000                        kbps
          Total Shaper Burst                      1864                          kbytes (150 us)
          NCP Core information
            NCP 0 Core 0                          200000000                     kbps
              Average rate                        320000                        kbps
              Interfaces:
                ge100-0/0/1
                ge100-0/0/22
            NCP 0 Core 1                          200000000                     kbps
              Average rate                        320000                        kbps
              Interfaces:
                ge100-0/0/12
                ge100-1/0/7
        Child-policy:
          Policy name                             egressP

     Policy_name: egressP   Direction: out

     Rule 1
       Traffic-class:                 my_traffic_class1
    ...


    # Hierarchical ingress policy: MEF policers
    # 1. parent and child policies
    # 2. rank - printed only when a policer (non shared) is defined, but not on parent policy.
    # when rank is printed, the following lines are also printed:
    #    'use shared tokens' strict implies 'false', otherwise 'true'
    #     add Max committed/excess rate whenever rank is shown configured.
    #     Max equals to Total if 'strict', otherwise, max cir is the sum of
    #     cirs of higher cir ranks, max eir is the sum of max eirs.
    # 3. shared: 'implicit shared' marker type instead of 'shared' info
    #    added 'shared' marker type

    dnRouter# show qos interfaces ge100-1/0/1 in

    Interface ge100-1/0/1:
    ip-marking: trusted

    Policy_name: ingress-peering-parent   Direction: in

      Rule default
        Policer configuration:
          Marker                                  tr3cm
          Committed rate                          10000000 (10%)                kbps
          Excess rate                             20000000 (20%)                kbps
          Committed burst                         20000                         kbytes (5 ms)
          Excess burst                            1250 (auto)                   kbytes (625 us)
          Color mode                              color-aware
        Child-policy:
          Policy name                             ingress-policy

    Policy name: ingress-policy    Direction: in

      Rule 1
        Traffic-class:                            my_traffic_class-7
          Match                                   any
          Mpls-exp                                7
          Precedence                              7
        Set configuration:
          Qos-tag                                 7
          Drop-tag                                green
        Policer configuration:
          Marker                                  tr3cm
          Committed rate                          100000 (1%)                   kbps
          Excess rate                             200000 (2%)                   kbps
          Max committed rate                      100000 (1%)                   kbps
          Max excess rate                         200000 (2%)                   kbps
          Committed burst                         20000                         kbytes (5 ms)
          Excess burst                            1250 (auto)                   kbytes (625 us)
          Color mode                              color-aware
          Rank                                    4

      Rule 2
        Traffic-class:                            my_traffic_class-6
          Match                                   any
          Mpls-exp                                6
          Precedence                              6
        Set configuration:
          Qos-tag                                 6
          Drop-tag                                green
        Policer configuration:
          Marker                                  tr3cm
          Committed rate                          1000000 (10%)                 kbps
          Excess rate                             2000000 (20%)                 kbps
          Max committed rate                      1100000 (11%)                 kbps
          Max excess rate                         2100000 (22%)                 kbps
          Committed burst                         20000                         kbytes (5 ms)
          Excess burst                            1250 (auto)                   kbytes (625 us)
          Color mode                              color-aware
          Rank                                    3
          Use shared tokens                       true

      Rule 3
        Traffic-class:                            my_traffic_class-5
          Match                                   any
          Mpls-exp                                5
          Precedence                              5
        Set configuration:
          Qos-tag                                 4
          Drop-tag                                green
        Policer configuration:
          Marker                                  shared
          Rule                                    2

      Rule 4
        Traffic-class:                            my_traffic_class-4
          Match                                   any
          Mpls-exp                                4
          Precedence                              4
        Set configuration:
          Qos-tag                                 4
          Drop-tag                                yellow
        Policer configuration:
          Marker                                  implicit shared
          Rule                                    2

      Rule default
        Set configuration:
          Qos-tag                                 0
          Drop-tag                                green


**Command mode:** operational

**TACACS role:** viewer

**Note:**

-  bundle interface max-size, yellow-threshold, guaranteed rate and max-bandwidth, policer rates and bursts indicate the total of the operational bundle members. The information is not dependent on the operational state of the members, i.e. are not updated if the member operational state is down.

-  once sub-interface policies are defined, a policy set on the interface, which are not 'shaper only' or 'policer only' policies have a limited 'remaining' scope. The additional 'scope: remaining traffic' line should be added, following the 'ip-marking' configuration.

**Help line:** show configured policies attached to an interface

**Parameter table:**

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 5.1.0   | Command introduced                 |
+---------+------------------------------------+
| 6.0     | Updated command output             |
+---------+------------------------------------+
| 9.0     | QoS not supported                  |
+---------+------------------------------------+
| 11.2    | Command re-introduced              |
+---------+------------------------------------+
| 11.4    | Added support for WRED             |
+---------+------------------------------------+
| 13.0    | Added support for QoS DSCP marking |
+---------+------------------------------------+
| 16.1    | Added support sub-interface-id     |
+---------+------------------------------------+
| 19.10   | Added ECN parameters               |
+---------+------------------------------------+
