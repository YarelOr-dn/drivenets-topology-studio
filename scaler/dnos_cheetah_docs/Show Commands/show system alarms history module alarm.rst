show system alarms history module alarm
---------------------------------------

**Minimum user role:** viewer

To display the system alarms history, the recent cleared alarms in the system filtered by module name and alarm name:



**Command syntax: show system alarms history module [module-name] alarm [alarm-name]** severity[severity-name] \| state[operator-state] \| all-history-records \| severity[severity-name] state[operator-state] \| severity[severity-name] all-history-records \| state[operator-state] all-history-records \| severity[severity-name] state[operator-state] all-history-records

**Command mode:** operational



**Parameter table**

The following information is displayed on each alarm:

+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Field              | Description                                                                                                                    | Range                    |
+====================+================================================================================================================================+==========================+
| Name               | The alarm name                                                                                                                 | \-                       |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Resource           | The resource the alarm is raised on                                                                                            | \-                       |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Alarm Raise Time   | The time when the alarm was raised                                                                                             | yyyy-mm-ddThh:mm:ss      |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Alarm Cleared Time | The time when the alarm was cleared                                                                                            | yyyy-mm-ddThh:mm:ss      |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Alarm Message      | The alarm message                                                                                                              | \-                       |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Severity           | The alarm severity                                                                                                             | warning, minor, major,   |
|                    |                                                                                                                                | critical                 |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Module Name        | The name of the alarm module                                                                                                   | dnos-alarms              |
|                    |                                                                                                                                | communications-alarm     |
|                    |                                                                                                                                | quality-of-service-alarm |
|                    |                                                                                                                                | processing-error-alarm   |
|                    |                                                                                                                                | equipment-alarm          |
|                    |                                                                                                                                | environmental-alarm      |
|                    |                                                                                                                                | bfd                      |
|                    |                                                                                                                                | bgp                      |
|                    |                                                                                                                                | efm-oam                  |
|                    |                                                                                                                                | management               |
|                    |                                                                                                                                | isis                     |
|                    |                                                                                                                                | pcep                     |
|                    |                                                                                                                                | ldp                      |
|                    |                                                                                                                                | l2vpn                    |
|                    |                                                                                                                                | aaa                      |
|                    |                                                                                                                                | rib                      |
|                    |                                                                                                                                | rsvp                     |
|                    |                                                                                                                                | segment-routing          |
|                    |                                                                                                                                | static-route             |
|                    |                                                                                                                                | fib-manager              |
|                    |                                                                                                                                | interfaces               |
|                    |                                                                                                                                | lacp                     |
|                    |                                                                                                                                | system                   |
|                    |                                                                                                                                | diagnostics              |
|                    |                                                                                                                                | platform                 |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Operator State     | The state set by the operator                                                                                                  | ack, closed              |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+

