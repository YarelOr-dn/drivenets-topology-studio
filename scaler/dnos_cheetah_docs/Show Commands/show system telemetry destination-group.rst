show system telemetry destination-group
---------------------------------------

**Minimum user role:** viewer

To display information on dial-out telemetry destination groups:

**Command syntax: show system telemetry destination-group** [destination-group-id]

**Command mode:** operational

**Parameter table**

+----------------------+--------------------------------------+---------+
| Parameter            | Description                          | Default |
+======================+======================================+=========+
| destination-group-id | Optionally filter the information to | \-      |
|                      | a specific destination group.        |         |
|                      |                                      |         |
+----------------------+--------------------------------------+---------+

The following information is displayed for each destination group in the table:

+----------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------------------+
| Field                      | Description                                                                                                   | Range                                              |
+============================+===============================================================================================================+====================================================+
| Server Address             | IP and port of the destination server                                                                         | A.B.C.D:Port                                       |
|                            |                                                                                                               | xx:xx::xx:xx:Port                                  |
+----------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------------------+
| VRF                        | The VRF used for network traffic to the server                                                                | 1..255 characters                                  |
+----------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------------------+
| Source Interface           | The source interface which sends telemetry data to its destination                                            | lo1                                                |
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
| Encoding                   | Communication encoding for data exchange                                                                      | json                                               |
+----------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------------------+
| Retry Timer                | The waiting period ( in seconds ) before attempting to restream after unsuccessful attempts                   | 10..1200                                           |
+----------------------------+---------------------------------------------------------------------------------------------------------------+----------------------------------------------------+

**Example**
::

    dnRouter# show system telemetry destination-group

    Destination Group: Development

    Servers:

    | Server Address       | VRF     | Source Interface | Compression | Protocol | Encoding | Retry Timer |
    +----------------------+---------+------------------+-------------+----------+----------+-------------+
    | 10.0.0.1:62000       | default | bundle-1.1       | none        | grpc     | json     | 30 seconds  |
    | a1b:2d:3f4c:1:::7503 | mgmt0   | mgmt0            | gzip        | grpc     | json     | 30 seconds  |

    Used by subscriptions:
        dev-subscription


    Destination Group: Production

    Servers:

    | Server Address       | VRF     | Source Interface | Compression | Protocol | Encoding | Retry Timer |
    +----------------------+---------+------------------+-------------+----------+----------+-------------+
    | 127.0.0.1:73000      | default |                  | none        | grpc     | json     | 30 seconds  |
    | a1b:2c:2f4c:1:::7503 | mgmt0   |                  | gzip        | grpc     | json     | 30 seconds  |

    Used by subscriptions:
        prod-subscription




.. **Help line:** show system telemetry destination-group

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 19.10   | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
