show system utilization limits
------------------------------

**Minimum user role:** viewer

The show system utilization command displays the configured hardware resource limits per NCE type and SW process for memory thresholds.

**Command syntax: show system utilization limits** [node-type] [node-id]

**Command mode:** operational

**Note**

- Internal abnormal memory utilization detection algorithm is enabled by default on all software processes. The algorithm may be disabled on specific processes if required.

- In addition to the detection algorithm, memory related thresholds can be set per node type and process name.

- Non-memory thresholds (cpu, file-descriptor, disk) are set on a node type basis.

- An asterisk (*) near the limit in the table marks default configuration value

- '--' in the User defined memory threshold configuration table marks threshold not set by the user.

**Parameter table**

The following are the parameters that you can use to filter the output results:

+----------------+------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| Parameter      | Description                                                                                                                                          | Range              |
+================+======================================================================================================================================================+====================+
| node-type      | The type of the node used to filter the output to a specific cluster element type. If no name is provided, all cluster node types will be displayed. | NCP/NCF/NCC        |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| node-id        | The node id of the node used to filter the output to a specific cluster element. If no name is provided, all cluster node ids will be displayed.     | 0..255             |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+

**Example**
::

    dnRouter# show system utilization limits ncc 1

    System utilization warning limits:
        | Node Type                                  |  CPU [%] |  Memory [%] |  Storage disk continous |  Storage disk |
        |                                            |          |             |  write bandwidth [MB/s] |  space  [%]   | 
        +--------------------------------------------+----------+-------------+-------------------------+---------------+
        | ncc                                        |  90*     |  90*        |  90*                    |  80*          |

    Default process utilization limits:
        | Node                                       |  CPU Limit [%]       |  Storage disk write BW Limit [MB/s] |  FD Limit [FD no]     |  Memory Limit [MB]      |
        |                                            |  Warning/Critical    |  Warning/Critical                   |  Warning/Critical     |  Warning/Critical       |
        +--------------------------------------------+----------------------+-------------------------------------+-----------------------+-------------------------+
        | ncc1                                       |  60/85               |  448/504                            |  48000/57600          |  44376/55000            |

    NCC: Process memory utilization configuration:
        | Process name                           |  Memory Limit [MB]        |  Abnormal memory utilization |
        |                                        |  Warn/Critical            |  detection algorithm state   |
        +----------------------------------------+---------------------------+------------------------------+
        | bgpd                                   |  20000/30000              |  Disabled                    |
        | bgpd_authentication_logger             |  25000/30000              |  Enabled                     |


    * - default thresholds

    dnRouter# show system utilization limits

    System utilization warning limits:
        | Node Type                                  |  CPU [%] |  Memory [%] |  Storage disk continous |  Storage disk |
        |                                            |          |             |  write bandwidth [MB/s] |  space  [%]   |
        +--------------------------------------------+----------+-------------+-------------------------+---------------+
        | ncc                                        |  75      |  65         |  90*                    |  80*          |
        | ncp                                        |  70      |  65         |  90*                    |  80*          |
        | ncf                                        |  80      |  65         |  90*                    |  80*          |

    Default process utilization limits:
        | Node                                       |  CPU Limit [%]       |  Storage disk write BW Limit [MB/s] |  FD Limit [FD no]     |  Memory Limit [MB]      |
        |                                            |  Warning/Critical    |  Warning/Critical                   |  Warning/Critical     |  Warning/Critical       |
        +--------------------------------------------+----------------------+-------------------------------------+-----------------------+-------------------------+
        | ncc0                                       |  60/85               |  448/504                            |  48000/57600          |  44376/50716            |
        | ncc1                                       |  60/85               |  448/504                            |  48000/57600          |  44376/50716            |
        | ncp0                                       |  60/85               |  448/504                            |  48000/57600          |  44376/50716            |
        | ncp1                                       |  60/85               |  448/504                            |  48000/57600          |  44376/50716            |
        | ncp2                                       |  60/85               |  448/504                            |  48000/57600          |  44376/50716            |
        | ncf0                                       |  60/85               |  448/504                            |  48000/57600          |  44376/50716            |
        | ncf1                                       |  60/85               |  448/504                            |  48000/57600          |  44376/50716            |

    NCC: Process memory utilization configuration:
        | Process name                           |  Memory Limit [MB]       |  Abnormal memory utilization |
        |                                        |  Warning/Critical        |  detection algorithm state   |
        +----------------------------------------+--------------------------+------------------------------+
        | bgpd                                   |  --/30000                |  Disabeld                    |
        | bgpd_authentication_logger             |  25000/30000             |  Disabled                    |

    NCP: Process memory utilization configuration:
        No defined thresholds

    NCF: Process memory utilization configuration:
        | Process name                           |  Memory Limit [MB]       |  Abnormal memory utilization |
        |                                        |  Warning/Critical        |  detection algorithm state   |
        +----------------------------------------+--------------------------+------------------------------+
        | interface_handler                      |  --/6000                 |  Disabled                    |

    -- - threshold not set by user
    * - default thresholds

.. **Help line:** Display configured hardware resource utilization limits


**Command History**

+---------+------------------------------------------------------------+
| Release | Modification                                               |
+=========+============================================================+
| 18.2    | Command introduced                                         |
+---------+------------------------------------------------------------+