**Example**
::

    dnRouter# show system alarms history module isis alarm isis_neighbor_adjacency_down

    System Totals Critical: 1  Major: 2  Minor: 0 Warning: 0

    | Name                         | Module Name | Resource        | Alarm Raised Time   | Alarm Cleared Time  | Severity | Alarm Message                        | Operator State |
    |------------------------------+-------------+-----------------+---------------------+---------------------+----------+--------------------------------------+----------------+
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-13T17:59:44 | 2022-10-14T17:59:44 | Major    | ISIS adjacency down on interface     | Ack,           |
    |                              |             |                 |                     |                     |          | ge100-0/0/5.600                      | Closed         |
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/4.200 | 2022-10-12T12:52:40 | 2022-10-13T12:52:40 | Major    | ISIS adjacency down on interface     |                |
    |                              |             |                 |                     |                     |          | ge100-0/0/4.200                      |                |


    dnRouter# show system alarms history module isis alarm isis_neighbor_adjacency_down severity major

    System Totals Critical: 1  Major: 2  Minor: 0 Warning: 0

    | Name                         | Module Name | Resource        | Alarm Raised Time   | Alarm Cleared Time  | Severity | Alarm Message                        | Operator State |
    |------------------------------+-------------+-----------------+---------------------+---------------------+----------+--------------------------------------+----------------+
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-13T17:59:44 | 2022-10-14T17:59:44 | Major    | ISIS adjacency down on interface     | Ack,           |
    |                              |             |                 |                     |                     |          | ge100-0/0/5.600                      | Closed         |
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/4.200 | 2022-10-12T12:52:40 | 2022-10-13T12:52:40 | Major    | ISIS adjacency down on interface     |                |
    |                              |             |                 |                     |                     |          | ge100-0/0/4.200                      |                |


    dnRouter# show system alarms history module isis alarm isis_neighbor_adjacency_down state ack

    System Totals Critical: 1  Major: 2  Minor: 0 Warning: 0

    | Name                         | Module Name | Resource        | Alarm Raised Time   | Alarm Cleared Time  | Severity | Alarm Message                        | Operator State |
    |------------------------------+-------------+-----------------+---------------------+---------------------+----------+--------------------------------------+----------------+
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-13T17:59:44 | 2022-10-14T17:59:44 | Major    | ISIS adjacency down on interface     | Ack,           |
    |                              |             |                 |                     |                     |          | ge100-0/0/5.600                      | Closed         |


    dnRouter# show system alarms history module isis alarm isis_neighbor_adjacency_down state closed

    System Totals Critical: 1  Major: 2  Minor: 0 Warning: 0

    | Name                         | Module Name | Resource        | Alarm Raised Time   | Alarm Cleared Time  | Severity | Alarm Message                        | Operator State |
    |------------------------------+-------------+-----------------+---------------------+---------------------+----------+--------------------------------------+----------------+
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-13T17:59:44 | 2022-10-13T17:59:44 | Major    | ISIS adjacency down on interface     | Ack,           |
    |                              |             |                 |                     |                     |          | ge100-0/0/5.600                      | Closed         |


    dnRouter# show system alarms history module isis alarm isis_neighbor_adjacency_down state closed severity major

    System Totals Critical: 1  Major: 2  Minor: 0 Warning: 0

    | Name                         | Module Name | Resource        | Alarm Raised Time   | Alarm Cleared Time  | Severity | Alarm Message                        | Operator State |
    |------------------------------+-------------+-----------------+---------------------+---------------------+----------+--------------------------------------+----------------+
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-13T17:59:44 | 2022-10-13T17:59:44 | Major    | ISIS adjacency down on interface     | Ack,           |
    |                              |             |                 |                     |                     |          | ge100-0/0/5.600                      | Closed         |


    dnRouter# show system alarms history module isis alarm isis_neighbor_adjacency_down all-history-records

    System Totals Critical: 1  Major: 2  Minor: 0 Warning: 0

    | Name                         | Module Name | Resource        | Alarm Raised Time   | Alarm Cleared Time  | Severity | Alarm Message                        | Operator State |
    |------------------------------+-------------+-----------------+---------------------+---------------------+----------+--------------------------------------+----------------+
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-13T17:59:44 | 2022-10-14T17:59:44 | Major    | ISIS adjacency down on interface     | Ack,           |
    |                              |             |                 |                     |                     |          | ge100-0/0/5.600                      | Closed         |
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/5.600 | 2022-10-12T12:52:39 | 2022-10-13T12:52:38 | Major    | ISIS adjacency down on interface     |                |
    |                              |             |                 |                     |                     |          | ge100-0/0/5.600                      |                |
    | ISIS_NEIGHBOR_ADJACENCY_DOWN | isis        | ge100-0/0/4.200 | 2022-10-12T12:52:40 | 2022-10-13T12:52:40 | Major    | ISIS adjacency down on interface     |                |
    |                              |             |                 |                     |                     |          | ge100-0/0/4.200                      |                |

.. **Help line:** show system alarms history.

**Command History**

+---------+--------------------------------------------------+
| Release | Modification                                     |
+=========+==================================================+
| 18.0    | Command introduced                               |
+---------+--------------------------------------------------+
