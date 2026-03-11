show system telemetry destination
----------------------------------

**Minimum user role:** viewer

The show system telemetry destination command displays concentric information of all unique telemetry destinations configured within the system. A unique destination is identified by a specific combination of subscription, destination group, IP address, and port number. When executed without any arguments, this command displays all unique destinations. However, if a user specifies a subscription ID or a destination group, the command filters the output to show only the unique destinations associated with the provided subscription or destination group information.

**Command syntax: show system telemetry destination** {subscription [subscription-id] destination-group [destination-group-id]}

**Command mode:** operational

**Parameter table**

+----------------------+------------------------------------------+---------+
| Parameter            | Description                              | Default |
+======================+==========================================+=========+
| subscription-id      | Optionally provide a subscription-id     | \-      |
|                      | to filter information for a specific     |         |
|                      | subscription                             |         |
+----------------------+------------------------------------------+---------+
| destination-group-id | Optionally provide a destination-group-id| \-      |
|                      | to filter information for a specific     |         |
|                      | destination-group                        |         |
+----------------------+------------------------------------------+---------+

For each destination the detailed information provided:

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
| Source Port                | The source port of the current active session to the destination                                              | Port                |
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
| Subscription               | The identifier of the subscription to which the destination-group is assigned                                 | String              |
+----------------------------+---------------------------------------------------------------------------------------------------------------+---------------------+
| Destination Group          | The identifier of the destination group to which the destination is assigned                                  | String              |
+----------------------------+---------------------------------------------------------------------------------------------------------------+---------------------+

**Example**
::

    dnRouter# show system telemetry destination

    | Server Address       | State     | Source Port | Creation Time       | Uptime            | Restart counter | Exported Leaves   | Export Rate  | Export Leaf Rate  | Subscription   | Destination Group   |
    +----------------------+-------------------------+---------------------+-------------------+-----------------+-------------------+--------------+-------------------+----------------+---------------------|
    | 10.0.0.1:62000       | active    | 7831        | 2023-07-10 11:10:12 | 10 Days,00:01:30  | 0               | 100               | 0.6 Mbps     | 16 lps            | counters       | prod                |
    | 10.0.0.1:62000       | active    | 7836        | 2023-07-10 11:10:14 | 10 Days,00:01:28  | 0               | 78                | 0.0 Mbps     | 0  lps            | system         | prod                |
    | a1b:2d:3f4c:1:::7503 | error     |             | 2023-07-10 11:10:13 |                   | 5               | 50                | 0.0 Mbps     | 0  lps            | counters       | prod                |
    | a1b:2d:3f4c:1:::7503 | error     |             | 2023-07-10 11:10:15 |                   | 5               | 39                | 0.0 Mbps     | 0  lps            | system         | prod                |
    | 10.0.0.2:7500        | paused    |             | 2023-07-10 09:50:21 |                   | 14              | 50                | 0.0 Mbps     | 0  lps            | misc           | dev                 |
    | 10.0.0.3:7500        | paused    |             | 2023-07-10 09:50:21 |                   | 25              | 50                | 0.0 Mbps     | 0  lps            | misc           | dev                 |


    dnRouter# show system telemetry destination subscription counters

    | Server Address       | State     | Source Port | Creation Time       | Uptime            | Restart counter | Exported Leaves   | Export Rate  | Export Leaf Rate  | Subscription   | Destination Group   |
    +----------------------+-------------------------+---------------------+-------------------+-----------------+-------------------+--------------+-------------------+----------------+---------------------|
    | 10.0.0.1:62000       | active    | 7831        | 2023-07-10 11:10:12 | 10 Days,00:01:33  | 0               | 100               | 0.6 Mbps     | 16 lps            | counters       | prod                |
    | a1b:2d:3f4c:1:::7503 | error     |             | 2023-07-10 11:10:13 |                   | 5               | 50                | 0.0 Mbps     | 0  lps            | counters       | prod                |


    dnRouter# show system telemetry destination subscription all destination-group prod

    | Server Address         | State     | Source Port | Creation Time       | Uptime            | Restart counter | Exported Leaves   | Export Rate  | Export Leaf Rate  | Subscription   | Destination Group   |
    +------------------------+-------------------------+---------------------+-------------------+-----------------+-------------------+--------------+-------------------+----------------+---------------------|
    | 10.0.0.1:62000         | active    | 7831        | 2023-07-10 11:10:12 | 10 Days,00:01:35  | 0               | 100               | 0.0 Mbps     | 0  lps            | counters       | prod                |
    | 10.0.0.1:62000         | active    | 7836        | 2023-07-10 11:10:14 | 10 Days,00:01:33  | 0               | 78                | 0.0 Mbps     | 0  lps            | system         | prod                |
    | a1b:2d:3f4c:1:::7503   | error     |             | 2023-07-10 11:10:13 |                   | 5               | 50                | 0.0 Mbps     | 0  lps            | counters       | prod                |
    | a1b:2d:3f4c:1:::7503   | error     |             | 2023-07-10 11:10:15 |                   | 5               | 39                | 0.0 Mbps     | 0  lps            | system         | prod                |


.. **Help line:** show system telemetry destination

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 19.10   | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
