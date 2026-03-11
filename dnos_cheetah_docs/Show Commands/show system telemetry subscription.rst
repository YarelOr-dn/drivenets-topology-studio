show system telemetry subscription
----------------------------------

**Minimum user role:** viewer

The show system telemetry subscription command displays concentric information of all subscriptions if a subscription-id is not specified. If a subscription-id is provided, then the full configuration for the requested interface is displayed with its operational information.

**Command syntax: show system telemetry subscription** [subscription-id]

**Command mode:** operational

**Parameter table**

+----------------------+-----------------------------------------+---------+
| Parameter            | Description                             | Default |
+======================+=========================================+=========+
| subscription-id      | Optionally provide detailed information | \-      |
|                      | On Given subscription                   |         |
|                      |                                         |         |
+----------------------+-----------------------------------------+---------+

The following concentric information is displayed for each subscription group:

The concentric information of all sensor groups configured for the subscription group:

+----------------------------+----------------------------------------------------------------------+----------+
| Field                      | Description                                                          | Range    |
+============================+======================================================================+==========+
| Sample interval            | The interval in seconds between each sample of data in a senor group | 5..86400 |
+----------------------------+----------------------------------------------------------------------+----------+
| Path Resolved              | The number of resolved paths in a sensor group                       | 0..16    |
+----------------------------+----------------------------------------------------------------------+----------+
| Path Unresolved            | The number of non-resolved paths in a sensor group                   | 0..16    |
+----------------------------+----------------------------------------------------------------------+----------+

The concentric information of all destination groups configured for the subscription group:

+----------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------------------+
| Field                      | Description                                                                                                   | Range                                              |
+============================+===============================================================================================================+====================================================+
| Server Address             | IP and port of the destination server                                                                         | A.B.C.D:Port                                       |
|                            |                                                                                                               | xx:xx::xx:xx:Port                                  |
+----------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------------------+
| VRF                        | The VRF used for network traffic to the server                                                                | 1..255 characters                                  |
+----------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------------------+
| Source Interface           | The source interface which sends telemetry data to its destination                                            | lo0                                                |
|                            |                                                                                                               | ge<interface speed>-<A>/<B>/<C>                    |
|                            |                                                                                                               | ge<interface speed>-<A>/<B>/<C>.<sub-interface id> |
|                            |                                                                                                               | bundle-<bundle id>                                 |
|                            |                                                                                                               | bundle-<bundle id>.<sub-interface id>              |
+----------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------------------+
| Compression                | If compression is used on the messages before being transferred                                               | none                                               |
|                            |                                                                                                               | gzip                                               |
+----------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------------------+
| Protocol                   | Communication protocol for data exchange                                                                      | grpc                                               |
+----------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------------------+
| Encoding                   | Communication Encoding for data exchange                                                                      | json                                               |
+----------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------------------+
| Retry Timer                | The waiting period ( in seconds ) before attempting to restream after unsuccessful attempts                   | 10..1200                                           |
+----------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------------------+

The following information is displayed if the user requests the subscription by subscription-id:

For each sensor group ID configured with the subscription-id a list is provided of all the YANG paths in the sensor group with their resolved status.

For each destination group ID configured with the subscription-id, the following is provided:
1. Concentric information on destinations.
2. Counters and operational states for each destination.

For each destination the following detailed information is provided:

+----------------------------+---------------------------------------------------------------------------------------------------------------+---------------------+
| Field                      | Description                                                                                                   | Range               |
+============================+===============================================================================================================+=====================+
| Server Address             | IP and port of the destination server                                                                         | A.B.C.D:Port        |
|                            |                                                                                                               | xx:xx::xx:xx:Port   |
+----------------------------+---------------------------------------------------------------------------------------------------------------+---------------------+
| State                      | The state of the connection between the device and destination                                                | initialized         |
|                            |                                                                                                               | connecting          |
|                            |                                                                                                               | active              |
|                            |                                                                                                               | paused              |
|                            |                                                                                                               | idle                |
|                            |                                                                                                               | reconnecting        |
|                            |                                                                                                               | error               |
+----------------------------+---------------------------------------------------------------------------------------------------------------+---------------------+
| Source Port                | Source port of the current active session to the destination                                                  | Port                |
+----------------------------+---------------------------------------------------------------------------------------------------------------+---------------------+
| Creation Time              | Date and time that the first session to the destination was created                                           | yyyy-mm-dd hh:mm:ss |
+----------------------------+---------------------------------------------------------------------------------------------------------------+---------------------+
| Uptime                     | The elapsed time since the last successful session was established                                            | dd days, hh:mm:ss   |
+----------------------------+---------------------------------------------------------------------------------------------------------------+---------------------+
| Restart counter            | Restart the count which counts the number of times a new connection or session has been established           | 64-bit counter      |
+----------------------------+---------------------------------------------------------------------------------------------------------------+---------------------+
| Exported Leaves            | The number of exported YANG leaves per telemetry dial-out session                                             | 64-bit counter      |
+----------------------------+---------------------------------------------------------------------------------------------------------------+---------------------+
| Export Rate                | Exported rate [bps] per telemetry dial-out session                                                            | 64-bit gauge        |
+----------------------------+---------------------------------------------------------------------------------------------------------------+---------------------+
| Export Leaf Rate           | Exported rate [leaves per second] per telemetry dial-out session                                              | 64-bit gauge        |
+----------------------------+---------------------------------------------------------------------------------------------------------------+---------------------+


