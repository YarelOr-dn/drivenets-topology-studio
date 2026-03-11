show system clock gnss
----------------------

**Minimum user role:** viewer

To display synchronization GNSS configuration and state parameters:

**Command syntax: show system clock gnss** [node-name] [node-id]

**Command mode:** operational

**Parameter table**

+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| Parameter | Description                                                                                                                                | Range              |
+===========+============================================================================================================================================+====================+
| node-name | The name of the node used to filter the output to a specific cluster element. If no name is provided, all cluster nodes will be displayed. | NCP                |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| node-id   | The ID of the node used to filter the output to a specific cluster element.                                                                | NCP: 0..191        |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+--------------------+

**Example**
::

    dnRouter# show system clock gnss ncp 0

    Synchronization GNSS parameters:
        Mode:                       enabled
        GNSS status:                fixed
        Cable legth compensation:   100 nanoseconds
        Constellation:              gps, galileo
        Min. satellites:            3
        Max. satellites:            32
        Min. CNo:                   22 dbHz
        Position
            Lattitude:
            Longtitude:
            Altitude:

    GNSS satellites information:
        | idx | type     | prn   | cno   | azimuth   | elevation   |
        |-----+----------+-------+-------+-----------+-------------|
        | 1   | galileo  |       |       |           |             |
        | 2   | galileo  |       |       |           |             |
        | 3   | galileo  |       |       |           |             |
        | 4   | galileo  |       |       |           |             |
        | 5   | gps      |       |       |           |             |
        | 6   | gps      |       |       |           |             |

**Example**
::

    dnRouter# show system clock gnss

    ncp 0 (dn-ncp-0)

    Synchronization GNSS parameters:
        Mode:                       enabled
        GNSS status:                fixed
        Cable legth compensation:   100 nanoseconds
        Constellations:             gps, glonass, imes
        Min. satellites:            3
        Max. satellites:            32
        Min. CNo:                   22 dbHz
        Position
            Lattitude:
            Longtitude:
            Altitude:

    GNSS satellites information:
        | idx | type     | prn   | cno   | azimuth   | elevation   |
        |-----+----------+-------+-------+-----------+-------------|
        | 1   | gps      |       |       |           |             |
        | 2   | gps      |       |       |           |             |
        | 3   | glonass  |       |       |           |             |
        | 4   | glonass  |       |       |           |             |
        | 5   | glonass  |       |       |           |             |
        | 6   | imes     |       |       |           |             |
        | 7   | imes     |       |       |           |             |
        | 8   | imes     |       |       |           |             |

    ncp 1 (dn-ncp-1)

    Synchronization GNSS parameters:
        Mode:                       enabled
        GNSS status:                fixed
        Cable legth compensation:    -200 nanoseconds
        Constellations:             galileo
        Min. satellites:            4
        Max. satellites:            32
        Min. CNo:                   23 dbHz
        Position
            Lattitude:
            Longtitude:
            Altitude:

    GNSS satellites information:
        | idx | type     | prn   | cno   | azimuth   | elevation   |
        |-----+----------+-------+-------+-----------+-------------|
        | 1   | galileo  |       |       |           |             |
        | 2   | galileo  |       |       |           |             |
        | 3   | galileo  |       |       |           |             |
        | 4   | galileo  |       |       |           |             |

.. **Help line:** show system clock gnss [ncp] [0..191]

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 18.3    | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
