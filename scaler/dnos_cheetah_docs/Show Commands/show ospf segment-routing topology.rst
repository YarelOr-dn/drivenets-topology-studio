show ospf segment-routing topology
----------------------------------

**Minimum user role:** viewer

To display OSPF topology constructed from Segment-Routing speaking nodes only:



**Command syntax: show ospf** instance [ospf-instance-name] **segment-routing** { flex-algo [flex-algo-id] } **topology** { router-id [router-id] | prefix [ipv4-prefix] }

**Command mode:** operational


..
    **Internal Note**

    - use "instance [ospf-instance-name]" to display information from a specific OSPF instance, when not specified, display information from all OSPF instances

**Parameter table**

+--------------------+--------------------------------------------------------------------+------------------------------+----------------+
| Parameter          | Description                                                        | Values                       | Default value  |
+====================+====================================================================+==============================+================+
| ospf-instance-name | Filters the displayed information to a specific OSPF instance      | Configure instances names    | all            |
+--------------------+--------------------------------------------------------------------+------------------------------+----------------+
| flex-algo          | Displays topology of the requested <flex-algo id>                  | FAD                          | all algorithms |
+--------------------+---------------------------------------------------------------------------------------------------+----------------+
| router-id          | Display a node information matching the required router-id         | A.B.C.D                      |                |
+--------------------+--------------------------------------------------------------------+------------------------------+----------------+
| ipv4-prefix        | Display a node information that holds the required prefix          | A.B.C.D/M                    |                |
+--------------------+--------------------------------------------------------------------+------------------------------+----------------+