**Example**
::

    dnRouter# show system telemetry subscription

    Subscription Name: dev-subscription
    -----------------------------------
    Admin State: Enabled

    Sensor Groups:

    | Sensor Group Id  | Sample interval | Path Resolved | Path Unresolved |
    +------------------+-----------------+---------------+-----------------+
    | Interfaces data  | 5 seconds       | 1             | 0               |
    | data with error  | 5 seconds       | 1             | 1               |

    Destination Groups:

    Destination Group: Development

    Servers:

    | Server Address       | VRF     | Source Interface | Compression | Protocol | Encoding | Retry Timer |
    +----------------------+---------+------------------+-------------+----------+----------+-------------+
    | 10.0.0.1:62000       | default | bundle-1.1       | none        | grpc     | json     | 30 seconds  |
    | a1b:2d:3f4c:1:::7503 | mgmt0   | mgmt0            | gzip        | grpc     | json     | 30 seconds  |

    Destination Group: Production

    Servers:

    | Server Address       | VRF     | Source Interface | Compression | Protocol | Encoding | Retry Timer |
    +----------------------+---------+------------------+-------------+----------+----------+-------------+
    | 127.0.0.1:73000      | default |                  | none        | grpc     | json     | 30 seconds  |
    | a1b:2c:2f4c:1:::7503 | mgmt0   |                  | gzip        | grpc     | json     | 30 seconds  |

    Subscription Name: partial-sub
    ------------------------------
    Admin State: Enabled

    Sensor Groups:
        No Sensor Groups configured.

    Destination Groups:
        No Destination Groups configured.


    dnRouter# show system telemetry subscription dev-subscription

    Subscription Name: dev-subscription
    -----------------------------------
    Admin State: Enabled

    Sensor Group Id: Interfaces data
    --------------------------------

    Sensor Path:        /drivenets-top/interfaces/interface[name='bundle*']/oper-items/counters/forwarding-counters/rx-octets
    Sensor Path State:  Resolved

    Sensor Group Id: data with error
    --------------------------------

    Sensor Path:        /drivenets-top/interfaces/interface[name='bundle*']/oper-items/counters/forwarding-counters/rx-octets
    Sensor Path State:  Resolved
    Sensor Path:        /path-with-error/interfaces
    Sensor Path State:  Not Resolved
    Sensor Path Error:  Path could not be resolved

    Destination Groups:

    Destination Group: Development

    Servers:

    | Server Address       | VRF     | Source Interface | Compression | Protocol | Encoding | Retry Timer |
    +----------------------+---------+------------------+-------------+----------+----------+-------------+
    | 10.0.0.1:62000       | default | bundle-1.1       | none        | grpc     | json     | 30 seconds  |
    | a1b:2d:3f4c:1:::7503 | mgmt0   | mgmt0            | gzip        | grpc     | json     | 30 seconds  |

    Destinations:

    | Server Address         | State     | Source Port | Creation Time       | Uptime            | Restart counter | Exported Leaves   | Export Rate  | Export Leaf Rate  |
    +------------------------+-------------------------+---------------------+-------------------+-----------------+-------------------+--------------+-------------------+
    | 10.0.0.1:62000         | active    | 7831        | 2023-07-10 11:10:12 | 10 Days,00:01:30  | 0               | 100               | 0.6 Mbps     | 16 lps            |
    | a1b:2d:3f4c:1:::7503   | error     |             | 2023-07-10 11:10:13 | 0 Days, 00:00:00  | 5               | 50                | 0.0 Mbps     | 0  lps            |

    Destination Group: Production

    Servers:

    | Server Address       | VRF     | Source Interface | Compression | Protocol | Encoding | Retry Timer |
    +----------------------+---------+------------------+-------------+----------+----------+-------------+
    | 127.0.0.1:73000      | default |                  | none        | grpc     | json     | 30 seconds  |
    | a1b:2c:2f4c:1:::7503 | mgmt0   |                  | gzip        | grpc     | json     | 30 seconds  |

    Destinations:

    | Server Address         | State     | Source Port | Creation Time       | Uptime           | Restart counter | Exported Leaves   | Export Rate  | Export Leaf Rate  |
    +------------------------+-----------+-------------+---------------------+------------------+-----------------+-------------------+--------------+-------------------+
    | 127.0.0.1:73000        | active    | 4981        | 2023-07-10 11:10:12 | 10 Days,00:01:30 | 0               | 100               | 0.6 Mbps     |  16 lps           |
    | a1b:2c:2f4c:1:::7503   | error     |             | 2023-07-10 11:10:13 | 0 Days, 00:00:00 | 5               | 50                | 0.0 Mbps     |  0  lps           |

.. **Help line:** show system telemetry

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 19.10   | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
