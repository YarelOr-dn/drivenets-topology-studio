show ospf route
---------------

**Minimum user role:** viewer

To displays OSPF routes, as determined by the most recent SPF calculation.



**Command syntax: show ospf** instance [ospf-instance-name] **route** table [ospf-routing-table] prefix [ipv4-prefix]

**Command mode:** operational


..
    **Internal Note**

    - use "instance [ospf-instance-name]" to display information from a specific OSPF instance, when not specified, display information from all OSPF instances

**Parameter table**

+--------------------+--------------------------------------------------------------------+------------------------------+----------------+
| Parameter          | Description                                                        | Values                       | Default value  |
+====================+====================================================================+==============================+================+
| ospf-routing-table | OSPF routing table                                                 | unicast, sr, mpls, shortcut, | all tables     |
|                    |                                                                    | color-sr                     |                |
+--------------------+--------------------------------------------------------------------+------------------------------+----------------+
| ipv4-prefix        | Display OSPF routing information for a specific prefix             | A.B.C.D/M                    | all prefixes   |
+--------------------+--------------------------------------------------------------------+------------------------------+----------------+
| ospf-instance-name | Filters the displayed routes from a specific OSPF instance         | configured instances names   | all instances  |
+--------------------+--------------------------------------------------------------------+------------------------------+----------------+
| label              | Filters the displayed routes matching a given mpls-label           | <0-1048575>                  | all labels     |
+--------------------+--------------------------------------------------------------------+------------------------------+----------------+
| color              | Filters the displayed routes that have a given color               | <0-4294967295>               | all colors     |
+--------------------+--------------------------------------------------------------------+------------------------------+----------------+
| algo               | Filters the displayed routes from a given Flex-Algo id             | <128-255>                    | all algorithms |
+--------------------+--------------------------------------------------------------------+------------------------------+----------------+