**Example**
::

        dnRouter# show ospf segment-routing topology

        OSPF Segment Routing topology for Router ID 3.3.3.3
          Area 0.0.0.0:
            SR-Node: 5.5.5.5
              SRGB: 16000/23999
              SRLB: 8000/15999
              Algorithm(s): SPF S-SPF
              MSD: 9
              Prefix-SIDs:
                5.5.5.5 | 5 | node
              Adjacency-SIDs:
                3.3.3.3 | 35.1.1.5 35.1.1.3 | 8000

            SR-Node: 3.3.3.3
              SRGB: 16000/23999
              SRLB: 8000/15999
              Algorithm(s): SPF S-SPF
              MSD: 9
              Prefix-SIDs:
                3.3.3.3 | 3 | node
              Adjacency-SIDs:
                2.2.2.2 | 23.1.1.3 23.1.1.2 | 8000
                4.4.4.4 | 34.1.1.3 34.1.1.4 | 8001
                5.5.5.5 | 35.1.1.3 35.1.1.5 | 8002

            SR-Node: 4.4.4.4
              SRGB: 16000/23999
              SRLB: 8000/15999
              Algorithm(s): SPF S-SPF
              MSD: 9
              Prefix-SIDs:
                4.4.4.4 | 4 | node
              Adjacency-SIDs:
                1.1.1.1 | 14.1.1.4 14.1.1.1 | 8000
                3.3.3.3 | 34.1.1.4 34.1.1.3 | 8001

            SR-Node: 2.2.2.2
              SRGB: 16000/23999
              SRLB: 8000/15999
              Algorithm(s): SPF S-SPF
              MSD: 9
              Prefix-SIDs:
                2.2.2.2 | 2 | node
                8.8.8.8 | 100 | anycast
              Adjacency-SIDs:
                1.1.1.1 | 12.1.1.2 12.1.1.1 | 8000
                3.3.3.3 | 23.1.1.2 23.1.1.3 | 8001

            SR-Node: 1.1.1.1
              SRGB: 16000/23999
              SRLB: 8000/15999
              Algorithm(s): SPF S-SPF
              MSD: 9
              Prefix-SIDs:
                1.1.1.1 | 1 | node
              Adjacency-SIDs:
                2.2.2.2 | 12.1.1.1 12.1.1.2 | 8000
                4.4.4.4 | 14.1.1.1 14.1.1.4 | 8001


        dnRouter# show ospf instance ospf-1 segment-routing topology

        Ospf Instance ospf-1
        OSPF Segment Routing topology for Router ID 1.1.1.1
          Area 0.0.0.0:
            SR-Node: 6.6.6.6
              SRGB: 16000/23999
              SRLB: 8000/15999
              Algorithm(s): SPF S-SPF
              MSD: 9
              Prefix-SIDs:
                6.6.6.6 | 6 | node
              Adjacency-SIDs:
                2.2.2.2 | 26.0.0.2 26.0.0.1 | 8000
                4.4.4.4 | 46.0.0.2 46.0.0.1 | 8001

            SR-Node: 4.4.4.4
              SRGB: 16000/23999
              SRLB: 8000/15999
              Algorithm(s): SPF S-SPF
              MSD: 9
              Prefix-SIDs:
                4.4.4.4 | 4 | node
              Adjacency-SIDs:
                1.1.1.1 | 14.0.0.2 14.0.0.1 | 8000
                6.6.6.6 | 46.0.0.1 46.0.0.2 | 8001

            SR-Node: 2.2.2.2
              SRGB: 16000/23999
              SRLB: 8000/15999
              Algorithm(s): SPF S-SPF
              MSD: 9
              Prefix-SIDs:
                22.22.22.22 | 22 | node
                2.2.2.2 | 2 | node
                3.3.3.3 | 3 | node | no-php
                5.5.5.5 | 5 | node | no-php
              Adjacency-SIDs:
                6.6.6.6 | 26.0.0.1 26.0.0.2 | 8000

            SR-Node: 1.1.1.1
              SRGB: 16000/23999
              SRLB: 8000/15999
              Algorithm(s): SPF S-SPF
              MSD: 9
              Prefix-SIDs:
                1.1.1.1 | 1 | node
                111.111.111.111 | 111 | as-external
                121.121.121.121 | 121 | nssa-external
              Adjacency-SIDs:
                4.4.4.4 | 14.0.0.1 14.0.0.2 | 8000

          Area 1.1.1.1:
            SR-Node: 5.5.5.5
              SRGB: 16000/23999
              SRLB: 8000/15999
              Algorithm(s): SPF S-SPF
              MSD: 9
              Prefix-SIDs:
                5.5.5.5 | 5 | node
              Adjacency-SIDs:
                2.2.2.2 | 25.0.0.2 25.0.0.1 | 8000
                3.3.3.3 | 35.0.0.2 35.0.0.1 | 8001

            SR-Node: 3.3.3.3
              SRGB: 16000/23999
              SRLB: 8000/15999
              Algorithm(s): SPF S-SPF
              MSD: 9
              Prefix-SIDs:
                3.3.3.3 | 3 | node
              Adjacency-SIDs:
                1.1.1.1 | 13.0.0.2 13.0.0.1 | 8000
                5.5.5.5 | 35.0.0.1 35.0.0.2 | 8001

            SR-Node: 2.2.2.2
              SRGB: 16000/23999
              SRLB: 8000/15999
              Algorithm(s): SPF S-SPF
              MSD: 9
              Prefix-SIDs:
                2.2.2.2 | 2 | node
                22.22.22.22 | 22 | node
                6.6.6.6 | 6 | node | no-php | inter-area
                4.4.4.4 | 4 | node | no-php
              Adjacency-SIDs:
                5.5.5.5 | 25.0.0.1 25.0.0.2 | 8001

            SR-Node: 1.1.1.1
              SRGB: 16000/23999
              SRLB: 8000/15999
              Algorithm(s): SPF S-SPF
              MSD: 9
              Prefix-SIDs:
                11.11.11.11 | 11 | node
              Adjacency-SIDs:
                3.3.3.3 | 13.0.0.1 13.0.0.2 | 8001


        dnRouter# show ospf segment-routing topology router-id 1.1.1.1

        Ospf Instance ospf-1
        OSPF Segment Routing topology for Router ID 3.3.3.3
          Area 0.0.0.0:
            SR-Node: 1.1.1.1
              SRGB: 16000/23999
              SRLB: 8000/15999
              Algorithm(s): SPF S-SPF
              MSD: 9
              Prefix-SIDs:
                1.1.1.1 | 1 | node
              Adjacency-SIDs:
                2.2.2.2 | 12.1.1.1 12.1.1.2 | 8000
                4.4.4.4 | 14.1.1.1 14.1.1.4 | 8001


        dnRouter# show ospf instance ospf-1 segment-routing topology router-id 1.1.1.1

        Ospf Instance ospf-1
        OSPF Segment Routing topology for Router ID 3.3.3.3
          Area 0.0.0.0:
            SR-Node: 1.1.1.1
              SRGB: 16000/23999
              SRLB: 8000/15999
              Algorithm(s): SPF S-SPF
              MSD: 9
              Prefix-SIDs:
                1.1.1.1 | 1 | node
              Adjacency-SIDs:
                2.2.2.2 | 12.1.1.1 12.1.1.2 | 8000
                4.4.4.4 | 14.1.1.1 14.1.1.4 | 8001


        dnRouter# show ospf segment-routing topology prefix 1.1.1.1/32

        Ospf Instance ospf-1
        OSPF Segment Routing topology for Router ID 3.3.3.3
          Area 0.0.0.0:
            SR-Node: 1.1.1.1
              SRGB: 16000/23999
              SRLB: 8000/15999
              Algorithm(s): SPF S-SPF
              MSD: 9
              Prefix-SIDs:
                1.1.1.1 | 1 | node
              Adjacency-SIDs:
                2.2.2.2 | 12.1.1.1 12.1.1.2 | 8000
                4.4.4.4 | 14.1.1.1 14.1.1.4 | 8001


        dnRouter# show ospf instance ospf-1 segment-routing topology prefix 1.1.1.1/32

        Ospf Instance ospf-1
        OSPF Segment Routing topology for Router ID 3.3.3.3
          Area 0.0.0.0:
            SR-Node: 1.1.1.1
              SRGB: 16000/23999
              SRLB: 8000/15999
              Algorithm(s): SPF S-SPF
              MSD: 9
              Prefix-SIDs:
                1.1.1.1 | 1 | node
              Adjacency-SIDs:
                2.2.2.2 | 12.1.1.1 12.1.1.2 | 8000
                4.4.4.4 | 14.1.1.1 14.1.1.4 | 8001


        dnRouter# show ospf segment-routing flex-algo topology 130
        Ospf Instance OSPF-1
        Algorithm 130
        Area 0.0.0.0:
          SR-Node: 1.1.1.1
            SRGB: 16000/23999
            SRLB: 8000/15999
            Algorithm(s): SPF S-SPF 130
            MSD: 9
            Prefix-SIDs:
              1.1.1.1 | 330 | node
            Adjacency-SIDs:
              2.2.2.2 | [metric igp 10] 12.1.1.1 12.1.1.2 | 256
              2.2.2.2 | [metric igp 10] 12.1.1.1 12.1.1.2 | 257

          SR-Node: 2.2.2.2
            SRGB: 16000/23999
            SRLB: 8000/15999
            Algorithm(s): SPF S-SPF 130
            MSD: 9
            Prefix-SIDs:
              2.2.2.2 | 331 | node
            Adjacency-SIDs:
              1.1.1.1 | [metric igp 10] 12.1.1.2 12.1.1.1 | 256

        dnRouter# show ospf segment-routing flex-algo topology 130 router-id 2.2.2.2
        Ospf Instance OSPF-1
        Algorithm 130
        Area 0.0.0.0:
          SR-Node: 2.2.2.2
            SRGB: 16000/23999
            SRLB: 8000/15999
            Algorithm(s): SPF S-SPF 130
            MSD: 9
            Prefix-SIDs:
              2.2.2.2 | 331 | node
            Adjacency-SIDs:
              1.1.1.1 | [metric igp 10] 12.1.1.2 12.1.1.1 | 256


        dnRouter# sh ip ospf segment-routing flex-algo 131 topology
        Ospf Instance OSPF-1
        Algorithm 131
        Area 0.0.0.0
          SR-Node: 1.1.1.1
            SRGB: 16000/23999
            SRLB: 8000/15999
            Algorithm(s): 131 132
            MSD: 9
            Prefix-SIDs:
              1.1.1.1 | 1001 node
            Adjacency-SIDs:
              2.2.2.2 | [metric te 10] 12.1.1.1 12.1.1.2 | 256

          SR-Node: 2.2.2.2
            SRGB: 16000/23999
            SRLB: 8000/15999
            Algorithm(s): 131
            MSD: 9
            Prefix-SIDs:
              2.2.2.2 | 1002 node
            Adjacency-SIDs:
              3.3.3.3 | [metric te 10] 23.1.1.2 23.1.1.3 | 258



.. **Help line:** Displays the OSPF Segment-Routing topology


**Command History**

+---------+----------------------------+
| Release | Modification               |
+=========+============================+
| v17.0   | Command introduced         |
+---------+----------------------------+
| 18.2    | Added instance parameter   |
+---------+----------------------------+
| 19.1    | Added flex-algo            |
+---------+----------------------------+
