show dnos-internal routing isis segment-routing uloop topology
--------------------------------------------------------------

**Minimum user role:** viewer

To display isis segment-routing micro-loop internal topology:

**Command syntax: show dnos-internal routing isis segment-routing uloop topology** {level-1 \| level-2}

**Command mode:** operation

**Parameter table**

+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                   |                                                                                                                                                               |
| Parameter         | Description                                                                                                                                                   |
+===================+===============================================================================================================================================================+
|                   |                                                                                                                                                               |
| level-1           | Displays ISIS level-1 Segment-Routing micro-loop internal topology.                                                                                           |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                   |                                                                                                                                                               |
| level-2           | Displays ISIS level-2 Segment-Routing micro-loop internal topology.                                                                                           |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

    dnRouter# show isis segment-routing uloop topology
    instance one
    Ipv4 level-1:
    Nodes (0):

    Links (0):

    Ipv4 level-2:
    Nodes (6):

    6666.6666.6666
    srgb: Base:16000 Range:4000 mt: 1
    6.6.6.6/32
    6 spf node
    206 strict-spf node

    5555.5555.5555
    srgb: Base:16000 Range:4000 mt: 1
    5.5.5.5/32
    5 spf node
    205 strict-spf node

    4444.4444.4444
    srgb: Base:16000 Range:4000 mt: 1
    1.0.0.1/32
    101 spf
    4.4.4.4/32
    4 spf node
    204 strict-spf node

    2222.2222.2222
    srgb: Base:16000 Range:4000 mt: 1
    1.0.0.1/32
    101 spf
    301 strict-spf
    2.2.2.2/32
    2 spf node
    202 strict-spf node

    1111.1111.1111
    srgb: Base:16000 Range:4000 mt: 1
    1.1.1.1/32
    1 spf node
    201 strict-spf node

    3333.3333.3333
    srgb: Base:16000 Range:4000 mt: 1
    3.3.3.3/32
    3 spf node
    203 strict-spf node

    Links (6):

    3333.3333.3333 -> 5555.5555.5555 [10.0.35.3 -> 10.0.35.5]
    metric 10 sids: 8001 ipv4;

    5555.5555.5555 -> 6666.6666.6666 [10.0.56.5 -> 10.0.56.6]
    metric 10 sids: 8000 ipv4;

    5555.5555.5555 -> 3333.3333.3333 [10.0.35.5 -> 10.0.35.3]
    metric 10 sids: 8002 ipv4;

    6666.6666.6666 -> 5555.5555.5555 [10.0.56.6 -> 10.0.56.5]
    metric 10 sids: 8000 ipv4;

    5555.5555.5555 -> 4444.4444.4444 [10.0.45.5 -> 10.0.45.4]
    metric 50 sids: 8001 ipv4;

    2222.2222.2222 -> 3333.3333.3333 [10.0.23.2 -> 10.0.23.3]
    metric 10 sids: 8000 ipv4;

    1111.1111.1111 -> 4444.4444.4444 [10.0.14.1 -> 10.0.14.4]
    metric 10 sids: 8000 ipv4;

    2222.2222.2222 -> 1111.1111.1111 [10.0.12.2 -> 10.0.12.1]
    metric 10 sids: 8001 ipv4;

    1111.1111.1111 -> 2222.2222.2222 [10.0.12.1 -> 10.0.12.2]
    metric 10 sids: 8001 ipv4;

    4444.4444.4444 -> 5555.5555.5555 [10.0.45.4 -> 10.0.45.5]
    metric 50 sids: 8000 ipv4;

    4444.4444.4444 -> 1111.1111.1111 [10.0.14.4 -> 10.0.14.1]
    metric 10 sids: 8001 ipv4;

    3333.3333.3333 -> 2222.2222.2222 [10.0.23.3 -> 10.0.23.2]
    metric 10 sids: 8000 ipv4;

    dnRouter# show isis segment-routing uloop topology level-2
    instance one
    Ipv4 level-2:
    Nodes (6):

    6666.6666.6666
    srgb: Base:16000 Range:4000 mt: 1
    6.6.6.6/32
    6 spf node
    206 strict-spf node

    5555.5555.5555
    srgb: Base:16000 Range:4000 mt: 1
    5.5.5.5/32
    5 spf node
    205 strict-spf node

    4444.4444.4444
    srgb: Base:16000 Range:4000 mt: 1
    1.0.0.1/32
    101 spf
    4.4.4.4/32
    4 spf node
    204 strict-spf node

    2222.2222.2222
    srgb: Base:16000 Range:4000 mt: 1
    1.0.0.1/32
    101 spf
    301 strict-spf
    2.2.2.2/32
    2 spf node
    202 strict-spf node

    1111.1111.1111
    srgb: Base:16000 Range:4000 mt: 1
    1.1.1.1/32
    1 spf node
    201 strict-spf node

    3333.3333.3333
    srgb: Base:16000 Range:4000 mt: 1
    3.3.3.3/32
    3 spf node
    203 strict-spf node

    Links (6):

    3333.3333.3333 -> 5555.5555.5555 [10.0.35.3 -> 10.0.35.5]
    metric 10 sids: 8001 ipv4;

    5555.5555.5555 -> 6666.6666.6666 [10.0.56.5 -> 10.0.56.6]
    metric 10 sids: 8000 ipv4;

    5555.5555.5555 -> 3333.3333.3333 [10.0.35.5 -> 10.0.35.3]
    metric 10 sids: 8002 ipv4;

    6666.6666.6666 -> 5555.5555.5555 [10.0.56.6 -> 10.0.56.5]
    metric 10 sids: 8000 ipv4;

    5555.5555.5555 -> 4444.4444.4444 [10.0.45.5 -> 10.0.45.4]
    metric 50 sids: 8001 ipv4;

    2222.2222.2222 -> 3333.3333.3333 [10.0.23.2 -> 10.0.23.3]
    metric 10 sids: 8000 ipv4;

    1111.1111.1111 -> 4444.4444.4444 [10.0.14.1 -> 10.0.14.4]
    metric 10 sids: 8000 ipv4;

    2222.2222.2222 -> 1111.1111.1111 [10.0.12.2 -> 10.0.12.1]
    metric 10 sids: 8001 ipv4;

    1111.1111.1111 -> 2222.2222.2222 [10.0.12.1 -> 10.0.12.2]
    metric 10 sids: 8001 ipv4;

    4444.4444.4444 -> 5555.5555.5555 [10.0.45.4 -> 10.0.45.5]
    metric 50 sids: 8000 ipv4;

    4444.4444.4444 -> 1111.1111.1111 [10.0.14.4 -> 10.0.14.1]
    metric 10 sids: 8001 ipv4;

    3333.3333.3333 -> 2222.2222.2222 [10.0.23.3 -> 10.0.23.2]
    metric 10 sids: 8000 ipv4;


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.3        | Command introduced    |
+-------------+-----------------------+


