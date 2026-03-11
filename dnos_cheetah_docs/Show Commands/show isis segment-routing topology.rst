show isis segment-routing topology
----------------------------------

**Minimum user role:** viewer

To display the IS-IS connectivity topology:

**Command syntax: show isis** instance [isis-instance-name] **segment-routing** flex-algo [flex-algo-id] **topology** {level [level] \| ipv4-unicast \| ipv6-unicast \| [ipv4-prefix] \| [ipv6-prefix]}

**Command mode:** operational

.. **Note**

	- use "instance [isis-instance-name]" to display information from a specific ISIS instance, when not specified, display information from all isis instances

**Parameter table**

+--------------------+--------------------------------------------------------------------------------------------------------------------------+
| Parameter          | Description                                                                                                              |
+====================+==========================================================================================================================+
| isis-instance-name | Filters the displayed information to the specified instance                                                              |
+--------------------+--------------------------------------------------------------------------------------------------------------------------+
| topology           | Displays the IS-IS connectivity topology, including segment-routing IPv4 and IPv6 SID information per node and adjacency |
+--------------------+--------------------------------------------------------------------------------------------------------------------------+
| level              | Displays routes from a specific level. If not defined, will display topology for all levels                              |
+--------------------+--------------------------------------------------------------------------------------------------------------------------+
| flex-algo          | Displays topology of the requested <flex-algo id>. If not defined, will display topology for all algorithms              |
+--------------------+--------------------------------------------------------------------------------------------------------------------------+
| ipv4-unicast       | Displays only IPv4 unicast routes, If not defined, will display topology for all address families                        |
+--------------------+--------------------------------------------------------------------------------------------------------------------------+
| ipv6-unicast       | Displays only IPv6 unicast routes, If not defined, will display topology for all address families                        |
+--------------------+--------------------------------------------------------------------------------------------------------------------------+
| ipv4-prefix        | Displays the routes for the specified IPv4 prefix (displays IPv4 route table)                                            |
+--------------------+--------------------------------------------------------------------------------------------------------------------------+
| ipv6-prefix        | Displays the routes for the specified IPv6 prefix (displays IPv6 route table)                                            |
+--------------------+--------------------------------------------------------------------------------------------------------------------------+