**Example**
::

    dnRouter# show ospf route
    Codes: IA - Inter area, D - Discard
           N1 - OSPF NSSA type 1, N2 - OSPF NSSA type 2
           E1 - External type 1, E2 - External type 2
           N - Node Prefix SID, A - Anycast Prefix SID
           L - Local Adjacency SID
           lp - link-protecting LFA, np - node-protecting LFA
           ul - microloop avoidance, ap - Adjacency-SID protection in use
           c:A.B.C.D/M - Color c
    Ospf Instance instance1
    ============ OSPF network unicast routing table ==================
         1.1.1.1/32            cost [41], area: 0.0.0.0
                               via 12.12.4.1, ge100-0/0/4
         2.2.2.2/32            cost [1], area: 0.0.0.0
                               directly attached to lo0
         25.1.1.0/24           cost [40], area: 0.0.0.0
                               directly attached to ge100-0/0/0.2500
         80.1.1.0/24           cost [40], area: 0.0.0.0
                               directly attached to ge100-0/0/3
         5.5.5.5/32            cost [5], area: 0.0.0.0
                               via 12.12.12.1, tunnel-te1
                               via 185.0.101.1, ge100-0/0/2.101 (lp) cost [410] alternate label 8000/16001
         6.6.6.6/32            cost [3], area: 0.0.0.0
                               via 12.12.12.1, tunnel-te1
                               via 185.0.103.1, ge100-0/0/2.103 (lp) cost [210] alternate label 8000/16003
         7.7.7.7/32            cost [4], area: 0.0.0.0
                               via 12.13.1.3 , tunnel-te2
         10.1.1.0/24           cost [3], area: 0.0.0.0
                               via 10.1.3.1, tunnel-te3
                               via 185.0.116.1, ge100-0/0/2.116 (lp) cost [210] alternate label 8000/16016
         10.1.2.0/24           cost [4], area: 0.0.0.0
                               via 10.1.3.1, tunnel-te3
    IA   205.1.192.0/24        cost [80], area: 0.0.0.0
                               via 12.12.4.2, ge100-0/0/4
    IA   205.1.193.0/24        cost [80], area: 0.0.0.0
                               via 12.12.4.2, ge100-0/0/4
    IA   205.1.194.0/24        cost [80], area: 0.0.0.0
                               via 12.12.4.2, ge100-0/0/4
    IA   205.1.195.0/24        cost [80], area: 0.0.0.0
                               via 12.12.4.2, ge100-0/0/4
    IA   205.1.196.0/24        cost [80], area: 0.0.0.0
                               via 12.12.4.2, ge100-0/0/4

    ============ OSPF router routing table ===========================
         3.3.3.3               cost [21], area: 0.0.0.0, ASBR
                               via 12.12.4.2, ge100-0/0/4
         12.122.8.21           cost [80], area: 0.0.0.0, ABR
                               via 12.12.4.2, ge100-0/0/4
         195.0.0.1             cost [80], area: 0.0.0.0, ABR, ASBR
                               via 12.12.4.2, ge100-0/0/4
         195.0.0.2             cost [80], area: 0.0.0.0, ABR, ASBR
                               via 12.12.4.2, ge100-0/0/4
         195.0.0.3             cost [80], area: 0.0.0.0, ABR, ASBR
                               via 12.12.4.2, ge100-0/0/4
         195.0.0.4             cost [80], area: 0.0.0.0, ABR, ASBR
                               via 12.12.4.2, ge100-0/0/4
         195.0.0.5             cost [80], area: 0.0.0.0, ABR, ASBR
                               via 12.12.4.2, ge100-0/0/4
         195.0.0.6             cost [80], area: 0.0.0.0, ABR, ASBR

    ============ OSPF external routing table =========================
    E2   0.0.0.0/0             cost [40/1], tag: 0
                               via 12.12.4.2, ge100-0/0/4
    E2   2.2.2.199/32          cost [40/1567], tag: 87
                               via 12.12.4.2, ge100-0/0/4
    E2   19.1.1.0/24           cost [80/1567], tag: 33
                               via 12.12.4.2, ge100-0/0/4
    E2   19.1.2.0/24           cost [40/1567], tag: 33
                               via 12.12.4.2, ge100-0/0/4
    E1   207.1.0.0/24          cost [80], tag: 0
                               via 12.12.4.2, ge100-0/0/4
    E1   207.1.1.0/24          cost [80], tag: 0
                               via 12.12.4.2, ge100-0/0/4
    E1   207.1.2.0/24          cost [80], tag: 0
                               via 12.12.4.2, ge100-0/0/4
    E1   207.1.3.0/24          cost [80], tag: 0
                               via 12.12.4.2, ge100-0/0/4
    E1   207.1.4.0/24          cost [80], tag: 0
                               via 12.12.4.2, ge100-0/0/4

    ============ OSPF network SR routing table =======================
    N    3.3.3.3/32            algo strict-spf cost [21] area: 0.0.0.0
                               via 12.1.1.2, ge100-0/0/4, egress-label 16003, ingress-label 16003, NH-srgb-base 16000
                               via 14.1.1.4, ge100-0/0/5, egress-label 16003, ingress-label 16003, NH-srgb-base 16000
    N    4.4.4.4/32            algo spf cost [11] area: 0.0.0.0
                               via 14.1.1.4, ge100-0/0/4, egress-label 3, ingress-label 16004, NH-srgb-base 16000
    N    5.5.5.5/32            algo spf cost [31] area: 0.0.0.0
                               via 12.1.1.2, ge100-0/0/4, egress-label 16005, ingress-label 16005, NH-srgb-base 16000
                               via 14.1.1.4, ge100-0/0/5, egress-label 16005, ingress-label 16005, NH-srgb-base 16000

    ============ OSPF network MPLS routing table =====================
    L    256                   12.1.1.1 cost [10] area: 0.0.0.0
                               via 12.1.1.2, ge100-0/0/4
                               via 14.1.1.4, ge100-0/0/5 cost [11] alternate label 16002
    L    257                   14.1.1.1 cost [10] area: 0.0.0.0
                               via 14.1.1.4, ge100-0/0/4
    N    16002                 2.2.2.2/32 algo spf cost [11] area: 0.0.0.0
                               via 12.1.1.2, ge100-0/0/4, egress-label 3, ingress-label 16002, NH-srgb-base 16000
    N    16003                 3.3.3.3/32 algo strict-spf cost [21] area: 0.0.0.0
                               via 12.1.1.2, ge100-0/0/4, egress-label 16003, ingress-label 16003, NH-srgb-base 16000
                               via 14.1.1.4, ge100-0/0/5, egress-label 16003, ingress-label 16003, NH-srgb-base 16000
    N    16004                 4.4.4.4/32 algo 133 cost [11] area: 0.0.0.0
                               via 14.1.1.4, ge100-0/0/5, egress-label 3, ingress-label 16004, NH-srgb-base 16000
    N    16005                 5.5.5.5/32 algo 140 cost [31] area: 0.0.0.0
                               via 12.1.1.2, ge100-0/0/4, egress-label 16005, ingress-label 16005, NH-srgb-base 16000
                               via 14.1.1.4, ge100-0/0/5, egress-label 16005, ingress-label 16005, NH-srgb-base 16000

    ============ OSPF network IPv4 shortcut routing table ============
         5.5.5.5/32            algo spf cost [11] area: 0.0.0.0
                               via 5.5.5.5, pol2
         35.1.1.0/24           algo spf cost [20] area: 0.0.0.0
                               via 5.5.5.5, pol2
         35.3.3.0/24           algo spf cost [20] area: 0.0.0.0
                               via 5.5.5.5, pol2

    ============ OSPF network MPLS shortcut routing table ============
    N    16005                 5.5.5.5/32 algo spf cost [11] area: 0.0.0.0
                               via 5.5.5.5/32, pol2

    ============ OSPF network Color-SR routing table =================
    N    30:4.4.4.4/32         algo 133 cost [11] area: 0.0.0.0
                               via 14.1.1.4, ge100-0/0/4, egress-label 3, ingress-label 17004, NH-srgb-base 16000
    N    43:5.5.5.5/32         algo 140 cost [31] area: 0.0.0.0
                               via 12.1.1.2, ge100-0/0/4, egress-label 17005, ingress-label 17005, NH-srgb-base 16000

    Ospf Instance instance2
    ============ OSPF network unicast routing table ==================
         203.1.0.0/24          cost [40], area: 0.0.0.0
                               via 185.0.101.1, ge100-0/0/2.101
                               via 185.0.103.1, ge100-0/0/2.103
                               via 185.0.107.1, ge100-0/0/2.107
                               via 185.0.115.1, ge100-0/0/2.115
                               via 185.0.131.1, ge100-0/0/2.131
                               via 185.0.132.1, ge100-0/0/2.132
                               via 185.0.116.1, ge100-0/0/2.116
                               via 185.0.130.1, ge100-0/0/2.130


    dnRouter# show ospf instance instance2 route
    Codes: IA - Inter area, D - Discard
           N1 - OSPF NSSA type 1, N2 - OSPF NSSA type 2
           E1 - External type 1, E2 - External type 2
           N - Node Prefix SID, A - Anycast Prefix SID
           L - Local Adjacency SID
           lp - link-protecting LFA, np - node-protecting LFA
           ul - microloop avoidance, ap - Adjacency-SID protection in use
           c:A.B.C.D/M - Color c
    Ospf Instance instance2
    ============ OSPF network unicast routing table ==================
         203.1.0.0/24          cost [40], area: 0.0.0.0
                               via 185.0.101.1, ge100-0/0/2.101
                               via 185.0.103.1, ge100-0/0/2.103
                               via 185.0.107.1, ge100-0/0/2.107
                               via 185.0.115.1, ge100-0/0/2.115
                               via 185.0.131.1, ge100-0/0/2.131
                               via 185.0.132.1, ge100-0/0/2.132
                               via 185.0.116.1, ge100-0/0/2.116
                               via 185.0.130.1, ge100-0/0/2.130


    dnRouter# show ospf route table sr
    Codes: IA - Inter area, D - Discard
           N1 - OSPF NSSA type 1, N2 - OSPF NSSA type 2
           E1 - External type 1, E2 - External type 2
           N - Node Prefix SID, A - Anycast Prefix SID
           L - Local Adjacency SID
           lp - link-protecting LFA, np - node-protecting LFA
           ul - microloop avoidance, ap - Adjacency-SID protection in use
           c:A.B.C.D/M - Color c
    Ospf Instance instance1
    ============ OSPF network SR routing table =======================
    N    3.3.3.3/32            algo strict-spf cost [21] area: 0.0.0.0
                               via 12.1.1.2, ge100-0/0/4, egress-label 16003, ingress-label 16003, NH-srgb-base 16000
                               via 14.1.1.4, ge100-0/0/5, egress-label 16003, ingress-label 16003, NH-srgb-base 16000
    N    4.4.4.4/32            algo spf cost [11] area: 0.0.0.0
                               via 14.1.1.4, ge100-0/0/4, egress-label 3, ingress-label 16004, NH-srgb-base 16000
    N    5.5.5.5/32            algo spf cost [31] area: 0.0.0.0
                               via 12.1.1.2, ge100-0/0/4, egress-label 16005, ingress-label 16005, NH-srgb-base 16000
                               via 14.1.1.4, ge100-0/0/5, egress-label 16005, ingress-label 16005, NH-srgb-base 16000



    dnRouter# show ospf instance instance1 route table sr
    Codes: IA - Inter area, D - Discard
           N1 - OSPF NSSA type 1, N2 - OSPF NSSA type 2
           E1 - External type 1, E2 - External type 2
           N - Node Prefix SID, A - Anycast Prefix SID
           L - Local Adjacency SID
           lp - link-protecting LFA, np - node-protecting LFA
           ul - microloop avoidance, ap - Adjacency-SID protection in use
           c:A.B.C.D/M - Color c
    Ospf Instance instance1
    ============ OSPF network SR routing table =======================
    N    3.3.3.3/32            algo strict-spf cost [21] area: 0.0.0.0
                               via 12.1.1.2, ge100-0/0/4, egress-label 16003, ingress-label 16003, NH-srgb-base 16000
                               via 14.1.1.4, ge100-0/0/5, egress-label 16003, ingress-label 16003, NH-srgb-base 16000
    N    4.4.4.4/32            algo spf cost [11] area: 0.0.0.0
                               via 14.1.1.4, ge100-0/0/4, egress-label 3, ingress-label 16004, NH-srgb-base 16000
    N    5.5.5.5/32            algo spf cost [31] area: 0.0.0.0
                               via 12.1.1.2, ge100-0/0/4, egress-label 16005, ingress-label 16005, NH-srgb-base 16000
                               via 14.1.1.4, ge100-0/0/5, egress-label 16005, ingress-label 16005, NH-srgb-base 16000



    dnRouter# show ospf instance instance1 route table mpls
    Codes: IA - Inter area, D - Discard
           N1 - OSPF NSSA type 1, N2 - OSPF NSSA type 2
           E1 - External type 1, E2 - External type 2
           N - Node Prefix SID, A - Anycast Prefix SID
           L - Local Adjacency SID
           lp - link-protecting LFA, np - node-protecting LFA
           ul - microloop avoidance, ap - Adjacency-SID protection in use
           c:A.B.C.D/M - Color c
    Ospf Instance instance1
    ============ OSPF network MPLS routing table =====================
    L    256                   12.1.1.1 cost [10] area: 0.0.0.0
                               via 12.1.1.2, ge100-0/0/4
                               via 14.1.1.4, ge100-0/0/5 cost [11] alternate label 16002
    L    257                   14.1.1.1 cost [10] area: 0.0.0.0
                               via 14.1.1.4, ge100-0/0/4
    N    16002                 2.2.2.2/32 algo spf cost [11] area: 0.0.0.0
                               via 12.1.1.2, ge100-0/0/4, egress-label 3, ingress-label 16002, NH-srgb-base 16000
    N    16003                 3.3.3.3/32 algo strict-spf cost [21] area: 0.0.0.0
                               via 12.1.1.2, ge100-0/0/4, egress-label 16003, ingress-label 16003, NH-srgb-base 16000
                               via 14.1.1.4, ge100-0/0/5, egress-label 16003, ingress-label 16003, NH-srgb-base 16000
    N    16004                 4.4.4.4/32 algo 133 cost [11] area: 0.0.0.0
                               via 14.1.1.4, ge100-0/0/5, egress-label 3, ingress-label 16004, NH-srgb-base 16000
    N    16005                 5.5.5.5/32 algo 140 cost [31] area: 0.0.0.0
                               via 12.1.1.2, ge100-0/0/4, egress-label 16005, ingress-label 16005, NH-srgb-base 16000
                               via 14.1.1.4, ge100-0/0/5, egress-label 16005, ingress-label 16005, NH-srgb-base 16000


    dnRouter# show ospf instance instance1 route table mpls label 16004
    Codes: IA - Inter area, D - Discard
           N1 - OSPF NSSA type 1, N2 - OSPF NSSA type 2
           E1 - External type 1, E2 - External type 2
           N - Node Prefix SID, A - Anycast Prefix SID
           L - Local Adjacency SID
           lp - link-protecting LFA, np - node-protecting LFA
           ul - microloop avoidance, ap - Adjacency-SID protection in use
           c:A.B.C.D/M - Color c
    Ospf Instance instance1
    ============ OSPF network MPLS routing table =====================
    N    16004                 4.4.4.4/32 algo 133 cost [11] area: 0.0.0.0
                               via 14.1.1.4, ge100-0/0/5, egress-label 3, ingress-label 16004, NH-srgb-base 16000


    dnRouter# show ospf instance instance1 route table mpls prefix 5.5.5.5/32
    Codes: IA - Inter area, D - Discard
           N1 - OSPF NSSA type 1, N2 - OSPF NSSA type 2
           E1 - External type 1, E2 - External type 2
           N - Node Prefix SID, A - Anycast Prefix SID
           L - Local Adjacency SID
           lp - link-protecting LFA, np - node-protecting LFA
           ul - microloop avoidance, ap - Adjacency-SID protection in use
           c:A.B.C.D/M - Color c
    Ospf Instance instance1
    ============ OSPF network MPLS routing table =====================
    N    16005                 5.5.5.5/32 algo 140 cost [31] area: 0.0.0.0
                               via 12.1.1.2, ge100-0/0/4, egress-label 16005, ingress-label 16005, NH-srgb-base 16000
                               via 14.1.1.4, ge100-0/0/5, egress-label 16005, ingress-label 16005, NH-srgb-base 16000


    dnRouter# show ospf route prefix 2.2.2.2/32
    Codes: IA - Inter area, D - Discard
           N1 - OSPF NSSA type 1, N2 - OSPF NSSA type 2
           E1 - External type 1, E2 - External type 2
           N - Node Prefix SID, A - Anycast Prefix SID
           L - Local Adjacency SID
           lp - link-protecting LFA, np - node-protecting LFA
           ul - microloop avoidance, ap - Adjacency-SID protection in use
           c:A.B.C.D/M - Color c
    Ospf Instance instance1
    ============ OSPF network unicast routing table ==================
         2.2.2.2/32            cost [21] area: 0.0.0.0
                               via 12.1.1.2, bundle-1
                               via 14.1.1.4, bundle-2 (np) cost [1051] alternate label 256

    ============ OSPF network SR routing table =======================
    N    2.2.2.2/32            algo spf cost [11] area: 0.0.0.0
                               via 12.1.1.2, vdev_1, egress-label 3, ingress-label 16002, NH-srgb-base 16000
                               via 14.1.1.4, vdev_2 (lp) cost [31] alternate egress-label 16003/16002, ingress-label 16002, NH-srgb-base 16000


    dnRouter# show ospf instance ospf1 route prefix 3.3.3.3/32
    Codes: IA - Inter area, D - Discard
           N1 - OSPF NSSA type 1, N2 - OSPF NSSA type 2
           E1 - External type 1, E2 - External type 2
           N - Node Prefix SID, A - Anycast Prefix SID
           L - Local Adjacency SID
           lp - link-protecting LFA, np - node-protecting LFA
           ul - microloop avoidance, ap - Adjacency-SID protection in use
           c:A.B.C.D/M - Color c
    Ospf Instance instance1
    ============ OSPF network unicast routing table ==================
         3.3.3.3/32            cost [21] area: 0.0.0.0
                               via 12.1.1.2, bundle-1
                               via 14.1.1.4, bundle-2 (np) cost [1010] alternate label 256
    
    ============ OSPF network SR routing table =======================
    N    3.3.3.3/32            cost [21] area: 0.0.0.0
                               via 12.1.1.2, bundle-1, egress-label 16003, ingress-label 16003, NH-srgb-base 16000
                               via 14.1.1.4, bundle-2, egress-label 16003, ingress-label 16003, NH-srgb-base 16000


    dnRouter# show ospf route prefix 5.5.5.5/32
    Codes: IA - Inter area, D - Discard
           N1 - OSPF NSSA type 1, N2 - OSPF NSSA type 2
           E1 - External type 1, E2 - External type 2
           N - Node Prefix SID, A - Anycast Prefix SID
           L - Local Adjacency SID
           lp - link-protecting LFA, np - node-protecting LFA
           ul - microloop avoidance, ap - Adjacency-SID protection in use
           c:A.B.C.D/M - Color c
    Ospf Instance instance1
    ============ OSPF network unicast routing table ==================
         5.5.5.5/32            cost [61] area: 0.0.0.0
                               via 10.0.14.4, bundle-14
                               via 10.0.12.2, bundle-12

    ============ OSPF network SR routing table =======================
    N    5.5.5.5/32            cost [31] area: 0.0.0.0
                               via 12.1.1.2, bundle-12, egress-label 16005, ingress-label 16005, NH-srgb-base 16000
                               via 14.1.1.4, bundle-14, egress-label 16005, ingress-label 16005, NH-srgb-base 16000

    ============ OSPF network MPLS routing table =====================
    N    16005                 5.5.5.5/32 algo 140 cost [31] area: 0.0.0.0
                               via 12.1.1.2, ge100-0/0/4, egress-label 16005, ingress-label 16005, NH-srgb-base 16000
                               via 14.1.1.4, ge100-0/0/5, egress-label 16005, ingress-label 16005, NH-srgb-base 16000

    ============ OSPF network IPv4 shortcut routing table ============
         5.5.5.5/32            algo spf cost [11] area: 0.0.0.0
                               via 5.5.5.5, pol2

    ============ OSPF network MPLS shortcut routing table ============
    N    16005                 5.5.5.5/32 algo spf cost [11] area: 0.0.0.0
                               via 5.5.5.5/32, pol2

    ============ OSPF network Color-SR routing table =================
    N    43:5.5.5.5/32         algo 140 cost [31] area: 0.0.0.0
                               via 12.1.1.2, ge100-0/0/4, egress-label 17005, ingress-label 17005, NH-srgb-base 16000


    dnRouter# show ospf route table unicast prefix 5.5.5.5/32
    Codes: IA - Inter area, D - Discard
           N1 - OSPF NSSA type 1, N2 - OSPF NSSA type 2
           E1 - External type 1, E2 - External type 2
           N - Node Prefix SID, A - Anycast Prefix SID
           L - Local Adjacency SID
           lp - link-protecting LFA, np - node-protecting LFA
           ul - microloop avoidance, ap - Adjacency-SID protection in use
           c:A.B.C.D/M - Color c
    Ospf Instance instance1
    ============ OSPF network unicast routing table ==================
         5.5.5.5/32            cost [5], area: 0.0.0.0
                               via 12.12.12.1, tunnel-te1
                               via 185.0.101.1, ge100-0/0/2.101 (lp) cost [410] alternate label 8000/16001


    dnRouter# show ospf route table shortcut
    Codes: IA - Inter area, D - Discard
           N1 - OSPF NSSA type 1, N2 - OSPF NSSA type 2
           E1 - External type 1, E2 - External type 2
           N - Node Prefix SID, A - Anycast Prefix SID
           L - Local Adjacency SID
           lp - link-protecting LFA, np - node-protecting LFA
           ul - microloop avoidance, ap - Adjacency-SID protection in use
           c:A.B.C.D/M - Color c
    Ospf Instance instance1
    ============ OSPF network IPv4 shortcut routing table ============
         5.5.5.5/32            algo spf cost [11] area: 0.0.0.0
                               via 5.5.5.5, pol2
         35.1.1.0/24           algo spf cost [20] area: 0.0.0.0
                               via 5.5.5.5, pol2
         35.3.3.0/24           algo spf cost [20] area: 0.0.0.0
                               via 5.5.5.5, pol2

    ============ OSPF network MPLS shortcut routing table ============
    N    16005                 5.5.5.5/32 algo spf cost [11] area: 0.0.0.0
                               via 5.5.5.5/32, pol2


    dnRouter# show ospf route table color-sr
    Codes: IA - Inter area, D - Discard
           N1 - OSPF NSSA type 1, N2 - OSPF NSSA type 2
           E1 - External type 1, E2 - External type 2
           N - Node Prefix SID, A - Anycast Prefix SID
           L - Local Adjacency SID
           lp - link-protecting LFA, np - node-protecting LFA
           ul - microloop avoidance, ap - Adjacency-SID protection in use
           c:A.B.C.D/M - Color c
    ============ OSPF network Color-SR routing table =================
    N    30:4.4.4.4/32         algo 133 cost [11] area: 0.0.0.0
                               via 14.1.1.4, ge100-0/0/4, egress-label 3, ingress-label 17004, NH-srgb-base 16000
    N    43:5.5.5.5/32         algo 140 cost [31] area: 0.0.0.0
                               via 12.1.1.2, ge100-0/0/4, egress-label 16005, ingress-label 17005, NH-srgb-base 16000


    dnRouter# show ospf route table color-sr prefix 5.5.5.5/32
    Codes: IA - Inter area, D - Discard
           N1 - OSPF NSSA type 1, N2 - OSPF NSSA type 2
           E1 - External type 1, E2 - External type 2
           N - Node Prefix SID, A - Anycast Prefix SID
           L - Local Adjacency SID
           lp - link-protecting LFA, np - node-protecting LFA
           ul - microloop avoidance, ap - Adjacency-SID protection in use
           c:A.B.C.D/M - Color c
    ============ OSPF network Color-SR routing table =================
    N    43:5.5.5.5/32         algo 140 cost [31] area: 0.0.0.0
                               via 12.1.1.2, ge100-0/0/4, egress-label 17005, ingress-label 17005, NH-srgb-base 16000


    dnRouter# show ospf route table mpls label 256
    Codes: IA - Inter area, D - Discard
           N1 - OSPF NSSA type 1, N2 - OSPF NSSA type 2
           E1 - External type 1, E2 - External type 2
           N - Node Prefix SID, A - Anycast Prefix SID
           L - Local Adjacency SID
           lp - link-protecting LFA, np - node-protecting LFA
           ul - microloop avoidance, ap - Adjacency-SID protection in use
           c:A.B.C.D/M - Color c
    ============ OSPF network MPLS routing table =====================
    L    256                   12.1.1.1 cost [1021] area: 0.0.0.0
                               via 14.1.1.4, vdev_2 (ap) (ul) label 16003/258


    dnRouter# show ospf route table mpls label 256
    Codes: IA - Inter area, D - Discard
           N1 - OSPF NSSA type 1, N2 - OSPF NSSA type 2
           E1 - External type 1, E2 - External type 2
           N - Node Prefix SID, A - Anycast Prefix SID
           L - Local Adjacency SID
           lp - link-protecting LFA, np - node-protecting LFA
           ul - microloop avoidance, ap - Adjacency-SID protection in use
           c:A.B.C.D/M - Color c
    ============ OSPF network MPLS routing table =====================
    L    256                   12.1.1.1 cost [1021] area: 0.0.0.0
                               via 14.1.1.4, vdev_2 (ap) label 16002

.. **Help line:** Displays the OSPF route information

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 11.6    | Command introduced                 |
+---------+------------------------------------+
| 16.2    | Removed fast-reroute option        |
+---------+------------------------------------+
| 17.0    | Extend support for segment-routing |
+---------+------------------------------------+
| 18.2    | Added ti-LFA                       |
+---------+------------------------------------+
| 18.2    | Added instance parameter           |
+---------+------------------------------------+
| 18.2    | Added microloop avoidance          |
+---------+------------------------------------+
| 18.2    | Added shortcut tables command      |
+---------+------------------------------------+
| 19.1    | Added MPLS / Color-SR tables       |
+---------+------------------------------------+
