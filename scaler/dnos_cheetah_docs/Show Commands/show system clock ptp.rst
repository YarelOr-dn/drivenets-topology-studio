show system clock ptp
---------------------

**Minimum user role:** viewer

To display PTP (1588v2) timing attributes of the system:

**Command syntax: show system clock ptp** [node-name] [node-id]

**Command mode:** operational

**Parameter table**

+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| Parameter | Description                                                                                                                                | Range              |
+===========+============================================================================================================================================+====================+
| node-name | The name of the node used to filter the output to a specific cluster element. If no name is provided, all cluster nodes will be displayed. | NCP                |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| node-id   | The ID of the node used to filter the output to a specific cluster element.                                                                | NCP: 0..191        |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+--------------------+

**Note**
- When the PTP feature is disabled or node is not in an operational state, data will not be available.

.. - By default (if node name not specified), output will show all the nodes in DNOS cluster.
.. - In Standalone mode, control ports are named ctrl-ncc-0/[0-1] and not ctrl-ncp-X/Y.

**Example**
::

    dnRouter# show system clock ptp ncp 0

    PTP Clock Default dataset parameters:
        Mode:                            enabled
        Type:                            T-BC
        Profile:                         G.8275.1
        Identity:                        04:05:AA:FE:EF:08:9A:00
        Num-of-ports:                    2
        Domain:                          24
        Class:                           0xFF
        Local priority:                  128
        Priority-2:                      128
        Max steps removed:               20
        Holdover-in-spec time:           120 minutes
        Num-of-steps:                    1
        Accuracy:                        0xFE
        Offset Scaled Log Variance:      0xFFFF

    PTP Clock Current dataset parameters:
        Steps removed:                   3
        Offset from master:              3 nsec
        Mean path delay:                 1 nsec

    ToD source:                          GNSS
    GNSS mode:                           enabled
    1pps SMB port mode:                  output
    ToD port mode:                       input


**Example**
::

    dnRouter# show system clock ptp

    ncp 0 (dn-ncp-0)

    PTP Clock Default dataset parameters:
        Mode:                            enabled
        Type:                            T-BC
        Profile:                         G.8275.1
        Identity:                        04:05:AA:FE:EF:08:9A:00
        Num-of-ports:                    2
        Domain:                          24
        Class:                           0xFF
        Local priority:                  128
        Priority-2:                      128
        Max steps removed:               20
        Holdover-in-spec time:           120 minutes
        Num-of-steps:                    1
        Accuracy:                        0xFE
        Offset Scaled Log Variance:      0xFFFF

    PTP Clock Current dataset parameters:
        Steps removed:                   3
        Offset from master:              3 nsec
        Mean path delay:                 1 nsec

    ToD source:                          packet
    GNSS mode:                           disabled
    1pps SMB port mode:                  output
    ToD port mode:                       output

    ncp 1 (dn-ncp-1)

    PTP Clock Default dataset parameters:
        Mode:                            enabled
        Type:                            T-TSC
        Profile:                         G.8275.1
        Identity:                        14:15:1A:1E:1F:18:1A:10
        Num-of-ports:                    1
        Domain:                          24
        Class:                           0xFF
        Local priority:                  128
        Priority-2:                      128
        Max steps removed:               20
        Holdover-in-spec time:           120 minutes
        Num-of-steps:                    1
        Accuracy:                        0xFE
        Offset Scaled Log Variance:      0xFFFF

    PTP Clock Current dataset parameters:
        Steps removed:                   4
        Offset from master:              5 nsec
        Mean path delay:                 2 nsec

    ToD source:                          tod-port
    GNSS mode:                           enabled
    1pps SMB port mode:                  output
    ToD port mode:                       input

**Example**
::

    dnRouter# show system clock ptp

        Requested data is unavailable.

.. **Help line:** Display the PTP (1588v2) timing attributes of the system

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 18.3    | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
| 18.3    | Added GNSS and ToD parameters                                       |
+---------+---------------------------------------------------------------------+