**Example**
::

    e2e_R1_1# show isis segment-routing topology
    instance one
    Level 1 IPv4-Unicast:

    Level 2 IPv4-Unicast:

    e2e_R3_1:3333.3333.3333 - 3.3.3.3
      SRGB = 16000-19999
      Prefix-SIDs:
      3.3.3.3/32 - 3 node
      3.3.3.3/32 (S) - 203 node
      Adjacency-SIDs:
      e2e_R1_1:1111.1111.1111 | 10.0.13.3 10.0.13.1 | 8002
      e2e_R2_1:2222.2222.2222 | 10.0.23.3 10.0.23.2 | 8001

    e2e_R2_1:2222.2222.2222 - 2.2.2.2
      SRGB = 16000-19999
      Prefix-SIDs:
      2.2.2.2/32 - 2 node
      1.0.0.1/32 - 101 no-php explicit-null
      2.2.2.2/32 (S) - 202 node
      1.0.0.1/32 (S) - 301 no-php explicit-null
      Adjacency-SIDs:
      e2e_R1_1:1111.1111.1111 | 10.0.12.2 10.0.12.1 | 8001
      e2e_R3_1:3333.3333.3333 | 10.0.23.2 10.0.23.3 | 8000

    e2e_R1_1:1111.1111.1111 - 1.1.1.1
      SRGB = 16000-19999
      Prefix-SIDs:
      1.1.1.1/32 - 1 node
      1.1.1.1/32 (S) - 201 node
      Adjacency-SIDs:
      e2e_R2_1:2222.2222.2222 | 10.0.12.1 10.0.12.2 | 8001
      e2e_R3_1:3333.3333.3333 | 10.0.13.1 10.0.13.3 | 8000

    Level 1 IPv6-Unicast:

    Level 2 IPv6-Unicast:

    e2e_R3_1:3333.3333.3333 - 3.3.3.3
      SRGB = 16000-19999
      Prefix-SIDs:
      3333::1111/128 - 13 node
      3333::1111/128 (S) - 213 node

    e2e_R2_1:2222.2222.2222 - 2.2.2.2
      SRGB = 16000-19999
      Prefix-SIDs:
      2222::1111/128 - 12 node
      2222::2222/128 - 111 no-php explicit-null
      2222::1111/128 (S) - 212 node
      2222::2222/128 (S) - 311 no-php explicit-null

    e2e_R1_1:1111.1111.1111 - 1.1.1.1
      SRGB = 16000-19999
      Prefix-SIDs:
      1111::1111/128 - 11 node
      1111::1111/128 (S) - 211 node


    e2e_R1_1# show isis segment-routing flex-algo 130 topology
    Instance one
    Level 1 IPv4-Unicast:
      Algorithm 130

    Level 2 IPv4-Unicast:
      Algorithm 130
    e2e_R1_1 - 1111.1111.1111
      [10] (8003) 10.0.12.1 -> 10.0.12.2 : e2e_R2_1
      [100] (8002) 10.0.13.1 -> 10.0.13.3 : e2e_R3_1
      [10] (8001) 10.0.16.1 -> 10.0.16.6 : e2e_R6_1
      [10] (8000) 10.1.16.1 -> 10.1.16.6 : e2e_R6_1
    e2e_R2_1 - 2222.2222.2222
      [10] (8002) 10.0.12.2 -> 10.0.12.1 : e2e_R1_1
      [10] (8001) 10.0.23.2 -> 10.0.23.3 : e2e_R3_1
      [10] (8000) 10.0.24.2 -> 10.0.24.4 : e2e_R4_1
    e2e_R3_1 - 3333.3333.3333
      [10] (8003) 10.0.13.3 -> 10.0.13.1 : e2e_R1_1
      [10] (8002) 10.0.23.3 -> 10.0.23.2 : e2e_R2_1
      [10] (8001) 10.0.34.3 -> 10.0.34.4 : e2e_R4_1
      [10] (8000) 10.0.35.3 -> 10.0.35.5 : e2e_R5_1
    e2e_R4_1 - 4444.4444.4444
      [10] (8002) 10.0.24.4 -> 10.0.24.2 : e2e_R2_1
      [10] (8001) 10.0.34.4 -> 10.0.34.3 : e2e_R3_1
      [10] (8000) 10.0.45.4 -> 10.0.45.5 : e2e_R5_1
      [10] (8003) 10.0.47.4 -> 10.0.47.7 : e2e_R7_1
    e2e_R5_1 - 5555.5555.5555
      [10] (8003) 10.0.35.5 -> 10.0.35.3 : e2e_R3_1
      [10] (8002) 10.0.45.5 -> 10.0.45.4 : e2e_R4_1
      [10] (8001) 10.0.57.5 -> 10.0.57.7 : e2e_R7_1
      [10] (8000) 10.0.58.5 -> 10.0.58.8 : e2e_R8_1
    e2e_R6_1 - 6666.6666.6666
      [10] (8001) 10.0.16.6 -> 10.0.16.1 : e2e_R1_1
      [10] (8000) 10.1.16.6 -> 10.1.16.1 : e2e_R1_1
    e2e_R7_1 - 7777.7777.7777
      [10] (8002) 10.0.47.7 -> 10.0.47.4 : e2e_R4_1
      [10] (8000) 10.0.57.7 -> 10.0.57.5 : e2e_R5_1
      [10] (8001) 10.0.78.7 -> 10.0.78.8 : e2e_R8_1
    e2e_R8_1 - 8888.8888.8888
      [10] (8000) 10.0.58.8 -> 10.0.58.5 : e2e_R5_1
      [10] (8001) 10.0.78.8 -> 10.0.78.7 : e2e_R7_1


    e2e_R1_1# show isis segment-routing topology ipv4-unicast
        instance one
        Level 1 IPv4-Unicast:

        Level 2 IPv4-Unicast:

        e2e_R3_1:3333.3333.3333 - 3.3.3.3
          SRGB = 16000-19999
          Prefix-SIDs:
          3.3.3.3/32 - 3 node
          3.3.3.3/32 (S) - 203 node
          Adjacency-SIDs:
          e2e_R1_1:1111.1111.1111 | 10.0.13.3 10.0.13.1 | 8002
          e2e_R2_1:2222.2222.2222 | 10.0.23.3 10.0.23.2 | 8001

        e2e_R2_1:2222.2222.2222 - 2.2.2.2
          SRGB = 16000-19999
          Prefix-SIDs:
          2.2.2.2/32 - 2 node
          1.0.0.1/32 - 101 no-php explicit-null
          2.2.2.2/32 (S) - 202 node
          1.0.0.1/32 (S) - 301 no-php explicit-null
          Adjacency-SIDs:
          e2e_R1_1:1111.1111.1111 | 10.0.12.2 10.0.12.1 | 8001
          e2e_R3_1:3333.3333.3333 | 10.0.23.2 10.0.23.3 | 8000

        e2e_R1_1:1111.1111.1111 - 1.1.1.1
          SRGB = 16000-19999
          Prefix-SIDs:
          1.1.1.1/32 - 1 node
          1.1.1.1/32 (S) - 201 node
          Adjacency-SIDs:
          e2e_R2_1:2222.2222.2222 | 10.0.12.1 10.0.12.2 | 8001
          e2e_R3_1:3333.3333.3333 | 10.0.13.1 10.0.13.3 | 8000


    e2e_R1_1# show isis segment-routing topology ipv4-unicast
        instance one
        Level 1 IPv4-Unicast:

        Level 2 IPv4-Unicast:

        e2e_R3_1:3333.3333.3333 - 3.3.3.3
          SRGB = 16000-19999
          Prefix-SIDs:
          3.3.3.3/32 - 3 node
          3.3.3.3/32 (S) - 203 node
          Adjacency-SIDs:
          e2e_R1_1:1111.1111.1111 | 10.0.13.3 10.0.13.1 | 8002
          e2e_R2_1:2222.2222.2222 | 10.0.23.3 10.0.23.2 | 8001

        e2e_R2_1:2222.2222.2222 - 2.2.2.2
          SRGB = 16000-19999
          Prefix-SIDs:
          2.2.2.2/32 - 2 node
          1.0.0.1/32 - 101 no-php explicit-null
          2.2.2.2/32 (S) - 202 node
          1.0.0.1/32 (S) - 301 no-php explicit-null
          Adjacency-SIDs:
          e2e_R1_1:1111.1111.1111 | 10.0.12.2 10.0.12.1 | 8001
          e2e_R3_1:3333.3333.3333 | 10.0.23.2 10.0.23.3 | 8000

        e2e_R1_1:1111.1111.1111 - 1.1.1.1
          SRGB = 16000-19999
          Prefix-SIDs:
          1.1.1.1/32 - 1 node
          1.1.1.1/32 (S) - 201 node
          Adjacency-SIDs:
          e2e_R2_1:2222.2222.2222 | 10.0.12.1 10.0.12.2 | 8001
          e2e_R3_1:3333.3333.3333 | 10.0.13.1 10.0.13.3 | 8000


    e2e_R1_1# show isis segment-routing flex-algo topology 6666::6666/128
    Instance one
    Ipv6 Level 1:
      Algorithm 130

      Algorithm 140


    Ipv6 Level 2:
      Algorithm 130
      e2e_R6_1:6666.6666.6666 - 6.6.6.6
        SRGB = 16000-19999
        Prefix-SIDs:
        6666::6666/128 - 2306 node
        Adjacency-SIDs:
        e2e_R1_1:1111.1111.1111 | [10] 11:16::6 10:16::1 | 8003


      Algorithm 140
      e2e_R6_1:6666.6666.6666 - 6.6.6.6
        SRGB = 16000-19999
        Prefix-SIDs:
        6666::6666/128 - 2406 node
        Adjacency-SIDs:
        e2e_R1_1:1111.1111.1111 | [10] 11:16::6 10:16::1 | 8003

.. **Help line:**

**Command History**

+---------+-----------------------------------------------------------+
| Release | Modification                                              |
+=========+===========================================================+
| 14.0    | Command introduced                                        |
+---------+-----------------------------------------------------------+
| 15.1    | Added support for displaying routes from a specific level |
+---------+-----------------------------------------------------------+
| 16.1    | Added support for IPv4 and IPv6 prefix SIDs               |
+---------+-----------------------------------------------------------+
| 18.1    | Added support for flex-algo topology                      |
+---------+-----------------------------------------------------------+
| 18.1    | Added support for ipv4-unicast and ipv6-unicast           |
+---------+-----------------------------------------------------------+
| 18.2    | Added support for Flex-Algo topology                      |
+---------+-----------------------------------------------------------+
